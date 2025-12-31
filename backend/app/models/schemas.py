"""
Pydantic schemas for HireMate API
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CustomerBase(BaseModel):
    """顧客基本情報"""
    name: str
    description: Optional[str] = None


class CustomerCreate(CustomerBase):
    """顧客作成"""
    pass


class Customer(CustomerBase):
    """顧客レスポンス"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBase(BaseModel):
    """知識ベース基本情報"""
    title: str
    content: str
    category: str  # "basic_info", "past_meeting", "needs", "notes"


class KnowledgeCreate(KnowledgeBase):
    """知識作成"""
    customer_id: str


class Knowledge(KnowledgeBase):
    """知識レスポンス"""
    id: str
    customer_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdviceRequest(BaseModel):
    """アドバイスリクエスト"""
    customer_id: Optional[str] = None  # 顧客ID（未選択の場合はNone）
    transcript: str  # 直近の会話文字起こし
    system_prompt: Optional[str] = None  # カスタムプロンプト


class AdviceResponse(BaseModel):
    """アドバイスレスポンス"""
    advice: str
    tools_used: List[str] = []
    context_used: List[str] = []


class TranscriptSave(BaseModel):
    """文字起こし保存"""
    customer_id: str
    content: str
    meeting_date: Optional[datetime] = None
