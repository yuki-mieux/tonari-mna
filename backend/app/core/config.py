"""
アプリケーション設定
環境変数から設定を読み込み
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """アプリケーション設定"""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # JWT Cache
    TOKEN_CACHE_TTL: int = 300  # 5分
    TOKEN_CACHE_MAX_SIZE: int = 100


settings = Settings()
