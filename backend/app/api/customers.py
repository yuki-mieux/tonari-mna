"""
顧客管理 API
"""
import io
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List

from ..models.schemas import Customer, CustomerCreate, Knowledge, KnowledgeCreate
from ..services.knowledge import KnowledgeManager
from ..core import verify_supabase_token


ALLOWED_EXTENSIONS = {'.md', '.txt', '.pdf'}

router = APIRouter(
    prefix="/api/customers",
    tags=["customers"],
    dependencies=[Depends(verify_supabase_token)]
)
knowledge_manager = KnowledgeManager()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """PDFからテキストを抽出してMarkdown形式に変換"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        md_parts = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text:
                md_parts.append(f"## ページ {i}\n\n{text.strip()}")
        return "\n\n---\n\n".join(md_parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF解析エラー: {str(e)}")


# ===== 顧客 CRUD =====

@router.get("/", response_model=List[Customer])
async def list_customers():
    """顧客一覧を取得"""
    return await knowledge_manager.list_customers()


@router.post("/", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    """顧客を作成"""
    return await knowledge_manager.create_customer(
        name=customer.name,
        description=customer.description
    )


@router.get("/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """顧客を取得"""
    customer = await knowledge_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}")
async def delete_customer(customer_id: str):
    """顧客を削除"""
    customer = await knowledge_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await knowledge_manager.delete_customer(customer_id)
    return {"status": "deleted", "id": customer_id}


# ===== ナレッジ管理 =====

@router.post("/{customer_id}/knowledge", response_model=Knowledge)
async def add_knowledge(customer_id: str, knowledge: KnowledgeCreate):
    """顧客にナレッジを追加"""
    customer = await knowledge_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return await knowledge_manager.add_knowledge(
        customer_id=customer_id,
        title=knowledge.title,
        content=knowledge.content,
        category=knowledge.category
    )


@router.get("/{customer_id}/knowledge")
async def list_knowledge(customer_id: str):
    """顧客のナレッジ一覧を取得"""
    customer = await knowledge_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return await knowledge_manager.list_knowledge(customer_id)


@router.delete("/{customer_id}/knowledge/{knowledge_id}")
async def delete_knowledge(customer_id: str, knowledge_id: str):
    """ナレッジを削除"""
    customer = await knowledge_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await knowledge_manager.delete_knowledge(knowledge_id)
    return {"status": "deleted", "id": knowledge_id}


# ===== ファイルアップロード =====

@router.post("/{customer_id}/upload")
async def upload_file(
    customer_id: str,
    file: UploadFile = File(...),
    category: str = Form(default="basic_info")
):
    """ファイルをアップロードしてナレッジとして保存（MD, TXT, PDF対応）"""
    customer = await knowledge_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    content_bytes = await file.read()
    filename = file.filename or "untitled"
    _, ext = os.path.splitext(filename.lower())

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"サポートされていないファイル形式です。対応形式: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if ext == ".pdf":
        content = extract_text_from_pdf(content_bytes)
        title = filename.rsplit(".", 1)[0]
    else:
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="UTF-8エンコーディングが必要です")
        title = filename.rsplit(".", 1)[0] if "." in filename else filename

    knowledge = await knowledge_manager.add_knowledge(
        customer_id=customer_id,
        title=title,
        content=content,
        category=category
    )

    return {
        "status": "success",
        "filename": filename,
        "converted_to_markdown": ext == ".pdf",
        "content_length": len(content),
        "knowledge": knowledge
    }


# ===== 会話履歴 =====

@router.get("/{customer_id}/meetings")
async def list_meetings(customer_id: str):
    """顧客の会話履歴を取得"""
    return await knowledge_manager.get_past_meetings(customer_id, limit=20)


@router.get("/{customer_id}/memos")
async def list_memos(customer_id: str):
    """顧客のメモ一覧を取得"""
    customer = await knowledge_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return await knowledge_manager.list_memos(customer_id)
