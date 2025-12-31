"""
聖人君子AI - ハラスメントリスク検知API
会話をリアルタイムで分析し、パワハラリスクのある発言を検知
"""
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from anthropic import AsyncAnthropic

from ..core import verify_supabase_token, settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["harassment"])

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """あなたは管理職のマネジメントを支援するAIです。
会話を分析し、パワハラリスクのある発言を検知してください。

## 検知対象
- 人格否定: 「君はダメだ」「使えない」など
- 過度な叱責: 「なぜできないの」「何度言ったらわかる」など
- 威圧的な言動: 「いいから黙ってやれ」など
- 能力否定: 「君には無理」「向いてない」など
- 責任追及: 「お前のせいだ」「責任取れ」など

## 重要
- 【自分】の発言のみを分析対象とする（管理職の発言）
- 問題がなければ risk_detected: false を返す
- 音声認識エラーへの言及は禁止
- 必ずJSON形式のみで回答

## 出力形式
```json
{
  "risk_detected": true/false,
  "risk_level": "high" | "medium" | "none",
  "detected_text": "問題のある発言テキスト",
  "analysis": "なぜ問題なのか（30文字以内）",
  "rephrase": "言い換え提案（具体的なフレーズ）"
}
```

## 例
入力: 【自分】: なぜこんなこともできないの？
出力:
```json
{
  "risk_detected": true,
  "risk_level": "high",
  "detected_text": "なぜこんなこともできないの？",
  "analysis": "詰問形式で相手を追い詰める表現",
  "rephrase": "具体的にどこで詰まっていますか？"
}
```
"""


class HarassmentCheckRequest(BaseModel):
    transcript: str


class HarassmentCheckResponse(BaseModel):
    risk_detected: bool
    risk_level: str
    detected_text: str = ""
    analysis: str = ""
    rephrase: str = ""


@router.post("/harassment_check", response_model=HarassmentCheckResponse)
async def check_harassment(
    request: HarassmentCheckRequest,
    user=Depends(verify_supabase_token)
):
    """会話からパワハラリスクを検知"""
    try:
        logger.info(f"[聖人君子AI] Checking transcript: {request.transcript[:200]}...")

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"以下の会話を分析してください:\n\n{request.transcript}"
                }
            ]
        )

        # Parse response
        text = response.content[0].text
        logger.info(f"[聖人君子AI] Response: {text}")

        # Extract JSON from response
        import json
        import re

        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            return HarassmentCheckResponse(
                risk_detected=data.get("risk_detected", False),
                risk_level=data.get("risk_level", "none"),
                detected_text=data.get("detected_text", ""),
                analysis=data.get("analysis", ""),
                rephrase=data.get("rephrase", "")
            )

        # No risk detected if can't parse
        return HarassmentCheckResponse(
            risk_detected=False,
            risk_level="none"
        )

    except Exception as e:
        logger.error(f"[聖人君子AI] Error: {str(e)}")
        return HarassmentCheckResponse(
            risk_detected=False,
            risk_level="none"
        )
