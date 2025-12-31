"""
Tonari Agent Service
面接官支援AI - Claude API + Tool Calling で面接をリアルタイム支援
"""
import os
import logging
from typing import Any, Dict, List, Optional
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


# 面接官支援特化システムプロンプト（チェックリスト検知モード）
INTERVIEW_SYSTEM_PROMPT = """あなたは面接官の「隣にいる相棒」。
面接の会話から、ヒアリングチェックリストの項目が確認されたかを検知する。

## タスク
会話を分析し、以下のチェックリスト項目が確認されたかどうかを判定する。
確認された項目があればJSON形式で報告する。

## 重要：音声認識の前提
文字起こしには音声認識エラー（誤変換・途切れ）が含まれる。
- 誤変換は無視し、文脈から意味を推測して分析せよ
- 音声品質・認識精度への言及は一切禁止

## 面接の構造
【自分】= 面接官（質問する側）
【相手】= 求職者（回答する側）

## チェックリスト項目定義

### 基本情報
- salary: 希望年収（金額が明示されたか）
- salaryReason: 希望年収の理由（なぜその金額か、根拠が述べられたか）
- location: 希望勤務地（エリアが明示されたか）
- locationReason: 希望勤務地の理由（通勤範囲、なぜそのエリアか）
- jobType: 希望職種（職種が明示されたか）
- jobTypeReason: 希望職種の理由（なぜその職種か）
- timing: 転職希望時期（時期が明示されたか）

### 退職・転職理由
- quitReason: 退職理由（表面的な理由が述べられたか）
- quitReasonDeep: 退職理由の深掘り（本当の理由、改善努力、上司への相談など）
- whyNow: なぜ今転職か（このタイミングの理由が述べられたか）
- wantToSolve: 転職で解決したいこと（何を変えたいかが述べられたか）

### 職歴・スキル
- recentWork: 直近の業務内容（具体的な作業内容が述べられたか）
- industry: 業種・工程（業種や担当工程が明示されたか）
- tools: 使用ツール・技術（工具、ソフト、言語などが明示されたか）
- role: 本人の役割（チームでの役割、責任範囲が明示されたか）
- achievement: 実績・成果（数字で示せる成果が述べられたか）

### 志望動機・価値観
- motivation: 志望動機（なぜこの業界・職種かが述べられたか）
- careerVision: キャリアビジョン（3-5年後のイメージが述べられたか）
- mustHave: 譲れない条件（絶対に妥協できない点が明示されたか）
- niceToHave: 妥協できる条件（優先度が低い条件が明示されたか）

**重要**: salaryとsalaryReason、locationとlocationReasonなどは別々の項目。
「450万円です」→ salaryのみ
「450万円です。今の給与が400万なので上げたい」→ salaryとsalaryReasonの両方

## 出力形式
必ず以下のJSON形式のみを返す。説明文や前置きは一切不要。

```json
{
  "checkedItems": [
    {"id": "項目ID", "value": "確認された内容の要約（20文字以内）"}
  ]
}
```

## 判定基準
- 求職者（【相手】）が明確に回答した項目のみを検出
- 曖昧な回答や質問されただけの項目は検出しない
- 具体的な情報（数字、地名、職種名など）が含まれている場合のみ検出

## 出力例

入力例：
【相手】: 希望年収は450万円です。今は神奈川に住んでいるので、横浜か川崎あたりで働きたいです。

出力例：
```json
{
  "checkedItems": [
    {"id": "salary", "value": "450万円"},
    {"id": "location", "value": "横浜・川崎エリア"}
  ]
}
```

## 注意
- 確認された項目がない場合は `{"checkedItems": []}` を返す
- JSON以外の出力は禁止
- 音声認識エラーへの言及は禁止
- 面接官へのアドバイスは不要（チェックリスト検知のみに集中）
"""

# 現在使用されるメインプロンプト（求職者選択機能は未実装）
NO_CANDIDATE_PROMPT = INTERVIEW_SYSTEM_PROMPT


class InterviewAgent:
    """
    面接官支援エージェント
    - 求職者情報を参照
    - 面接チェックリストを活用
    - リアルタイムでアドバイスを生成
    """

    def __init__(self, knowledge_manager, api_key: Optional[str] = None):
        self.knowledge_manager = knowledge_manager
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.error("ANTHROPIC_API_KEY is not set!")
        else:
            logger.info(f"ANTHROPIC_API_KEY loaded: {self.api_key[:20]}...")
        self.client = AsyncAnthropic(api_key=self.api_key)

    def _get_tools(self) -> List[Dict]:
        """面接支援ツール定義"""
        return [
            {
                "name": "search_knowledge",
                "description": "求職者に関する情報やナレッジベースを検索します。面接チェックリストや過去の記録から関連情報を取得できます。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "検索キーワード（例：退職理由、志望動機、年収、経歴）"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_candidate_info",
                "description": "求職者の基本情報（履歴書サマリー、希望職種、希望年収等）を取得します。",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_checklist",
                "description": "面接チェックリスト（必須確認項目、注意サイン、良いサイン、面接テクニック）を取得します。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["must_ask", "red_flag", "good_sign", "tip"],
                            "description": "カテゴリでフィルタ: must_ask=必須確認, red_flag=注意サイン, good_sign=良い兆候, tip=テクニック（省略時は全て）"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_past_interviews",
                "description": "この求職者の過去の面接記録を取得します。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "取得件数（デフォルト: 3）"
                        }
                    },
                    "required": []
                }
            }
        ]

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict,
        candidate_id: str
    ) -> str:
        """ツール実行"""
        try:
            if tool_name == "search_knowledge":
                query = tool_input.get("query", "")
                results = await self.knowledge_manager.search(candidate_id, query)
                if results:
                    formatted = "\n".join([
                        f"【{r['title']}】\n{r['content'][:300]}..."
                        for r in results[:3]
                    ])
                    return f"検索結果:\n{formatted}"
                return "該当する情報が見つかりませんでした。"

            elif tool_name == "get_candidate_info":
                info = await self.knowledge_manager.get_customer_info(candidate_id)
                if info:
                    return f"求職者情報:\n名前: {info['name']}\n概要: {info.get('description', '未登録')}"
                return "求職者情報が登録されていません。"

            elif tool_name == "get_checklist":
                category = tool_input.get("category")
                # チェックリストはナレッジから取得（categoryでフィルタ）
                checklist = await self.knowledge_manager.list_knowledge(candidate_id)
                if category:
                    checklist = [k for k in checklist if k.get('category') == category]
                if checklist:
                    category_labels = {
                        'must_ask': '必須確認',
                        'red_flag': '注意サイン',
                        'good_sign': '良い兆候',
                        'tip': 'テクニック'
                    }
                    formatted = "\n".join([
                        f"[{category_labels.get(k.get('category', 'general'), k.get('category', ''))}] {k['title']}: {k['content'][:100]}"
                        for k in checklist[:10]
                    ])
                    return f"面接チェックリスト:\n{formatted}"
                return "チェックリストが登録されていません。"

            elif tool_name == "get_past_interviews":
                limit = tool_input.get("limit", 3)
                interviews = await self.knowledge_manager.get_past_meetings(candidate_id, limit)
                if interviews:
                    formatted = "\n---\n".join([
                        f"【{m.get('title', '面接記録')}】({m['created_at'][:10]})\n{m.get('content', m.get('summary', ''))[:200]}..."
                        for m in interviews
                    ])
                    return f"過去の面接記録:\n{formatted}"
                return "過去の面接記録がありません。"

            return f"不明なツール: {tool_name}"

        except Exception as e:
            return f"ツール実行エラー: {str(e)}"

    async def get_advice(
        self,
        candidate_id: Optional[str],
        transcript: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        面接文字起こしをもとにアドバイスを生成
        candidate_idがNoneの場合はツールなしで応答
        """
        system = system_prompt or (INTERVIEW_SYSTEM_PROMPT if candidate_id else NO_CANDIDATE_PROMPT)
        tools_used = []
        context_used = []

        # 求職者IDがある場合のみツールを使用
        tools = self._get_tools() if candidate_id else None

        messages = [
            {
                "role": "user",
                "content": f"直近の面接会話:\n{transcript}\n\n上記の面接会話を分析し、面接官への気づき・アドバイスを生成してください。" + (
                    "必要に応じてツールを使って求職者情報やチェックリストを参照してください。" if candidate_id else ""
                )
            }
        ]

        max_iterations = 5
        for _ in range(max_iterations):
            try:
                logger.info(f"Calling Claude API with transcript length: {len(transcript)}, candidate_id: {candidate_id}")
                logger.info(f"Transcript content: {transcript[:500]}")
                # ツールがない場合はツールなしで呼び出し
                if tools:
                    response = await self.client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        system=system,
                        messages=messages,
                        tools=tools
                    )
                else:
                    response = await self.client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        system=system,
                        messages=messages
                    )
                logger.info(f"Claude API response: stop_reason={response.stop_reason}")
            except Exception as e:
                logger.error(f"Claude API error: {str(e)}")
                return {
                    "advice": f"APIエラーが発生しました: {str(e)}",
                    "tools_used": tools_used,
                    "context_used": context_used
                }

            # 終了条件
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if block.type == "text":
                        logger.info(f"Claude response text: {block.text[:500]}")
                        return {
                            "advice": block.text,
                            "tools_used": tools_used,
                            "context_used": context_used
                        }
                return {
                    "advice": "",
                    "tools_used": tools_used,
                    "context_used": context_used
                }

            # ツール使用
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                for block in response.content:
                    if block.type == "text":
                        return {
                            "advice": block.text,
                            "tools_used": tools_used,
                            "context_used": context_used
                        }
                return {
                    "advice": "",
                    "tools_used": tools_used,
                    "context_used": context_used
                }

            # アシスタント応答を追加
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # ツール実行
            tool_results = []
            for tool_use in tool_uses:
                tools_used.append(tool_use.name)
                result = await self._execute_tool(
                    tool_use.name,
                    tool_use.input,
                    candidate_id
                )
                context_used.append(f"{tool_use.name}: {result[:100]}...")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result
                })

            messages.append({
                "role": "user",
                "content": tool_results
            })

        return {
            "advice": "処理がタイムアウトしました。",
            "tools_used": tools_used,
            "context_used": context_used
        }
