"""
Knowledge Manager for Tonari
顧客・ナレッジ・メモをSupabaseで管理
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
from supabase import create_client, Client


class KnowledgeManager:
    """
    Supabaseベースの顧客知識管理
    RLSポリシーでユーザーごとにデータ分離
    """

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self._client: Optional[Client] = None
        self._auth_token: Optional[str] = None

    def set_auth_token(self, token: str):
        """認証トークンを設定（リクエストごとに呼び出し）"""
        self._auth_token = token

    @property
    def client(self) -> Client:
        """Supabaseクライアントを取得"""
        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY are required")

        client = create_client(self.supabase_url, self.supabase_key)
        if self._auth_token:
            client.postgrest.auth(self._auth_token)
        return client

    # ===== 顧客管理 =====

    async def create_customer(self, name: str, description: str = "") -> Dict:
        """顧客作成"""
        data = {"name": name, "description": description}
        result = self.client.table("customers").insert(data).execute()
        if result.data:
            return result.data[0]
        raise Exception("Failed to create customer")

    async def get_customer(self, customer_id: str) -> Optional[Dict]:
        """顧客取得"""
        result = self.client.table("customers").select("*").eq("id", customer_id).execute()
        return result.data[0] if result.data else None

    async def list_customers(self) -> List[Dict]:
        """顧客一覧"""
        result = self.client.table("customers").select("*").order("created_at", desc=True).execute()
        return result.data or []

    async def delete_customer(self, customer_id: str) -> bool:
        """顧客削除（カスケードでknowledge, memosも削除）"""
        result = self.client.table("customers").delete().eq("id", customer_id).execute()
        return bool(result.data)

    # ===== ナレッジ管理 =====

    async def add_knowledge(self, customer_id: str, title: str, content: str, category: str = "general") -> Dict:
        """ナレッジを追加"""
        data = {
            "customer_id": customer_id,
            "title": title,
            "content": content,
            "category": category
        }
        result = self.client.table("knowledge").insert(data).execute()
        if result.data:
            return result.data[0]
        raise Exception("Failed to add knowledge")

    async def list_knowledge(self, customer_id: str) -> List[Dict]:
        """顧客のナレッジ一覧"""
        result = (
            self.client.table("knowledge")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """ナレッジ削除"""
        result = self.client.table("knowledge").delete().eq("id", knowledge_id).execute()
        return bool(result.data)

    # ===== メモ管理 =====

    async def save_meeting(self, customer_id: str, content: str, meeting_date: datetime = None) -> Dict:
        """会話メモを保存"""
        data = {"customer_id": customer_id, "summary": content}
        result = self.client.table("memos").insert(data).execute()
        if result.data:
            return result.data[0]
        raise Exception("Failed to save meeting")

    async def list_memos(self, customer_id: str) -> List[Dict]:
        """顧客のメモ一覧"""
        result = (
            self.client.table("memos")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    # ===== Agent用メソッド =====

    async def search(self, customer_id: str, query: str) -> List[Dict]:
        """ナレッジを検索"""
        try:
            result = (
                self.client.table("knowledge")
                .select("*")
                .eq("customer_id", customer_id)
                .or_(f"title.ilike.%{query}%,content.ilike.%{query}%")
                .limit(10)
                .execute()
            )
            return result.data or []
        except Exception:
            # フォールバック: 全件取得してPythonでフィルタ
            result = self.client.table("knowledge").select("*").eq("customer_id", customer_id).execute()
            query_lower = query.lower()
            filtered = [
                k for k in (result.data or [])
                if query_lower in k.get("title", "").lower() or query_lower in k.get("content", "").lower()
            ]
            return filtered[:10]

    async def get_customer_info(self, customer_id: str) -> Optional[Dict]:
        """顧客基本情報を取得（Agent用）"""
        return await self.get_customer(customer_id)

    async def get_past_meetings(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """過去の会話を取得（Agent用）"""
        # メモを取得
        memo_result = (
            self.client.table("memos")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        # 議事録カテゴリのナレッジも取得
        knowledge_result = (
            self.client.table("knowledge")
            .select("*")
            .eq("customer_id", customer_id)
            .eq("category", "minutes")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        meetings = []
        for m in (memo_result.data or []):
            meetings.append({
                "id": m.get("id"),
                "title": f"会話メモ ({m.get('created_at', '')[:10]})",
                "content": m.get("summary", ""),
                "created_at": m.get("created_at", "")
            })
        for k in (knowledge_result.data or []):
            meetings.append({
                "id": k.get("id"),
                "title": k.get("title", ""),
                "content": k.get("content", ""),
                "created_at": k.get("created_at", "")
            })

        meetings.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return meetings[:limit]

    async def get_needs(self, customer_id: str) -> List[Dict]:
        """顧客の課題・ニーズを取得（Agent用）"""
        result = (
            self.client.table("knowledge")
            .select("*")
            .eq("customer_id", customer_id)
            .in_("category", ["basic_info", "needs"])
            .execute()
        )
        return result.data or []
