"""
TONARI for M&A - FastAPI Backend
M&Aアドバイザーの隣にいる、最高の相棒
"""
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .api import mna_session, mna_project
from .core import settings

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# APIキー確認
if settings.ANTHROPIC_API_KEY:
    logger.info(f"ANTHROPIC_API_KEY is set: {settings.ANTHROPIC_API_KEY[:20]}...")
else:
    logger.error("ANTHROPIC_API_KEY is NOT set!")

app = FastAPI(
    title="TONARI for M&A API",
    description="M&Aアドバイザーの隣にいる、最高の相棒。水野メソッドでヒアリングを支援し、IM作成を自動化。",
    version="1.0.0"
)

# CORS設定（本番ではFRONTEND_URL環境変数で制限推奨）
frontend_url = os.getenv("FRONTEND_URL", "*")
allow_origins = [frontend_url] if frontend_url != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TONARI for M&A ルーター
app.include_router(mna_session.router)
app.include_router(mna_project.router)


@app.get("/")
async def root():
    """ルートエンドポイント."""
    return {
        "name": "TONARI for M&A API",
        "version": "1.0.0",
        "description": "M&Aアドバイザーの隣にいる、最高の相棒",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """ヘルスチェック."""
    return {"status": "healthy"}


@app.get("/api/config")
async def get_config():
    """設定情報を返す（認証必須に変更推奨）."""
    return {
        "deepgram_api_key": settings.DEEPGRAM_API_KEY,
    }
