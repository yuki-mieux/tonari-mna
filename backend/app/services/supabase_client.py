"""
Supabase Client for Tonari
"""
import os
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """
    Supabaseクライアントを取得
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

    return create_client(url, key)


# シングルトンインスタンス
_supabase_client: Client = None


def get_supabase() -> Client:
    """
    シングルトンでSupabaseクライアントを取得
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client
