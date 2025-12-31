"""
マッチング API
ヒアリング情報をもとに求人候補を提案する
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..core import verify_supabase_token

router = APIRouter(prefix="/api", tags=["matching"])


# ===== Request/Response Models =====
class CheckedItem(BaseModel):
    id: str
    value: str


class MatchingRequest(BaseModel):
    transcript: str
    checked_items: List[CheckedItem] = []


class JobCandidate(BaseModel):
    id: int
    company: str
    title: str
    location: str
    salary: str
    tags: List[str]
    match_score: Optional[int] = None


class MatchingResponse(BaseModel):
    candidates: List[JobCandidate]
    total_count: int
    status: str  # "collecting" | "ready" | "narrowing"


# ===== ダミー求人データ（エンジニア向け） =====
DUMMY_JOBS = [
    # フロントエンド系
    JobCandidate(id=1, company="株式会社テックイノベーション", title="フロントエンドエンジニア", location="上野", salary="500-700万", tags=["React", "TypeScript", "リモート可"]),
    JobCandidate(id=2, company="UIデザインテック", title="フロントエンドリード", location="渋谷", salary="650-850万", tags=["Vue.js", "Nuxt", "デザインシステム"]),
    # バックエンド系
    JobCandidate(id=3, company="合同会社クラウドサービス", title="バックエンドエンジニア", location="秋葉原", salary="550-750万", tags=["Python", "AWS", "フレックス"]),
    JobCandidate(id=4, company="フィンテックスタートアップ", title="Goエンジニア", location="六本木", salary="600-900万", tags=["Go", "Kubernetes", "マイクロサービス"]),
    # フルスタック系
    JobCandidate(id=5, company="グローバルIT株式会社", title="フルスタックエンジニア", location="御徒町", salary="600-800万", tags=["Node.js", "React", "自社開発"]),
    JobCandidate(id=6, company="スタートアップX", title="Webエンジニア", location="浅草", salary="450-600万", tags=["Next.js", "Prisma", "ベンチャー"]),
    # AI/ML系
    JobCandidate(id=7, company="AIテクノロジー株式会社", title="機械学習エンジニア", location="御茶ノ水", salary="650-900万", tags=["Python", "PyTorch", "LLM"]),
    JobCandidate(id=8, company="データサイエンス社", title="MLOpsエンジニア", location="品川", salary="700-1000万", tags=["MLflow", "Kubeflow", "AWS SageMaker"]),
    JobCandidate(id=9, company="生成AIラボ", title="LLMエンジニア", location="渋谷", salary="800-1200万", tags=["OpenAI", "LangChain", "RAG"]),
    # インフラ/SRE系
    JobCandidate(id=10, company="クラウドインフラ株式会社", title="SREエンジニア", location="新宿", salary="600-850万", tags=["Terraform", "AWS", "監視設計"]),
    JobCandidate(id=11, company="大手ECプラットフォーム", title="プラットフォームエンジニア", location="目黒", salary="700-950万", tags=["Kubernetes", "ArgoCD", "大規模"]),
    # モバイル系
    JobCandidate(id=12, company="モバイルアプリ開発", title="iOSエンジニア", location="神田", salary="550-700万", tags=["Swift", "SwiftUI", "アジャイル"]),
    JobCandidate(id=13, company="ゲーム開発スタジオ", title="Androidエンジニア", location="池袋", salary="500-700万", tags=["Kotlin", "Jetpack Compose", "ゲーム"]),
    # セキュリティ系
    JobCandidate(id=14, company="セキュリティベンチャー", title="セキュリティエンジニア", location="大手町", salary="650-900万", tags=["脆弱性診断", "SIEM", "SOC"]),
    # データエンジニア系
    JobCandidate(id=15, company="ビッグデータ分析社", title="データエンジニア", location="丸の内", salary="600-850万", tags=["Spark", "Snowflake", "dbt"]),
]

# マッチングに必要な項目（年収・勤務地・職歴の3項目）
REQUIRED_ITEMS_COUNT = 3
REQUIRED_ITEM_IDS = {"salary", "location", "recentWork"}


@router.post("/matching", response_model=MatchingResponse)
async def get_matching_candidates(
    request: MatchingRequest,
    user=Depends(verify_supabase_token)
):
    """
    ヒアリング情報をもとに求人候補を返す
    - 必要項目が5つ未満: status="collecting", candidates=[]
    - 5つ以上: status="ready", candidates=[ダミーデータ]
    """
    # チェック済み項目のIDセットを取得
    checked_ids = {item.id for item in request.checked_items}
    
    # 必須項目のうちチェック済みの数
    matched_required = checked_ids & REQUIRED_ITEM_IDS
    checked_count = len(matched_required)
    
    if checked_count < REQUIRED_ITEMS_COUNT:
        # まだ情報収集中
        return MatchingResponse(
            candidates=[],
            total_count=0,
            status="collecting"
        )
    
    # 5項目以上揃ったら候補を返す
    # 実際のマッチングロジックはここに実装（今はダミー）
    candidates = filter_candidates(request.checked_items)
    
    return MatchingResponse(
        candidates=candidates,
        total_count=len(candidates),
        status="ready"
    )


def filter_candidates(checked_items: List[CheckedItem]) -> List[JobCandidate]:
    """
    チェック済み項目をもとに候補をフィルタリング（ダミー実装）
    実際にはDBクエリやマッチングロジックを実装
    """
    # 今はダミーデータをそのまま返す
    # 将来的にはlocation, salary, jobTypeでフィルタリング
    return DUMMY_JOBS
