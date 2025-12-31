"""
TONARI for M&A - セッションAPI
リアルタイム面談セッション管理
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..models.mna_schemas import (
    ExtractionField,
    ExtractionUpdate,
    Hypothesis,
    InfoLayer,
    SessionCreate,
    SessionState,
    SessionSummary,
    Suggestion,
    Utterance,
    UtteranceCreate,
    WSMessage,
    WSMessageType,
)
from ..services.mna_extraction import MnAExtractionService
from ..services.mna_suggestion import MnASuggestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mna/sessions", tags=["M&A Sessions"])

# インメモリセッションストア（本番ではRedis等に置き換え）
active_sessions: dict[str, SessionState] = {}

# サービスインスタンス
extraction_service = MnAExtractionService()
suggestion_service = MnASuggestionService()


# ========================
# REST API
# ========================


class CreateSessionResponse(BaseModel):
    """セッション作成レスポンス."""

    session_id: str
    project_id: str
    status: str


@router.post("", response_model=CreateSessionResponse)
async def create_session(data: SessionCreate) -> CreateSessionResponse:
    """新規セッションを作成する.

    Args:
        data: セッション作成データ

    Returns:
        CreateSessionResponse: 作成されたセッション情報
    """
    session_id = str(uuid4())
    session = SessionState(
        id=session_id,
        project_id=data.project_id,
        status="active",
        started_at=datetime.now(),
    )
    active_sessions[session_id] = session

    logger.info(f"Session created: {session_id} for project {data.project_id}")

    return CreateSessionResponse(
        session_id=session_id,
        project_id=data.project_id,
        status="active",
    )


@router.get("/{session_id}")
async def get_session(session_id: str) -> SessionState:
    """セッション情報を取得する.

    Args:
        session_id: セッションID

    Returns:
        SessionState: セッション状態

    Raises:
        HTTPException: セッションが見つからない場合
    """
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/end")
async def end_session(session_id: str) -> SessionSummary:
    """セッションを終了する.

    Args:
        session_id: セッションID

    Returns:
        SessionSummary: セッションサマリー

    Raises:
        HTTPException: セッションが見つからない場合
    """
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    session.ended_at = datetime.now()

    duration = None
    if session.ended_at and session.started_at:
        duration = int((session.ended_at - session.started_at).total_seconds())

    logger.info(f"Session ended: {session_id}")

    return SessionSummary(
        id=session_id,
        project_id=session.project_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=duration,
        extraction_count=len(session.extractions),
        utterance_count=len(session.utterances),
    )


@router.get("/{session_id}/extractions")
async def get_extractions(session_id: str) -> dict:
    """抽出情報を取得する.

    Args:
        session_id: セッションID

    Returns:
        dict: 抽出情報と進捗
    """
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    progress = extraction_service.calculate_extraction_progress(session.extractions)
    missing = extraction_service.get_missing_fields(
        session.extractions, session.current_layer
    )

    return {
        "extractions": session.extractions,
        "progress": progress,
        "missing_fields": missing[:10],
    }


@router.put("/{session_id}/extractions/{field_key}")
async def update_extraction(
    session_id: str,
    field_key: str,
    value: str,
) -> ExtractionField:
    """抽出情報を手動更新する.

    Args:
        session_id: セッションID
        field_key: フィールドキー（category.field形式）
        value: 更新値

    Returns:
        ExtractionField: 更新後のフィールド
    """
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if field_key in session.extractions:
        session.extractions[field_key].value = value
        session.extractions[field_key].confidence = 1.0  # 手動入力は確信度1
    else:
        # 新規フィールドを作成
        parts = field_key.split(".")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid field key format")

        from ..models.mna_schemas import ExtractionCategory

        try:
            category = ExtractionCategory(parts[0])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category")

        session.extractions[field_key] = ExtractionField(
            category=category,
            field=parts[1],
            value=value,
            confidence=1.0,
        )

    return session.extractions[field_key]


# ========================
# WebSocket
# ========================


class SessionWebSocketManager:
    """セッションWebSocket管理.

    Attributes:
        connections: アクティブな接続
        text_buffer: テキストバッファ
    """

    def __init__(self) -> None:
        """マネージャーを初期化する."""
        self.connections: dict[str, list[WebSocket]] = {}
        self.text_buffer: dict[str, list[Utterance]] = {}
        self.buffer_duration: float = 10.0  # 10秒バッファ
        self.min_utterances: int = 3

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """WebSocket接続を登録する."""
        await websocket.accept()
        if session_id not in self.connections:
            self.connections[session_id] = []
            self.text_buffer[session_id] = []
        self.connections[session_id].append(websocket)
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        """WebSocket接続を解除する."""
        if session_id in self.connections:
            self.connections[session_id].remove(websocket)
            if not self.connections[session_id]:
                del self.connections[session_id]
                del self.text_buffer[session_id]
        logger.info(f"WebSocket disconnected: {session_id}")

    async def broadcast(self, session_id: str, message: WSMessage) -> None:
        """セッションの全接続にメッセージを送信する."""
        if session_id not in self.connections:
            return

        message_json = message.model_dump_json()
        disconnected = []

        for ws in self.connections[session_id]:
            try:
                await ws.send_text(message_json)
            except Exception:
                disconnected.append(ws)

        # 切断された接続を削除
        for ws in disconnected:
            self.disconnect(session_id, ws)

    async def handle_transcript(
        self,
        session_id: str,
        text: str,
        speaker: str,
        is_final: bool,
    ) -> None:
        """文字起こし結果を処理する.

        Args:
            session_id: セッションID
            text: テキスト
            speaker: 話者
            is_final: 確定テキストかどうか
        """
        session = active_sessions.get(session_id)
        if not session:
            return

        # 発話を作成・保存
        utterance = Utterance(
            id=str(uuid4()),
            session_id=session_id,
            timestamp=datetime.now(),
            speaker=speaker,
            text=text,
        )

        if is_final:
            session.utterances.append(utterance)
            self.text_buffer[session_id].append(utterance)

            # リフレーミング検出
            reframe = suggestion_service.detect_reframing_opportunity(utterance)
            if reframe:
                await self.broadcast(
                    session_id,
                    WSMessage(
                        type=WSMessageType.REFRAMING,
                        data=reframe.model_dump(),
                    ),
                )

        # クライアントに文字起こしを送信
        await self.broadcast(
            session_id,
            WSMessage(
                type=WSMessageType.TRANSCRIPT,
                data={
                    "utterance": utterance.model_dump(),
                    "is_final": is_final,
                },
            ),
        )

        # バッファがたまったら抽出・サジェスト生成
        if is_final and len(self.text_buffer[session_id]) >= self.min_utterances:
            await self._process_buffer(session_id)

    async def _process_buffer(self, session_id: str) -> None:
        """バッファを処理して抽出・サジェストを生成する."""
        session = active_sessions.get(session_id)
        buffer = self.text_buffer.get(session_id, [])

        if not session or not buffer:
            return

        # バッファをクリア
        self.text_buffer[session_id] = []

        # 並列で抽出・サジェスト生成
        extraction_task = extraction_service.extract_from_utterances(
            session_id,
            buffer,
            session.extractions,
        )

        missing_fields = extraction_service.get_missing_fields(
            session.extractions, session.current_layer
        )

        suggestion_task = suggestion_service.generate_suggestions(
            session_id,
            session.utterances[-10:],
            session.extractions,
            missing_fields,
            session.hypotheses,
        )

        extraction_result, suggestions = await asyncio.gather(
            extraction_task,
            suggestion_task,
            return_exceptions=True,
        )

        # 抽出結果を反映・送信
        if not isinstance(extraction_result, Exception):
            for field in extraction_result.fields:
                field_key = f"{field.category.value}.{field.field}"
                session.extractions[field_key] = field

                await self.broadcast(
                    session_id,
                    WSMessage(
                        type=WSMessageType.EXTRACTION_UPDATE,
                        data={
                            "field_key": field_key,
                            "field": field.model_dump(),
                        },
                    ),
                )

        # サジェストを送信
        if not isinstance(suggestions, Exception):
            for suggestion in suggestions:
                await self.broadcast(
                    session_id,
                    WSMessage(
                        type=WSMessageType.SUGGESTION,
                        data=suggestion.model_dump(),
                    ),
                )


ws_manager = SessionWebSocketManager()


@router.websocket("/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """セッションWebSocketエンドポイント.

    メッセージタイプ:
    - audio_chunk: 音声データ
    - pin_utterance: 発話をピン留め
    - dismiss_suggestion: サジェストを非表示
    - use_suggestion: サジェストを使用
    - update_extraction: 抽出情報を更新
    """
    session = active_sessions.get(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await ws_manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "transcript":
                # 文字起こし結果（Deepgramからのコールバック想定）
                await ws_manager.handle_transcript(
                    session_id,
                    message.get("text", ""),
                    message.get("speaker", "customer"),
                    message.get("is_final", False),
                )

            elif msg_type == "pin_utterance":
                # 発話をピン留め
                utterance_id = message.get("utterance_id")
                note = message.get("note", "")
                for u in session.utterances:
                    if u.id == utterance_id:
                        u.is_pinned = True
                        u.pin_note = note
                        break

            elif msg_type == "update_extraction":
                # 抽出情報を手動更新
                field_key = message.get("field_key")
                value = message.get("value")
                if field_key and value is not None:
                    await update_extraction(session_id, field_key, value)

            elif msg_type == "set_layer":
                # 現在のレイヤーを設定
                layer = message.get("layer")
                try:
                    session.current_layer = InfoLayer(layer)
                except ValueError:
                    pass

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(session_id, websocket)
