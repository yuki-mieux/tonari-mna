"""
TONARI for M&A - プロジェクトAPI
案件管理エンドポイント
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.mna_schemas import (
    Output,
    OutputCreate,
    OutputType,
    Project,
    ProjectCreate,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mna/projects", tags=["M&A Projects"])

# インメモリストア（本番ではSupabase）
projects: dict[str, Project] = {}
outputs: dict[str, Output] = {}


# ========================
# プロジェクト CRUD
# ========================


class ProjectListResponse(BaseModel):
    """プロジェクト一覧レスポンス."""

    projects: list[Project]
    total: int


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> ProjectListResponse:
    """プロジェクト一覧を取得する.

    Args:
        status: ステータスフィルタ
        limit: 取得件数
        offset: オフセット

    Returns:
        ProjectListResponse: プロジェクト一覧
    """
    all_projects = list(projects.values())

    if status:
        all_projects = [p for p in all_projects if p.status == status]

    # 更新日時でソート
    all_projects.sort(key=lambda p: p.updated_at, reverse=True)

    total = len(all_projects)
    paginated = all_projects[offset : offset + limit]

    return ProjectListResponse(projects=paginated, total=total)


@router.post("", response_model=Project)
async def create_project(data: ProjectCreate) -> Project:
    """プロジェクトを作成する.

    Args:
        data: プロジェクト作成データ

    Returns:
        Project: 作成されたプロジェクト
    """
    project_id = str(uuid4())
    now = datetime.now()

    project = Project(
        id=project_id,
        user_id="demo-user",  # TODO: 認証実装後に実ユーザーIDに
        name=data.name,
        company_name=data.company_name,
        status="active",
        created_at=now,
        updated_at=now,
    )
    projects[project_id] = project

    logger.info(f"Project created: {project_id} - {data.name}")
    return project


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """プロジェクトを取得する.

    Args:
        project_id: プロジェクトID

    Returns:
        Project: プロジェクト

    Raises:
        HTTPException: プロジェクトが見つからない場合
    """
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, data: ProjectUpdate) -> Project:
    """プロジェクトを更新する.

    Args:
        project_id: プロジェクトID
        data: 更新データ

    Returns:
        Project: 更新されたプロジェクト
    """
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.name is not None:
        project.name = data.name
    if data.company_name is not None:
        project.company_name = data.company_name
    if data.status is not None:
        project.status = data.status

    project.updated_at = datetime.now()
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str) -> dict:
    """プロジェクトを削除する.

    Args:
        project_id: プロジェクトID

    Returns:
        dict: 削除結果
    """
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    del projects[project_id]

    # 関連する成果物も削除
    to_delete = [oid for oid, o in outputs.items() if o.project_id == project_id]
    for oid in to_delete:
        del outputs[oid]

    logger.info(f"Project deleted: {project_id}")
    return {"message": "Project deleted"}


# ========================
# 成果物管理
# ========================


class OutputListResponse(BaseModel):
    """成果物一覧レスポンス."""

    outputs: list[Output]


@router.get("/{project_id}/outputs", response_model=OutputListResponse)
async def list_outputs(project_id: str) -> OutputListResponse:
    """プロジェクトの成果物一覧を取得する.

    Args:
        project_id: プロジェクトID

    Returns:
        OutputListResponse: 成果物一覧
    """
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    project_outputs = [o for o in outputs.values() if o.project_id == project_id]
    project_outputs.sort(key=lambda o: o.created_at, reverse=True)

    return OutputListResponse(outputs=project_outputs)


@router.post("/{project_id}/outputs", response_model=Output)
async def create_output(project_id: str, data: OutputCreate) -> Output:
    """成果物を作成する.

    Args:
        project_id: プロジェクトID
        data: 成果物作成データ

    Returns:
        Output: 作成された成果物
    """
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    output_id = str(uuid4())

    # TODO: 実際の成果物生成ロジック
    content = {}
    if data.output_type == OutputType.NON_NAME:
        content = _generate_non_name_content(project_id)
    elif data.output_type == OutputType.IM:
        content = _generate_im_content(project_id)

    output = Output(
        id=output_id,
        project_id=project_id,
        output_type=data.output_type,
        content=content,
        created_at=datetime.now(),
    )
    outputs[output_id] = output

    logger.info(f"Output created: {output_id} ({data.output_type.value})")
    return output


@router.get("/{project_id}/outputs/{output_id}", response_model=Output)
async def get_output(project_id: str, output_id: str) -> Output:
    """成果物を取得する.

    Args:
        project_id: プロジェクトID
        output_id: 成果物ID

    Returns:
        Output: 成果物
    """
    output = outputs.get(output_id)
    if not output or output.project_id != project_id:
        raise HTTPException(status_code=404, detail="Output not found")
    return output


# ========================
# 成果物生成ヘルパー
# ========================


def _generate_non_name_content(project_id: str) -> dict:
    """ノンネームコンテンツを生成する.

    Args:
        project_id: プロジェクトID

    Returns:
        dict: ノンネームコンテンツ
    """
    # TODO: セッションから抽出情報を取得して生成
    return {
        "title": "譲渡案件のご紹介",
        "industry": "（業種）",
        "region": "（地域）",
        "revenue_range": "（売上規模）",
        "profit_range": "（利益規模）",
        "transfer_scheme": "（譲渡スキーム）",
        "transfer_reason": "（譲渡理由）",
        "appeal_points": [],
        "generated_at": datetime.now().isoformat(),
    }


def _generate_im_content(project_id: str) -> dict:
    """IMコンテンツを生成する.

    Args:
        project_id: プロジェクトID

    Returns:
        dict: IMコンテンツ
    """
    # TODO: セッションから抽出情報を取得して生成
    return {
        "version": "1.0",
        "sections": [
            {
                "title": "会社概要",
                "content": {},
            },
            {
                "title": "事業内容",
                "content": {},
            },
            {
                "title": "財務ハイライト",
                "content": {},
            },
            {
                "title": "譲渡条件",
                "content": {},
            },
        ],
        "generated_at": datetime.now().isoformat(),
    }
