"""
聖人君子AI - 振り返りAPI
セッション終了後のサマリーと改善ポイントを生成
"""
import logging
import json
import re
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from anthropic import AsyncAnthropic

from ..core import verify_supabase_token, settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["reflection"])

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """あなたは管理職のマネジメントを支援するAIです。
1on1の会話を振り返り、建設的なフィードバックを提供してください。

## 出力形式
必ず以下のJSON形式のみで回答してください。

```json
{
  "summary": "会話の要約（2-3文）",
  "positive_points": [
    "良かった点1",
    "良かった点2"
  ],
  "improvement_points": [
    "改善できる点1",
    "改善できる点2"
  ],
  "next_actions": [
    "次回へのアクション1",
    "次回へのアクション2"
  ]
}
```

## ガイドライン
- ポジティブなトーンで書く
- 具体的で実践可能なフィードバックを提供
- リスク発言があった場合は、改善点として優しく言及
- 次回アクションは2-3個に絞る
"""


class RiskEvent(BaseModel):
    time: str
    text: str
    risk_level: str
    analysis: str
    rephrase: str


class ReflectionRequest(BaseModel):
    transcript: str
    risk_events: List[RiskEvent] = []


class ReflectionResponse(BaseModel):
    summary: str
    positive_points: List[str]
    improvement_points: List[str]
    next_actions: List[str]


@router.post("/reflection", response_model=ReflectionResponse)
async def generate_reflection(
    request: ReflectionRequest,
    user=Depends(verify_supabase_token)
):
    """セッションの振り返りを生成"""
    try:
        # Build context with risk events
        risk_context = ""
        if request.risk_events:
            risk_context = "\n\n## 検知されたリスク発言:\n"
            for event in request.risk_events:
                risk_context += f"- [{event.time}] 「{event.text}」({event.risk_level})\n"

        logger.info(f"[聖人君子AI] Generating reflection...")

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"以下の1on1を振り返ってください:\n\n{request.transcript}{risk_context}"
                }
            ]
        )

        text = response.content[0].text
        logger.info(f"[聖人君子AI] Reflection response: {text[:300]}...")

        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            return ReflectionResponse(
                summary=data.get("summary", "会話の振り返りを生成できませんでした。"),
                positive_points=data.get("positive_points", []),
                improvement_points=data.get("improvement_points", []),
                next_actions=data.get("next_actions", [])
            )

        # Fallback
        return ReflectionResponse(
            summary="会話の振り返りを生成できませんでした。",
            positive_points=[],
            improvement_points=[],
            next_actions=[]
        )

    except Exception as e:
        logger.error(f"[聖人君子AI] Reflection error: {str(e)}")
        return ReflectionResponse(
            summary="エラーが発生しました。",
            positive_points=[],
            improvement_points=[],
            next_actions=[]
        )
