"""
TONARI for M&A - サジェスト生成サービス
水野メソッドに基づく質問・リフレーミング提案を生成
"""
import logging
import re
from datetime import datetime
from typing import Optional
from uuid import uuid4

from anthropic import AsyncAnthropic

from ..core.config import settings
from ..models.mna_schemas import (
    ExtractionField,
    Hypothesis,
    InfoLayer,
    ReframingSuggestion,
    Suggestion,
    SuggestionCreate,
    SuggestionType,
    Utterance,
)

logger = logging.getLogger(__name__)


# ネガティブワードパターン（リフレーミング対象）
NEGATIVE_PATTERNS: dict[str, dict] = {
    "赤字": {
        "reframe": "投資フェーズ、成長への先行投資",
        "question": "この赤字は何に投資した結果でしょうか？",
    },
    "減収": {
        "reframe": "選択と集中、収益性改善への取り組み",
        "question": "減収の背景にはどのような戦略的判断がありましたか？",
    },
    "借入": {
        "reframe": "レバレッジ活用、成長資金の確保",
        "question": "その借入はどのような投資に充てられましたか？",
    },
    "高齢": {
        "reframe": "豊富な経験、業界への深い知見",
        "question": "長年の経験から得られた独自のノウハウはありますか？",
    },
    "離職": {
        "reframe": "組織の新陳代謝、適材適所の実現",
        "question": "離職後の補充や組織強化はどのように進めていますか？",
    },
    "競合": {
        "reframe": "市場の成長性、需要の証明",
        "question": "競合と比較した際の御社の強みは何でしょうか？",
    },
    "依存": {
        "reframe": "強固な関係性、信頼の証",
        "question": "その取引先との関係はどのように構築されましたか？",
    },
    "古い": {
        "reframe": "実績のある、安定した",
        "question": "長年使い続けている理由は何でしょうか？",
    },
    "小さい": {
        "reframe": "機動力がある、意思決定が早い",
        "question": "小規模だからこそできることは何ですか？",
    },
    "ない": {
        "reframe": "これから構築可能、柔軟性がある",
        "question": "今後どのように整備していく予定ですか？",
    },
}


class MnASuggestionService:
    """サジェスト生成サービス.

    水野メソッドの4原則に基づいて質問・リフレーミングを提案:
    1. 多層的情報収集: 表層→構造→本質→出口の4レイヤー
    2. 仮説駆動: 仮説を立て、検証する質問
    3. リフレーミング: ネガティブ→ポジティブ転換
    4. 出口逆算: 買い手が知りたい情報を優先
    """

    def __init__(self) -> None:
        """サービスを初期化する."""
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    async def generate_suggestions(
        self,
        session_id: str,
        recent_utterances: list[Utterance],
        current_extractions: dict[str, ExtractionField],
        missing_fields: list[dict],
        hypotheses: list[Hypothesis],
    ) -> list[Suggestion]:
        """サジェストを生成する.

        Args:
            session_id: セッションID
            recent_utterances: 直近の発話リスト
            current_extractions: 現在の抽出情報
            missing_fields: 未取得フィールドリスト
            hypotheses: 現在の仮説リスト

        Returns:
            list[Suggestion]: サジェストリスト
        """
        prompt = self._build_suggestion_prompt(
            recent_utterances,
            current_extractions,
            missing_fields,
            hypotheses,
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
                tools=[
                    {
                        "name": "suggest_questions",
                        "description": "次に聞くべき質問を提案する",
                        "input_schema": self._build_suggestion_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": "suggest_questions"},
            )

            tool_use = next(
                (block for block in response.content if block.type == "tool_use"),
                None,
            )

            if tool_use is None:
                return []

            suggestions_data = tool_use.input.get("suggestions", [])
            suggestions = []

            for item in suggestions_data:
                try:
                    suggestion = Suggestion(
                        id=str(uuid4()),
                        session_id=session_id,
                        suggestion_type=SuggestionType.QUESTION,
                        content=item["question"],
                        reason=item["reason"],
                        layer=InfoLayer(item["layer"]),
                        priority=item["priority"],
                        target_field=item.get("target_field"),
                    )
                    suggestions.append(suggestion)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse suggestion: {e}")
                    continue

            # 優先度でソート
            suggestions.sort(key=lambda x: x.priority, reverse=True)
            return suggestions[:5]  # 上位5件

        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return []

    def detect_reframing_opportunity(
        self,
        utterance: Utterance,
    ) -> Optional[ReframingSuggestion]:
        """リフレーミング機会を検出する.

        Args:
            utterance: 発話

        Returns:
            ReframingSuggestion: リフレーミング提案（該当なしの場合None）
        """
        text = utterance.text

        for pattern, reframe_info in NEGATIVE_PATTERNS.items():
            if pattern in text:
                return ReframingSuggestion(
                    original_text=text,
                    negative_word=pattern,
                    positive_interpretation=reframe_info["reframe"],
                    follow_up_question=reframe_info["question"],
                    reframe_conditions=f"「{pattern}」を「{reframe_info['reframe']}」として捉え直す",
                )

        return None

    async def generate_reframing(
        self,
        utterance: Utterance,
        context: list[Utterance],
    ) -> Optional[ReframingSuggestion]:
        """AIによるリフレーミング提案を生成する.

        Args:
            utterance: 対象発話
            context: 文脈としての発話リスト

        Returns:
            ReframingSuggestion: リフレーミング提案
        """
        # まずパターンマッチで検出
        pattern_match = self.detect_reframing_opportunity(utterance)
        if pattern_match:
            return pattern_match

        # パターンにない場合はAIで分析
        prompt = f"""以下の発言にネガティブな内容が含まれているか分析し、
M&Aの観点からポジティブに解釈できる可能性を提示してください。

## 発言
{utterance.text}

## 直近の会話
{chr(10).join([f"[{'アドバイザー' if u.speaker == 'user' else '売り手'}] {u.text}" for u in context[-3:]])}

ネガティブな内容がない場合は、何も出力しないでください。
"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                tools=[
                    {
                        "name": "reframe",
                        "description": "リフレーミング提案を出力",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "has_negative": {
                                    "type": "boolean",
                                    "description": "ネガティブ要素があるか",
                                },
                                "negative_word": {
                                    "type": "string",
                                    "description": "ネガティブワード",
                                },
                                "positive_interpretation": {
                                    "type": "string",
                                    "description": "ポジティブな解釈",
                                },
                                "follow_up_question": {
                                    "type": "string",
                                    "description": "確認すべき質問",
                                },
                                "reframe_conditions": {
                                    "type": "string",
                                    "description": "ポジティブに転換できる条件",
                                },
                            },
                            "required": ["has_negative"],
                        },
                    }
                ],
                tool_choice={"type": "tool", "name": "reframe"},
            )

            tool_use = next(
                (block for block in response.content if block.type == "tool_use"),
                None,
            )

            if tool_use is None or not tool_use.input.get("has_negative"):
                return None

            data = tool_use.input
            return ReframingSuggestion(
                original_text=utterance.text,
                negative_word=data.get("negative_word", ""),
                positive_interpretation=data.get("positive_interpretation", ""),
                follow_up_question=data.get("follow_up_question", ""),
                reframe_conditions=data.get("reframe_conditions", ""),
            )

        except Exception as e:
            logger.error(f"Reframing generation failed: {e}")
            return None

    def _build_suggestion_prompt(
        self,
        recent_utterances: list[Utterance],
        current_extractions: dict[str, ExtractionField],
        missing_fields: list[dict],
        hypotheses: list[Hypothesis],
    ) -> str:
        """サジェストプロンプトを構築する."""
        # 抽出済み情報
        extracted_lines = []
        for key, field in current_extractions.items():
            if field.value:
                extracted_lines.append(f"- {key}: {field.value}")
        extracted_info = "\n".join(extracted_lines) if extracted_lines else "(なし)"

        # 未取得情報
        missing_lines = [f"- {f['label']} ({f['layer'].value})" for f in missing_fields[:10]]
        missing_info = "\n".join(missing_lines)

        # 直近の会話
        conversation_lines = []
        for u in recent_utterances[-5:]:
            speaker = "アドバイザー" if u.speaker == "user" else "売り手"
            conversation_lines.append(f"[{speaker}] {u.text}")
        conversation = "\n".join(conversation_lines)

        # 仮説
        hypothesis_lines = [
            f"- {h.content}（確信度: {h.confidence:.1f}）" for h in hypotheses[-3:]
        ]
        hypotheses_info = "\n".join(hypothesis_lines) if hypothesis_lines else "(なし)"

        return f"""あなたはM&Aヒアリングの専門家「水野メソッド」を実践するアシスタントです。

## 水野メソッドの4原則
1. **多層的情報収集**: 表層→構造→本質→出口の4レイヤーで情報を集める
2. **仮説駆動**: 仮説を立て、検証する質問をする
3. **リフレーミング**: ネガティブ情報をポジティブに転換
4. **出口逆算**: 買い手が知りたい情報を優先

## 現在の状況

### 抽出済み情報
{extracted_info}

### 未取得の重要情報
{missing_info}

### 直近の会話
{conversation}

### 現在の仮説
{hypotheses_info}

## 出力
以下を生成してください（2-4個の質問を推奨）：
1. 今聞くべき質問（文脈に自然に乗る形で）
2. その理由
3. 対応するレイヤー（surface/structure/essence/exit）
4. 優先度（0-1）
5. 対象フィールド（あれば）

重要：
- 会話の流れを壊さない自然な質問を心がける
- 買い手が最も知りたい情報を優先する
- 仮説を検証できる質問を意識する
"""

    def _build_suggestion_schema(self) -> dict:
        """サジェストスキーマを構築する."""
        return {
            "type": "object",
            "properties": {
                "suggestions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "提案する質問",
                            },
                            "reason": {
                                "type": "string",
                                "description": "この質問を提案する理由",
                            },
                            "layer": {
                                "type": "string",
                                "enum": ["surface", "structure", "essence", "exit"],
                                "description": "対応するレイヤー",
                            },
                            "priority": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "優先度",
                            },
                            "target_field": {
                                "type": "string",
                                "description": "対象フィールド名",
                            },
                        },
                        "required": ["question", "reason", "layer", "priority"],
                    },
                },
            },
            "required": ["suggestions"],
        }

    def calculate_suggestion_priority(
        self,
        field: dict,
        current_layer: InfoLayer,
        conversation_context: list[Utterance],
    ) -> float:
        """サジェスト優先度を計算する.

        水野メソッドに基づく優先度計算:
        - 現在のレイヤーに近いほど高優先度
        - 会話の文脈に関連するほど高優先度
        - 買い手が重視する情報（出口レイヤー）は常に高め

        Args:
            field: フィールド情報
            current_layer: 現在のレイヤー
            conversation_context: 会話文脈

        Returns:
            float: 優先度（0-1）
        """
        base_priority = 0.5

        # レイヤー距離による調整
        layer_order = [InfoLayer.SURFACE, InfoLayer.STRUCTURE, InfoLayer.ESSENCE, InfoLayer.EXIT]
        field_layer = field.get("layer", InfoLayer.SURFACE)

        try:
            current_idx = layer_order.index(current_layer)
            field_idx = layer_order.index(field_layer)
            distance = abs(current_idx - field_idx)
            layer_adjustment = 0.2 - (distance * 0.1)
        except ValueError:
            layer_adjustment = 0

        # 出口レイヤーは常に重要
        exit_bonus = 0.15 if field_layer == InfoLayer.EXIT else 0

        # 文脈関連性（簡易実装: キーワードマッチ）
        context_text = " ".join([u.text for u in conversation_context[-3:]])
        field_label = field.get("label", "")
        context_bonus = 0.1 if field_label in context_text else 0

        priority = base_priority + layer_adjustment + exit_bonus + context_bonus
        return max(0.0, min(1.0, priority))
