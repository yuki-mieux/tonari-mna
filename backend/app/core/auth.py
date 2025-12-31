"""
Supabase JWT認証
- ローカルでJWTをデコード・基本検証
- Supabase APIで完全検証（初回のみ）
- トークン検証結果をキャッシュ
"""
import time
import base64
import json
from typing import Optional, Dict
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from .config import settings

security = HTTPBearer(auto_error=False)

# トークン検証キャッシュ: token -> (user_data, expires_at)
_token_cache: Dict[str, tuple] = {}


def _decode_jwt_payload(token: str) -> Optional[dict]:
    """JWTのペイロードをデコード（署名検証なし）"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return None


def _is_token_expired(payload: dict) -> bool:
    """JWTの有効期限をチェック"""
    exp = payload.get('exp')
    return not exp or time.time() > exp


def _get_cached_user(token: str) -> Optional[dict]:
    """キャッシュからユーザー情報を取得"""
    if token in _token_cache:
        user_data, expires_at = _token_cache[token]
        if time.time() < expires_at:
            return user_data
        del _token_cache[token]
    return None


def _cache_user(token: str, user_data: dict):
    """ユーザー情報をキャッシュに保存"""
    _token_cache[token] = (user_data, time.time() + settings.TOKEN_CACHE_TTL)
    # 古いエントリを削除
    if len(_token_cache) > settings.TOKEN_CACHE_MAX_SIZE:
        now = time.time()
        expired = [k for k, (_, exp) in _token_cache.items() if exp < now]
        for k in expired:
            del _token_cache[k]


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Supabase JWTトークンを検証

    1. キャッシュをチェック
    2. JWTをローカルでデコード・基本検証
    3. Supabase APIで完全検証
    4. 結果をキャッシュ
    """
    # 環境変数が未設定ならスキップ（ローカル開発用）
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return None

    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    token = credentials.credentials

    # キャッシュチェック
    cached_user = _get_cached_user(token)
    if cached_user:
        return cached_user

    # JWTデコード・基本検証
    payload = _decode_jwt_payload(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token format")

    if _is_token_expired(payload):
        raise HTTPException(status_code=401, detail="Token has expired")

    if 'supabase' not in payload.get('iss', ''):
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    # Supabase APIで完全検証
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.SUPABASE_ANON_KEY
                },
                timeout=10.0
            )

            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid or expired token")

            user_data = response.json()
            _cache_user(token, user_data)
            return user_data

        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Authentication service unavailable")
