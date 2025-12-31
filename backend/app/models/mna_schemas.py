"""
TONARI for M&A - Pydantic スキーマ定義
M&Aヒアリング情報抽出・分析のためのデータモデル
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ExtractionCategory(str, Enum):
    """抽出カテゴリ."""

    BASIC_INFO = "basic_info"
    FINANCIAL = "financial"
    BUSINESS = "business"
    ORGANIZATION = "organization"
    TRANSFER = "transfer"


class InfoLayer(str, Enum):
    """水野メソッド: 4層モデル."""

    SURFACE = "surface"  # 表層情報
    STRUCTURE = "structure"  # 構造情報
    ESSENCE = "essence"  # 本質情報
    EXIT = "exit"  # 出口情報


class SuggestionType(str, Enum):
    """サジェストタイプ."""

    QUESTION = "question"  # 質問提案
    REFRAMING = "reframing"  # リフレーミング提案


class AnalysisType(str, Enum):
    """分析タイプ."""

    STRUCTURE = "structure"  # 事業構造分析
    BUYER_PROFILE = "buyer_profile"  # 買い手像
    RISK = "risk"  # リスク分析
    HYPOTHESIS = "hypothesis"  # 仮説


# ========================
# 発話関連
# ========================


class Utterance(BaseModel):
    """発話データ."""

    id: str
    session_id: str
    timestamp: datetime
    speaker: str  # "user" or "customer"
    text: str
    is_important: bool = False
    is_pinned: bool = False
    pin_note: Optional[str] = None


class UtteranceCreate(BaseModel):
    """発話作成."""

    session_id: str
    speaker: str
    text: str


# ========================
# 抽出情報関連
# ========================


class ExtractionField(BaseModel):
    """抽出フィールド."""

    category: ExtractionCategory
    field: str
    value: Optional[str] = None
    confidence: float = 0.0
    source_utterance_id: Optional[str] = None
    layer: InfoLayer = InfoLayer.SURFACE


class ExtractionResult(BaseModel):
    """抽出結果."""

    session_id: str
    fields: list[ExtractionField]
    timestamp: datetime = Field(default_factory=datetime.now)


class ExtractionUpdate(BaseModel):
    """抽出情報更新（WebSocket経由）."""

    type: str = "extraction_update"
    session_id: str
    field: ExtractionField


# ========================
# IM抽出項目定義（約35項目）
# ========================


IM_EXTRACTION_FIELDS: dict[ExtractionCategory, list[dict]] = {
    ExtractionCategory.BASIC_INFO: [
        {"field": "company_name", "label": "会社名", "layer": InfoLayer.SURFACE},
        {"field": "location", "label": "所在地", "layer": InfoLayer.SURFACE},
        {"field": "established_year", "label": "設立年", "layer": InfoLayer.SURFACE},
        {"field": "capital", "label": "資本金", "layer": InfoLayer.SURFACE},
        {"field": "employee_count", "label": "従業員数", "layer": InfoLayer.SURFACE},
        {"field": "representative", "label": "代表者", "layer": InfoLayer.SURFACE},
        {"field": "representative_profile", "label": "代表者プロフィール", "layer": InfoLayer.STRUCTURE},
        {"field": "history", "label": "沿革", "layer": InfoLayer.STRUCTURE},
    ],
    ExtractionCategory.FINANCIAL: [
        {"field": "revenue_latest", "label": "売上高（直近）", "layer": InfoLayer.SURFACE},
        {"field": "revenue_trend", "label": "売上高推移（3-5期）", "layer": InfoLayer.STRUCTURE},
        {"field": "operating_profit", "label": "営業利益", "layer": InfoLayer.SURFACE},
        {"field": "ordinary_profit", "label": "経常利益", "layer": InfoLayer.SURFACE},
        {"field": "net_assets", "label": "純資産", "layer": InfoLayer.SURFACE},
        {"field": "adjusted_net_assets", "label": "調整後純資産", "layer": InfoLayer.STRUCTURE},
        {"field": "debt", "label": "借入金", "layer": InfoLayer.SURFACE},
        {"field": "main_kpis", "label": "主要KPI", "layer": InfoLayer.STRUCTURE},
    ],
    ExtractionCategory.BUSINESS: [
        {"field": "business_description", "label": "事業内容", "layer": InfoLayer.SURFACE},
        {"field": "main_products_services", "label": "主要サービス/製品", "layer": InfoLayer.SURFACE},
        {"field": "main_clients", "label": "主要取引先", "layer": InfoLayer.STRUCTURE},
        {"field": "client_composition", "label": "顧客構成", "layer": InfoLayer.STRUCTURE},
        {"field": "competitive_advantage", "label": "競合優位性", "layer": InfoLayer.ESSENCE},
        {"field": "strengths", "label": "強み", "layer": InfoLayer.ESSENCE},
        {"field": "weaknesses", "label": "弱み", "layer": InfoLayer.STRUCTURE},
        {"field": "industry_trends", "label": "業界動向", "layer": InfoLayer.STRUCTURE},
        {"field": "market_position", "label": "市場ポジション", "layer": InfoLayer.STRUCTURE},
    ],
    ExtractionCategory.ORGANIZATION: [
        {"field": "org_structure", "label": "組織体制", "layer": InfoLayer.STRUCTURE},
        {"field": "key_persons", "label": "キーパーソン", "layer": InfoLayer.ESSENCE},
        {"field": "successor_status", "label": "後継者有無", "layer": InfoLayer.ESSENCE},
        {"field": "employee_treatment", "label": "従業員の処遇", "layer": InfoLayer.EXIT},
        {"field": "executive_retention", "label": "役員の残留意向", "layer": InfoLayer.EXIT},
    ],
    ExtractionCategory.TRANSFER: [
        {"field": "transfer_scheme", "label": "譲渡スキーム", "layer": InfoLayer.EXIT},
        {"field": "transfer_reason", "label": "譲渡理由", "layer": InfoLayer.ESSENCE},
        {"field": "desired_price", "label": "希望価格", "layer": InfoLayer.EXIT},
        {"field": "desired_timing", "label": "希望時期", "layer": InfoLayer.EXIT},
        {"field": "desired_conditions", "label": "希望条件", "layer": InfoLayer.EXIT},
        {"field": "dd_notes", "label": "DD留意事項", "layer": InfoLayer.EXIT},
    ],
}


# ========================
# 分析関連
# ========================


class StructureAnalysis(BaseModel):
    """事業構造分析."""

    profit_source: str  # なぜ利益が出ているか
    competitive_moat: str  # 競合優位性
    risk_factors: list[str]  # リスク要因
    hidden_value: str  # 隠れた価値


class BuyerProfile(BaseModel):
    """買い手像."""

    ideal_buyer_type: str  # 理想の買い手タイプ
    synergy_points: list[str]  # シナジーポイント
    deal_structure_suggestion: str  # 取引構造提案


class Hypothesis(BaseModel):
    """仮説."""

    id: str
    content: str
    confidence: float
    supporting_evidence: list[str]
    created_at: datetime


# ========================
# サジェスト関連
# ========================


class Suggestion(BaseModel):
    """サジェスト."""

    id: str
    session_id: str
    suggestion_type: SuggestionType
    content: str
    reason: str
    layer: InfoLayer
    priority: float  # 0-1
    target_field: Optional[str] = None  # 対象抽出フィールド
    was_used: bool = False
    was_dismissed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class SuggestionCreate(BaseModel):
    """サジェスト作成."""

    session_id: str
    suggestion_type: SuggestionType
    content: str
    reason: str
    layer: InfoLayer
    priority: float
    target_field: Optional[str] = None


class ReframingSuggestion(BaseModel):
    """リフレーミング提案."""

    original_text: str
    negative_word: str
    positive_interpretation: str
    follow_up_question: str
    reframe_conditions: str


# ========================
# セッション関連
# ========================


class SessionState(BaseModel):
    """セッション状態."""

    id: str
    project_id: str
    status: str  # "active" or "completed"
    started_at: datetime
    ended_at: Optional[datetime] = None
    utterances: list[Utterance] = []
    extractions: dict[str, ExtractionField] = {}
    hypotheses: list[Hypothesis] = []
    current_layer: InfoLayer = InfoLayer.SURFACE


class SessionCreate(BaseModel):
    """セッション作成."""

    project_id: str


class SessionSummary(BaseModel):
    """セッションサマリー."""

    id: str
    project_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    extraction_count: int
    utterance_count: int


# ========================
# プロジェクト関連
# ========================


class Project(BaseModel):
    """プロジェクト."""

    id: str
    user_id: str
    name: str
    company_name: Optional[str] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    """プロジェクト作成."""

    name: str
    company_name: Optional[str] = None


class ProjectUpdate(BaseModel):
    """プロジェクト更新."""

    name: Optional[str] = None
    company_name: Optional[str] = None
    status: Optional[str] = None


# ========================
# 成果物関連
# ========================


class OutputType(str, Enum):
    """成果物タイプ."""

    NON_NAME = "non_name"  # ノンネーム
    IM = "im"  # IM


class Output(BaseModel):
    """成果物."""

    id: str
    project_id: str
    output_type: OutputType
    content: dict  # 構造化されたコンテンツ
    file_url: Optional[str] = None
    created_at: datetime


class OutputCreate(BaseModel):
    """成果物作成."""

    project_id: str
    output_type: OutputType


# ========================
# WebSocketメッセージ
# ========================


class WSMessageType(str, Enum):
    """WebSocketメッセージタイプ."""

    # クライアント → サーバー
    AUDIO_CHUNK = "audio_chunk"
    PIN_UTTERANCE = "pin_utterance"
    DISMISS_SUGGESTION = "dismiss_suggestion"
    USE_SUGGESTION = "use_suggestion"
    UPDATE_EXTRACTION = "update_extraction"

    # サーバー → クライアント
    TRANSCRIPT = "transcript"
    EXTRACTION_UPDATE = "extraction_update"
    ANALYSIS_UPDATE = "analysis_update"
    SUGGESTION = "suggestion"
    REFRAMING = "reframing"
    ERROR = "error"
    SESSION_STATUS = "session_status"


class WSMessage(BaseModel):
    """WebSocketメッセージ."""

    type: WSMessageType
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)
