"""
ヒアリングチェック API
面接の文字起こしからチェックリスト項目を検知する
"""
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.schemas import AdviceRequest, AdviceResponse
from ..services.knowledge import KnowledgeManager
from ..services.agent import InterviewAgent
from ..core import verify_supabase_token

router = APIRouter(prefix="/api", tags=["hearing"])

knowledge_manager = KnowledgeManager()
agent = InterviewAgent(knowledge_manager)
security = HTTPBearer(auto_error=False)


def get_auth_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Authorizationヘッダーからトークンを取得"""
    return credentials.credentials if credentials else None


# 後方互換性のため /advice も維持
@router.post("/advice", response_model=AdviceResponse)
@router.post("/hearing", response_model=AdviceResponse)
async def get_hearing_check(
    request: AdviceRequest,
    user=Depends(verify_supabase_token),
    token: str = Depends(get_auth_token)
):
    """
    面接文字起こしからヒアリングチェックリスト項目を検知
    """
    if token:
        knowledge_manager.set_auth_token(token)

    result = await agent.get_advice(
        candidate_id=request.customer_id,
        transcript=request.transcript,
        system_prompt=request.system_prompt
    )

    return AdviceResponse(
        advice=result["advice"],
        tools_used=result["tools_used"],
        context_used=result["context_used"]
    )



