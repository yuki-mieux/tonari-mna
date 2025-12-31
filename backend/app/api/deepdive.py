"""
深掘りサポート API
面接の文字起こしをもとに深掘り質問を提案する
"""
import os
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from anthropic import AsyncAnthropic

from ..core import verify_supabase_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["deepdive"])


# ===== Request/Response Models =====
class CheckedItem(BaseModel):
    id: str
    value: str


class DeepDiveRequest(BaseModel):
    transcript: str
    checked_items: List[CheckedItem] = []


class QuestionSuggestion(BaseModel):
    type: str  # "suggest" | "warning" | "action"
    question: str
    reason: Optional[str] = None


class DeepDiveResponse(BaseModel):
    suggestions: List[QuestionSuggestion]


# ===== System Prompt =====
DEEPDIVE_SYSTEM_PROMPT = """あなたは面接官の「隣にいる相棒」。
面接の会話を分析し、より良い質問の仕方や、足りていない質問、候補者のインサイトを引き出すための深掘り質問を提案する。

## タスク
会話を分析し、以下の観点で質問提案を行う：
1. **より良い聞き方**: 曖昧な回答に対して、より具体的な情報を引き出す質問
2. **足りていない質問**: 重要だが聞けていない項目
3. **深い洞察を得る質問**: 候補者の本音や価値観を引き出す質問

## 面接の構造
【自分】= 面接官（質問する側）
【相手】= 求職者（回答する側）

## チェック済み項目
ユーザーから提供されるchecked_itemsは既に確認できた項目。
これらは再度質問する必要がないが、深掘りの余地があれば提案してよい。

## 出力形式
必ず以下のJSON形式のみを返す。説明文や前置きは一切不要。

```json
{
  "suggestions": [
    {
      "type": "suggest | warning | action",
      "question": "提案する質問文",
      "reason": "なぜこの質問が有効か（短く）"
    }
  ]
}
```

## typeの意味
- **suggest**: 深掘り提案（インサイトを引き出す質問）
- **warning**: 確認推奨（矛盾や曖昧な点への確認）
- **action**: 質問が足りない（重要項目が未確認）

## 提案の優先度
1. 矛盾点や曖昧な回答への確認（warning）
2. 重要だが聞けていない項目（action）
3. より深い洞察を得る質問（suggest）

## 注意
- 提案は3〜5個程度に絞る
- 具体的で実行可能な質問文を提案
- 面接官がそのまま使える自然な日本語で
- JSON以外の出力は禁止
"""


# ===== Claude Client =====
client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@router.post("/deepdive", response_model=DeepDiveResponse)
async def get_deepdive_suggestions(
    request: DeepDiveRequest,
    user=Depends(verify_supabase_token)
):
    """
    面接の文字起こしをもとに深掘り質問を提案
    """
    if not request.transcript or len(request.transcript) < 50:
        # 文字起こしが短すぎる場合は空を返す
        return DeepDiveResponse(suggestions=[])
    
    try:
        # チェック済み項目をコンテキストとして追加
        checked_context = ""
        if request.checked_items:
            items_str = "\n".join([f"- {item.id}: {item.value}" for item in request.checked_items])
            checked_context = f"\n\n## 既に確認できた項目\n{items_str}"
        
        user_message = f"""直近の面接会話:
{request.transcript}
{checked_context}

上記の会話を分析し、深掘り質問を提案してください。"""

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=DEEPDIVE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        
        # レスポンスからJSONを抽出
        response_text = response.content[0].text if response.content else ""
        suggestions = parse_suggestions(response_text)
        
        return DeepDiveResponse(suggestions=suggestions)
        
    except Exception as e:
        logger.error(f"DeepDive API error: {str(e)}")
        return DeepDiveResponse(suggestions=[])


def parse_suggestions(text: str) -> List[QuestionSuggestion]:
    """
    Claude応答からsuggestions配列を抽出
    """
    import json
    
    if not text:
        return []
    
    # ```json ... ``` ブロックを探す
    import re
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if "suggestions" in data and isinstance(data["suggestions"], list):
                return [
                    QuestionSuggestion(
                        type=s.get("type", "suggest"),
                        question=s.get("question", ""),
                        reason=s.get("reason")
                    )
                    for s in data["suggestions"]
                    if s.get("question")
                ]
        except json.JSONDecodeError:
            pass
    
    # 直接JSONを探す
    json_match = re.search(r'\{[\s\S]*"suggestions"[\s\S]*\}', text)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            if "suggestions" in data and isinstance(data["suggestions"], list):
                return [
                    QuestionSuggestion(
                        type=s.get("type", "suggest"),
                        question=s.get("question", ""),
                        reason=s.get("reason")
                    )
                    for s in data["suggestions"]
                    if s.get("question")
                ]
        except json.JSONDecodeError:
            pass
    
    return []
