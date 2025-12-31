"""
TONARI for M&A - 情報抽出サービス
音声テキストからIM項目を構造化抽出する
"""
import json
import logging
from datetime import datetime
from typing import Optional

from anthropic import AsyncAnthropic

from ..core.config import settings
from ..models.mna_schemas import (
    ExtractionCategory,
    ExtractionField,
    ExtractionResult,
    InfoLayer,
    IM_EXTRACTION_FIELDS,
    Utterance,
)

logger = logging.getLogger(__name__)


class MnAExtractionService:
    """M&A情報抽出サービス.

    Attributes:
        client: Anthropic APIクライアント
        model: 使用するモデル名
    """

    def __init__(self) -> None:
        """サービスを初期化する."""
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    async def extract_from_utterances(
        self,
        session_id: str,
        new_utterances: list[Utterance],
        current_extractions: dict[str, ExtractionField],
    ) -> ExtractionResult:
        """発話から情報を抽出する.

        Args:
            session_id: セッションID
            new_utterances: 新しい発話リスト
            current_extractions: 現在の抽出情報

        Returns:
            ExtractionResult: 抽出結果
        """
        prompt = self._build_extraction_prompt(new_utterances, current_extractions)
        schema = self._build_extraction_schema()

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                tools=[
                    {
                        "name": "extract_mna_info",
                        "description": "M&Aヒアリングから情報を抽出する",
                        "input_schema": schema,
                    }
                ],
                tool_choice={"type": "tool", "name": "extract_mna_info"},
            )

            # ツール使用結果を解析
            tool_use = next(
                (block for block in response.content if block.type == "tool_use"),
                None,
            )

            if tool_use is None:
                logger.warning("No tool use in response")
                return ExtractionResult(session_id=session_id, fields=[])

            extracted_data = tool_use.input
            fields = self._parse_extraction_response(extracted_data)

            return ExtractionResult(
                session_id=session_id,
                fields=fields,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractionResult(session_id=session_id, fields=[])

    def _build_extraction_prompt(
        self,
        new_utterances: list[Utterance],
        current_extractions: dict[str, ExtractionField],
    ) -> str:
        """抽出プロンプトを構築する.

        Args:
            new_utterances: 新しい発話リスト
            current_extractions: 現在の抽出情報

        Returns:
            str: プロンプト文字列
        """
        # 現在の抽出情報をフォーマット
        current_info_lines = []
        for category in ExtractionCategory:
            category_fields = IM_EXTRACTION_FIELDS.get(category, [])
            for field_def in category_fields:
                field_key = f"{category.value}.{field_def['field']}"
                extraction = current_extractions.get(field_key)
                if extraction and extraction.value:
                    current_info_lines.append(
                        f"- {field_def['label']}: {extraction.value}"
                    )
                else:
                    current_info_lines.append(f"- {field_def['label']}: (未取得)")

        current_info = "\n".join(current_info_lines)

        # 新しい発話をフォーマット
        utterance_lines = []
        for u in new_utterances:
            speaker_label = "アドバイザー" if u.speaker == "user" else "売り手"
            utterance_lines.append(f"[{speaker_label}] {u.text}")
        new_conversation = "\n".join(utterance_lines)

        return f"""あなたはM&Aアドバイザーのアシスタントです。
以下の会話から、M&A検討に必要な情報を抽出してください。

## これまでの抽出情報
{current_info}

## 新しい会話
{new_conversation}

## 抽出対象
以下のカテゴリから、新しく抽出できた情報のみを出力してください：

### 基本情報
会社名、所在地、設立年、資本金、従業員数、代表者、代表者プロフィール、沿革

### 財務情報
売上高（直近）、売上高推移、営業利益、経常利益、純資産、調整後純資産、借入金、主要KPI

### 事業情報
事業内容、主要サービス/製品、主要取引先、顧客構成、競合優位性、強み、弱み、業界動向、市場ポジション

### 組織情報
組織体制、キーパーソン、後継者有無、従業員の処遇、役員の残留意向

### 譲渡情報
譲渡スキーム、譲渡理由、希望価格、希望時期、希望条件、DD留意事項

注意事項：
- 明確に言及された情報のみを抽出
- 推測は避け、確信度を0-1で示す
- 既に取得済みの情報は出力しない
- 具体的な数値や固有名詞を正確に抽出
"""

    def _build_extraction_schema(self) -> dict:
        """抽出スキーマを構築する.

        Returns:
            dict: JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "extractions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": [c.value for c in ExtractionCategory],
                                "description": "抽出カテゴリ",
                            },
                            "field": {
                                "type": "string",
                                "description": "フィールド名（英語）",
                            },
                            "value": {
                                "type": "string",
                                "description": "抽出した値",
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "確信度（0-1）",
                            },
                        },
                        "required": ["category", "field", "value", "confidence"],
                    },
                },
            },
            "required": ["extractions"],
        }

    def _parse_extraction_response(self, data: dict) -> list[ExtractionField]:
        """抽出レスポンスをパースする.

        Args:
            data: APIレスポンスデータ

        Returns:
            list[ExtractionField]: 抽出フィールドリスト
        """
        fields = []
        extractions = data.get("extractions", [])

        for item in extractions:
            try:
                category = ExtractionCategory(item["category"])
                field_name = item["field"]

                # フィールド定義からレイヤーを取得
                layer = InfoLayer.SURFACE
                category_fields = IM_EXTRACTION_FIELDS.get(category, [])
                for field_def in category_fields:
                    if field_def["field"] == field_name:
                        layer = field_def.get("layer", InfoLayer.SURFACE)
                        break

                fields.append(
                    ExtractionField(
                        category=category,
                        field=field_name,
                        value=item["value"],
                        confidence=item["confidence"],
                        layer=layer,
                    )
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse extraction: {e}")
                continue

        return fields

    def get_missing_fields(
        self,
        current_extractions: dict[str, ExtractionField],
        priority_layer: Optional[InfoLayer] = None,
    ) -> list[dict]:
        """未取得フィールドを取得する.

        Args:
            current_extractions: 現在の抽出情報
            priority_layer: 優先するレイヤー（指定時はそのレイヤーを優先）

        Returns:
            list[dict]: 未取得フィールドリスト（優先度順）
        """
        missing = []

        for category in ExtractionCategory:
            category_fields = IM_EXTRACTION_FIELDS.get(category, [])
            for field_def in category_fields:
                field_key = f"{category.value}.{field_def['field']}"
                extraction = current_extractions.get(field_key)

                if extraction is None or extraction.value is None:
                    missing.append(
                        {
                            "category": category.value,
                            "field": field_def["field"],
                            "label": field_def["label"],
                            "layer": field_def.get("layer", InfoLayer.SURFACE),
                        }
                    )

        # レイヤー優先度でソート（表層→構造→本質→出口）
        layer_priority = {
            InfoLayer.SURFACE: 0,
            InfoLayer.STRUCTURE: 1,
            InfoLayer.ESSENCE: 2,
            InfoLayer.EXIT: 3,
        }

        if priority_layer:
            # 指定レイヤーを最優先
            missing.sort(
                key=lambda x: (
                    0 if x["layer"] == priority_layer else 1,
                    layer_priority.get(x["layer"], 99),
                )
            )
        else:
            missing.sort(key=lambda x: layer_priority.get(x["layer"], 99))

        return missing

    def calculate_extraction_progress(
        self,
        current_extractions: dict[str, ExtractionField],
    ) -> dict:
        """抽出進捗を計算する.

        Args:
            current_extractions: 現在の抽出情報

        Returns:
            dict: 進捗情報
        """
        total = 0
        filled = 0
        by_category = {}
        by_layer = {layer: {"total": 0, "filled": 0} for layer in InfoLayer}

        for category in ExtractionCategory:
            category_fields = IM_EXTRACTION_FIELDS.get(category, [])
            category_total = len(category_fields)
            category_filled = 0

            for field_def in category_fields:
                field_key = f"{category.value}.{field_def['field']}"
                extraction = current_extractions.get(field_key)
                layer = field_def.get("layer", InfoLayer.SURFACE)

                total += 1
                by_layer[layer]["total"] += 1

                if extraction and extraction.value:
                    filled += 1
                    category_filled += 1
                    by_layer[layer]["filled"] += 1

            by_category[category.value] = {
                "total": category_total,
                "filled": category_filled,
                "percentage": (
                    round(category_filled / category_total * 100, 1)
                    if category_total > 0
                    else 0
                ),
            }

        return {
            "total": total,
            "filled": filled,
            "percentage": round(filled / total * 100, 1) if total > 0 else 0,
            "by_category": by_category,
            "by_layer": {
                layer.value: {
                    "total": data["total"],
                    "filled": data["filled"],
                    "percentage": (
                        round(data["filled"] / data["total"] * 100, 1)
                        if data["total"] > 0
                        else 0
                    ),
                }
                for layer, data in by_layer.items()
            },
        }
