# TONARI for M&A - 技術アーキテクチャ設計書

## 1. システム概要

### 1.1 アーキテクチャ概念図

```
┌─────────────────────────────────────────────────────────────────┐
│                         クライアント                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Vanilla HTML/CSS/JS                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │ 会話UI   │  │ 情報UI   │  │ 提案UI   │              │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │   │
│  │       │             │             │                      │   │
│  │       └─────────────┼─────────────┘                      │   │
│  │                     │                                     │   │
│  │              ┌──────┴──────┐                             │   │
│  │              │ WebSocket   │                             │   │
│  │              │ Manager     │                             │   │
│  │              └──────┬──────┘                             │   │
│  └─────────────────────┼───────────────────────────────────┘   │
└────────────────────────┼───────────────────────────────────────┘
                         │
                         │ WSS
                         │
┌────────────────────────┼───────────────────────────────────────┐
│                        │            バックエンド               │
│  ┌─────────────────────┴─────────────────────────────────┐    │
│  │                    FastAPI Server                      │    │
│  │  ┌──────────────────────────────────────────────────┐ │    │
│  │  │              WebSocket Handler                    │ │    │
│  │  └──────────────────────┬───────────────────────────┘ │    │
│  │                         │                              │    │
│  │  ┌──────────┬───────────┼───────────┬──────────────┐  │    │
│  │  │          │           │           │              │  │    │
│  │  ▼          ▼           ▼           ▼              │  │    │
│  │ ┌────┐  ┌────────┐  ┌────────┐  ┌────────┐        │  │    │
│  │ │STT │  │Extract │  │Analyze │  │Suggest │        │  │    │
│  │ │Svc │  │Engine  │  │Engine  │  │Engine  │        │  │    │
│  │ └──┬─┘  └───┬────┘  └───┬────┘  └───┬────┘        │  │    │
│  │    │        │           │           │              │  │    │
│  └────┼────────┼───────────┼───────────┼──────────────┘  │    │
│       │        │           │           │                  │    │
│       │        └───────────┼───────────┘                  │    │
│       │                    │                              │    │
│       ▼                    ▼                              │    │
│  ┌─────────┐         ┌──────────┐                        │    │
│  │Deepgram │         │Claude API│                        │    │
│  │   API   │         │          │                        │    │
│  └─────────┘         └──────────┘                        │    │
│                                                           │    │
│  ┌───────────────────────────────────────────────────┐   │    │
│  │                    Supabase                        │   │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │    │
│  │  │  Auth   │  │PostgreSQL│  │ Storage │           │   │    │
│  │  └─────────┘  └─────────┘  └─────────┘           │   │    │
│  └───────────────────────────────────────────────────┘   │    │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 技術スタック

| レイヤー | 技術 | 選定理由 |
|----------|------|----------|
| フロントエンド | Vanilla HTML/CSS/JS | シンプル、依存少、高速 |
| バックエンド | FastAPI (Python) | 非同期対応、WebSocket、型安全 |
| リアルタイムSTT | Deepgram API | 日本語対応、低遅延、WebSocket |
| AI推論 | Claude API (claude-sonnet-4-20250514) | 高精度、日本語、構造化出力 |
| データベース | Supabase (PostgreSQL) | RLS、リアルタイム、認証統合 |
| 認証 | Supabase Auth | ソーシャルログイン、JWT |
| ホスティング | Railway | 簡易デプロイ、WebSocket対応 |
| ストレージ | Supabase Storage | 音声ファイル、生成物保存 |

---

## 2. コンポーネント設計

### 2.1 フロントエンド構成

```
frontend/
├── index.html
├── css/
│   ├── main.css
│   ├── components/
│   │   ├── header.css
│   │   ├── conversation.css
│   │   ├── extraction.css
│   │   ├── analysis.css
│   │   └── suggestion.css
│   └── utils/
│       └── variables.css
├── js/
│   ├── app.js              # エントリーポイント
│   ├── websocket.js        # WebSocket管理
│   ├── audio.js            # 音声キャプチャ
│   ├── components/
│   │   ├── conversation.js # 会話ログUI
│   │   ├── extraction.js   # 抽出情報UI
│   │   ├── analysis.js     # 分析UI
│   │   └── suggestion.js   # 提案UI
│   ├── state/
│   │   └── store.js        # 状態管理（シンプル実装）
│   └── utils/
│       ├── api.js          # API呼び出し
│       └── helpers.js      # ユーティリティ
└── assets/
    └── icons/
```

### 2.2 バックエンド構成

```
backend/
├── main.py                 # FastAPIエントリーポイント
├── config.py               # 設定管理
├── routers/
│   ├── __init__.py
│   ├── auth.py             # 認証エンドポイント
│   ├── sessions.py         # セッション管理API
│   ├── websocket.py        # WebSocketハンドラ
│   └── outputs.py          # 成果物生成API
├── services/
│   ├── __init__.py
│   ├── stt_service.py      # Deepgram連携
│   ├── extraction_service.py    # 情報抽出
│   ├── analysis_service.py      # 構造分析
│   ├── suggestion_service.py    # サジェスト生成
│   ├── reframing_service.py     # リフレーミング
│   └── output_service.py        # ノンネーム/IM生成
├── models/
│   ├── __init__.py
│   ├── session.py          # セッションモデル
│   ├── extraction.py       # 抽出情報モデル
│   ├── analysis.py         # 分析結果モデル
│   └── suggestion.py       # サジェストモデル
├── prompts/
│   ├── extraction.py       # 抽出プロンプト
│   ├── analysis.py         # 分析プロンプト
│   ├── suggestion.py       # サジェストプロンプト
│   └── output.py           # 成果物生成プロンプト
├── db/
│   ├── __init__.py
│   ├── supabase.py         # Supabaseクライアント
│   └── repositories/
│       ├── session_repo.py
│       └── extraction_repo.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

---

## 3. データフロー

### 3.1 リアルタイム音声処理フロー

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ マイク   │───▶│ AudioAPI │───▶│ WebSocket│───▶│ FastAPI  │
│          │    │(Browser) │    │ (Client) │    │ (Server) │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                      │
                                                      ▼
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Server                          │
│                                                              │
│   音声バイナリ ──▶ Deepgram WSS ──▶ テキスト               │
│                                           │                  │
│                                           ▼                  │
│                          ┌─────────────────────────┐        │
│                          │    Extraction Engine    │        │
│                          │   (Claude API呼び出し)  │        │
│                          └───────────┬─────────────┘        │
│                                      │                       │
│                                      ▼                       │
│                          ┌─────────────────────────┐        │
│                          │ 抽出情報 + 分析 + 提案  │        │
│                          └───────────┬─────────────┘        │
│                                      │                       │
└──────────────────────────────────────┼───────────────────────┘
                                       │
                                       ▼ WebSocket
                               ┌──────────────┐
                               │   クライアント │
                               │   UI更新     │
                               └──────────────┘
```

### 3.2 WebSocketメッセージ仕様

#### クライアント → サーバー

```typescript
// 音声データ送信
{
  "type": "audio",
  "data": "<base64 encoded audio>"
}

// セッション開始
{
  "type": "session_start",
  "session_id": "uuid",
  "project_id": "uuid"
}

// セッション終了
{
  "type": "session_end"
}

// ピン留め
{
  "type": "pin",
  "utterance_id": "uuid"
}
```

#### サーバー → クライアント

```typescript
// 文字起こし結果
{
  "type": "transcript",
  "data": {
    "id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "speaker": "customer" | "user",
    "text": "発言内容",
    "is_final": true,
    "is_important": false
  }
}

// 抽出情報更新
{
  "type": "extraction_update",
  "data": {
    "category": "basic_info",
    "field": "employee_count",
    "value": "15名",
    "confidence": 0.95,
    "source_utterance_id": "uuid"
  }
}

// 分析更新
{
  "type": "analysis_update",
  "data": {
    "structure_analysis": "...",
    "buyer_profiles": [...],
    "risk_factors": [...]
  }
}

// サジェスト更新
{
  "type": "suggestion_update",
  "data": {
    "suggestions": [
      {
        "id": "uuid",
        "type": "question" | "reframing",
        "content": "質問内容",
        "reason": "理由",
        "layer": "structure",
        "priority": 0.8
      }
    ]
  }
}

// エラー
{
  "type": "error",
  "data": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ"
  }
}
```

---

## 4. AI処理パイプライン

### 4.1 処理フロー

```
音声テキスト
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                  バッファリング                          │
│  (5〜10秒分のテキストを蓄積してからAPI呼び出し)         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  情報抽出 (Claude API)                   │
│                                                          │
│  入力: 会話テキスト + 既存抽出情報                       │
│  出力: 新規抽出情報 (差分)                               │
│                                                          │
│  処理時間目標: 3秒以内                                   │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     ┌─────────┐   ┌─────────┐   ┌─────────┐
     │構造分析 │   │買い手像 │   │サジェスト│
     │ (並列)  │   │ (並列)  │   │ (並列)  │
     └────┬────┘   └────┬────┘   └────┬────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                   クライアント送信
```

### 4.2 Claude API呼び出し戦略

#### バッチ処理 vs ストリーミング

| 処理 | 方式 | 理由 |
|------|------|------|
| 情報抽出 | バッチ | 構造化出力が必要 |
| 構造分析 | バッチ | まとまった分析が必要 |
| サジェスト | ストリーミング | 即時性重視 |

#### レート制限対策

```python
class ClaudeRateLimiter:
    """
    Claude APIのレート制限を管理
    - RPM (Requests Per Minute): 60
    - TPM (Tokens Per Minute): 100,000
    """

    def __init__(self):
        self.request_times = []
        self.token_counts = []

    async def acquire(self, estimated_tokens: int):
        # レート制限チェック
        await self._wait_if_needed()
        # リクエスト記録
        self._record_request(estimated_tokens)

    async def _wait_if_needed(self):
        # 必要に応じてウェイト
        pass
```

### 4.3 プロンプト最適化

#### トークン効率化

```python
# 悪い例：毎回全情報を送信
prompt = f"""
会話全文:
{full_conversation}

これまでの抽出情報:
{all_extracted_info}
"""

# 良い例：差分のみ送信
prompt = f"""
新しい会話部分:
{new_utterances_only}

変更があった抽出情報のキー:
{changed_keys_only}
"""
```

---

## 5. データベース設計

### 5.1 テーブル構成

```sql
-- ユーザー（Supabase Auth連携）
-- auth.usersを使用

-- プロジェクト（案件）
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    name TEXT NOT NULL,
    company_name TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- セッション（面談）
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    status TEXT DEFAULT 'active'
);

-- 発話（会話ログ）
CREATE TABLE utterances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    timestamp TIMESTAMPTZ NOT NULL,
    speaker TEXT NOT NULL, -- 'user' | 'customer'
    text TEXT NOT NULL,
    is_important BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 抽出情報
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    category TEXT NOT NULL, -- 'basic_info', 'financial', etc.
    field TEXT NOT NULL,
    value TEXT,
    confidence FLOAT,
    source_utterance_id UUID REFERENCES utterances(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 分析結果
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    analysis_type TEXT NOT NULL, -- 'structure', 'buyer', 'risk'
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- サジェスト履歴
CREATE TABLE suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    suggestion_type TEXT NOT NULL, -- 'question', 'reframing'
    content TEXT NOT NULL,
    reason TEXT,
    layer TEXT, -- 'surface', 'structure', 'essence', 'exit'
    was_used BOOLEAN DEFAULT false,
    was_dismissed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 成果物
CREATE TABLE outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    output_type TEXT NOT NULL, -- 'non_name', 'im'
    content JSONB NOT NULL,
    file_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 5.2 RLS (Row Level Security)

```sql
-- プロジェクトは所有者のみアクセス可
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own projects"
ON projects FOR ALL
USING (auth.uid() = user_id);

-- セッションはプロジェクト経由でアクセス
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access sessions of their projects"
ON sessions FOR ALL
USING (
    project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    )
);

-- 以下同様に他テーブルもRLS設定
```

---

## 6. セキュリティ

### 6.1 認証・認可

```python
# FastAPI依存性注入による認証
async def get_current_user(
    authorization: str = Header(None)
) -> User:
    if not authorization:
        raise HTTPException(401, "Authorization header required")

    token = authorization.replace("Bearer ", "")
    user = await supabase.auth.get_user(token)

    if not user:
        raise HTTPException(401, "Invalid token")

    return user

# エンドポイントでの使用
@router.get("/sessions")
async def get_sessions(user: User = Depends(get_current_user)):
    return await session_repo.get_by_user(user.id)
```

### 6.2 データ暗号化

| データ | 暗号化方式 |
|--------|-----------|
| 通信 | TLS 1.3 (HTTPS/WSS) |
| DB保存 | Supabase標準暗号化 |
| 音声ファイル | Supabase Storage暗号化 |
| APIキー | 環境変数 + Secret Manager |

### 6.3 入力検証

```python
from pydantic import BaseModel, validator

class SessionCreate(BaseModel):
    project_id: str
    name: str

    @validator('project_id')
    def validate_project_id(cls, v):
        if not is_valid_uuid(v):
            raise ValueError('Invalid project_id')
        return v

    @validator('name')
    def validate_name(cls, v):
        if len(v) > 200:
            raise ValueError('Name too long')
        return sanitize_string(v)
```

---

## 7. パフォーマンス最適化

### 7.1 キャッシング戦略

```python
from functools import lru_cache
import redis

# インメモリキャッシュ（プロンプトテンプレート等）
@lru_cache(maxsize=100)
def get_prompt_template(template_name: str) -> str:
    return load_template(template_name)

# Redis（セッション状態）
class SessionCache:
    def __init__(self):
        self.redis = redis.Redis()

    async def get_extraction_state(self, session_id: str) -> dict:
        key = f"session:{session_id}:extraction"
        return await self.redis.hgetall(key)

    async def update_extraction(self, session_id: str, field: str, value: str):
        key = f"session:{session_id}:extraction"
        await self.redis.hset(key, field, value)
```

### 7.2 非同期処理

```python
import asyncio

async def process_utterance(utterance: str, session_state: dict):
    """
    発話を処理し、複数の分析を並列実行
    """
    # 情報抽出は先に実行（他の分析の入力になる）
    extraction_result = await extraction_service.extract(utterance, session_state)

    # 分析は並列実行
    analysis_tasks = [
        analysis_service.analyze_structure(extraction_result),
        analysis_service.infer_buyers(extraction_result),
        suggestion_service.generate(extraction_result, session_state),
    ]

    results = await asyncio.gather(*analysis_tasks)

    return {
        "extraction": extraction_result,
        "structure": results[0],
        "buyers": results[1],
        "suggestions": results[2],
    }
```

### 7.3 WebSocket最適化

```python
# メッセージのバッチ送信
class WebSocketManager:
    def __init__(self):
        self.pending_messages = []
        self.flush_interval = 0.1  # 100ms

    async def send(self, websocket, message):
        self.pending_messages.append(message)

        if len(self.pending_messages) >= 10:
            await self._flush(websocket)

    async def _flush(self, websocket):
        if self.pending_messages:
            # まとめて送信
            await websocket.send_json({
                "type": "batch",
                "messages": self.pending_messages
            })
            self.pending_messages = []
```

---

## 8. 監視・ログ

### 8.1 ログ設計

```python
import structlog

logger = structlog.get_logger()

# 構造化ログ
logger.info(
    "extraction_completed",
    session_id=session_id,
    field_count=len(extracted_fields),
    processing_time_ms=processing_time,
    token_usage=token_count
)
```

### 8.2 メトリクス

| メトリクス | 説明 | 閾値 |
|-----------|------|------|
| ws_latency_ms | WebSocket往復遅延 | < 100ms |
| stt_latency_ms | 音声→テキスト遅延 | < 1000ms |
| extraction_time_ms | 情報抽出処理時間 | < 3000ms |
| claude_token_usage | Claude APIトークン使用量 | モニタリング |
| active_sessions | アクティブセッション数 | < 100 |

### 8.3 アラート

```yaml
# Datadog/PagerDuty等での設定例
alerts:
  - name: high_extraction_latency
    condition: extraction_time_ms > 5000
    severity: warning

  - name: websocket_errors
    condition: ws_error_rate > 0.01
    severity: critical

  - name: claude_api_errors
    condition: claude_error_rate > 0.05
    severity: critical
```

---

## 9. デプロイメント

### 9.1 環境構成

| 環境 | 用途 | URL |
|------|------|-----|
| development | ローカル開発 | localhost:8000 |
| staging | 検証環境 | staging.tonari-ma.com |
| production | 本番環境 | app.tonari-ma.com |

### 9.2 CI/CD

```yaml
# GitHub Actions
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

      - name: Deploy to Railway
        uses: railwayapp/deploy@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
```

### 9.3 環境変数

```bash
# .env.example
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_KEY=xxx

DEEPGRAM_API_KEY=xxx

ANTHROPIC_API_KEY=xxx

REDIS_URL=redis://localhost:6379

ENVIRONMENT=development
LOG_LEVEL=INFO
```
