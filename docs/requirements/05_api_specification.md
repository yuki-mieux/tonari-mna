# TONARI for M&A - API仕様書

## 1. API概要

### 1.1 ベースURL

| 環境 | URL |
|------|-----|
| Development | `http://localhost:8000/api/v1` |
| Staging | `https://staging.tonari-ma.com/api/v1` |
| Production | `https://api.tonari-ma.com/api/v1` |

### 1.2 認証

すべてのAPIリクエストには認証が必要（一部を除く）。

```
Authorization: Bearer <supabase_access_token>
```

### 1.3 共通レスポンス形式

```typescript
// 成功時
{
  "success": true,
  "data": { ... }
}

// エラー時
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

---

## 2. REST API エンドポイント

### 2.1 プロジェクト（案件）管理

#### プロジェクト一覧取得
```
GET /projects
```

**Response:**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "uuid",
        "name": "株式会社○○",
        "company_name": "株式会社○○",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "extraction_progress": {
          "basic_info": 80,
          "financial": 40,
          "business": 60,
          "organization": 20,
          "transfer": 30
        },
        "session_count": 3
      }
    ]
  }
}
```

#### プロジェクト作成
```
POST /projects
```

**Request:**
```json
{
  "name": "株式会社○○",
  "company_name": "株式会社○○"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "株式会社○○",
    "company_name": "株式会社○○",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### プロジェクト詳細取得
```
GET /projects/{project_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "project": {
      "id": "uuid",
      "name": "株式会社○○",
      "company_name": "株式会社○○",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "extractions": {
      "basic_info": {
        "company_name": { "value": "株式会社○○", "confidence": 1.0 },
        "industry": { "value": "建設業", "confidence": 0.95 },
        "employee_count": { "value": "15名", "confidence": 0.9 }
      },
      "financial": { ... },
      "business": { ... },
      "organization": { ... },
      "transfer": { ... }
    },
    "analysis": {
      "structure": "...",
      "buyer_profiles": [ ... ],
      "risk_factors": [ ... ]
    },
    "sessions": [
      {
        "id": "uuid",
        "started_at": "2024-01-01T10:00:00Z",
        "duration_seconds": 3600
      }
    ]
  }
}
```

#### プロジェクト更新
```
PATCH /projects/{project_id}
```

**Request:**
```json
{
  "name": "新しい名前",
  "status": "completed"
}
```

#### プロジェクト削除
```
DELETE /projects/{project_id}
```

---

### 2.2 セッション（面談）管理

#### セッション一覧取得
```
GET /projects/{project_id}/sessions
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "uuid",
        "project_id": "uuid",
        "started_at": "2024-01-01T10:00:00Z",
        "ended_at": "2024-01-01T11:00:00Z",
        "duration_seconds": 3600,
        "status": "completed",
        "utterance_count": 150,
        "extraction_count": 25
      }
    ]
  }
}
```

#### セッション詳細取得
```
GET /sessions/{session_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session": {
      "id": "uuid",
      "project_id": "uuid",
      "started_at": "2024-01-01T10:00:00Z",
      "ended_at": "2024-01-01T11:00:00Z",
      "duration_seconds": 3600,
      "status": "completed"
    },
    "utterances": [
      {
        "id": "uuid",
        "timestamp": "2024-01-01T10:00:30Z",
        "speaker": "customer",
        "text": "うちは創業30年で...",
        "is_important": true,
        "is_pinned": false
      }
    ],
    "extractions": { ... },
    "suggestions": [
      {
        "id": "uuid",
        "type": "question",
        "content": "従業員の方の平均年齢は？",
        "reason": "技術承継可能性の確認",
        "layer": "essence",
        "was_used": true
      }
    ]
  }
}
```

#### セッション開始（REST経由）
```
POST /projects/{project_id}/sessions
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "websocket_url": "wss://api.tonari-ma.com/ws/{session_id}"
  }
}
```

#### セッション終了
```
POST /sessions/{session_id}/end
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "duration_seconds": 3600,
    "extraction_summary": {
      "total_fields": 30,
      "extracted_fields": 22,
      "completion_rate": 0.73
    }
  }
}
```

---

### 2.3 抽出情報管理

#### 抽出情報取得
```
GET /sessions/{session_id}/extractions
```

**Response:**
```json
{
  "success": true,
  "data": {
    "extractions": {
      "basic_info": {
        "company_name": {
          "value": "株式会社○○",
          "confidence": 1.0,
          "source_utterance_id": "uuid",
          "updated_at": "2024-01-01T10:05:00Z"
        },
        "industry": {
          "value": "建設業",
          "confidence": 0.95,
          "source_utterance_id": "uuid",
          "updated_at": "2024-01-01T10:03:00Z"
        }
      },
      "financial": { ... }
    },
    "progress": {
      "basic_info": 0.8,
      "financial": 0.4,
      "business": 0.6,
      "organization": 0.2,
      "transfer": 0.3,
      "overall": 0.46
    }
  }
}
```

#### 抽出情報手動更新
```
PATCH /sessions/{session_id}/extractions
```

**Request:**
```json
{
  "category": "financial",
  "field": "revenue",
  "value": "3億円"
}
```

---

### 2.4 成果物生成

#### ノンネーム生成
```
POST /projects/{project_id}/outputs/non-name
```

**Request:**
```json
{
  "format": "text"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "output_id": "uuid",
    "content": {
      "industry": "建設業",
      "region": "関東",
      "revenue_range": "1億〜5億円",
      "employee_range": "10〜20名",
      "transfer_reason": "後継者不在",
      "strengths": ["安定した顧客基盤", "30年の実績"],
      "summary": "関東エリアで30年の実績を持つ建設会社..."
    },
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### IM生成
```
POST /projects/{project_id}/outputs/im
```

**Request:**
```json
{
  "format": "pptx",
  "template_id": "default"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "output_id": "uuid",
    "status": "generating",
    "estimated_seconds": 30
  }
}
```

#### 成果物ステータス確認
```
GET /outputs/{output_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "output_id": "uuid",
    "type": "im",
    "status": "completed",
    "file_url": "https://storage.supabase.co/...",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 成果物ダウンロード
```
GET /outputs/{output_id}/download
```

**Response:** ファイルバイナリ（Content-Disposition: attachment）

---

## 3. WebSocket API

### 3.1 接続

```
WSS /ws/{session_id}
```

**接続時パラメータ:**
```
Authorization: Bearer <token>
```

### 3.2 メッセージタイプ一覧

#### クライアント → サーバー

| タイプ | 説明 |
|--------|------|
| `audio` | 音声データ送信 |
| `session_start` | セッション開始 |
| `session_end` | セッション終了 |
| `pin` | 発話ピン留め |
| `dismiss_suggestion` | サジェスト非表示 |
| `use_suggestion` | サジェスト使用 |

#### サーバー → クライアント

| タイプ | 説明 |
|--------|------|
| `connected` | 接続完了 |
| `transcript` | 文字起こし結果 |
| `extraction_update` | 抽出情報更新 |
| `analysis_update` | 分析結果更新 |
| `suggestion_update` | サジェスト更新 |
| `reframing` | リフレーミング提案 |
| `error` | エラー通知 |

### 3.3 メッセージ詳細

#### audio（クライアント → サーバー）
```json
{
  "type": "audio",
  "data": "<base64_encoded_audio>",
  "timestamp": "2024-01-01T10:00:30.123Z"
}
```

#### transcript（サーバー → クライアント）
```json
{
  "type": "transcript",
  "data": {
    "id": "uuid",
    "timestamp": "2024-01-01T10:00:30Z",
    "speaker": "customer",
    "text": "うちは創業30年で従業員は15人ぐらいです",
    "is_final": true,
    "is_important": true,
    "importance_reason": "基本情報（創業年・従業員数）を含む"
  }
}
```

#### extraction_update（サーバー → クライアント）
```json
{
  "type": "extraction_update",
  "data": {
    "updates": [
      {
        "category": "basic_info",
        "field": "founding_years",
        "value": "30年",
        "confidence": 0.95,
        "source_utterance_id": "uuid"
      },
      {
        "category": "basic_info",
        "field": "employee_count",
        "value": "15名",
        "confidence": 0.9,
        "source_utterance_id": "uuid"
      }
    ],
    "progress": {
      "basic_info": 0.6,
      "financial": 0.0,
      "overall": 0.12
    }
  }
}
```

#### analysis_update（サーバー → クライアント）
```json
{
  "type": "analysis_update",
  "data": {
    "structure_analysis": {
      "summary": "建設業×30年×15名体制",
      "inferences": [
        "安定した下請け基盤の可能性",
        "技術者の経験蓄積",
        "地域密着型の顧客関係"
      ],
      "confirmations_needed": [
        "主要取引先の依存度",
        "技術者の年齢構成"
      ]
    },
    "buyer_profiles": [
      {
        "type": "same_industry_expansion",
        "label": "同業他社（エリア拡大）",
        "fit_score": 0.8,
        "description": "都市部の建設会社で地方進出を狙う企業",
        "synergy": "地方の顧客基盤・許認可の取得",
        "key_info_needed": ["主要取引先", "保有許認可", "施工実績"]
      }
    ],
    "risk_factors": [
      {
        "factor": "後継者不在",
        "severity": "medium",
        "mitigation": "従業員承継の可能性確認"
      }
    ]
  }
}
```

#### suggestion_update（サーバー → クライアント）
```json
{
  "type": "suggestion_update",
  "data": {
    "suggestions": [
      {
        "id": "uuid",
        "type": "question",
        "priority": 0.9,
        "layer": "structure",
        "content": "主要取引先との取引は何年くらい続いていますか？",
        "reason": "顧客基盤の安定性を確認するため",
        "context_trigger": "創業30年との発言から"
      },
      {
        "id": "uuid",
        "type": "question",
        "priority": 0.7,
        "layer": "essence",
        "content": "従業員の方の平均年齢や勤続年数は？",
        "reason": "技術承継可能性を確認するため",
        "context_trigger": "15名体制との発言から"
      }
    ]
  }
}
```

#### reframing（サーバー → クライアント）
```json
{
  "type": "reframing",
  "data": {
    "trigger_phrase": "後継者がいない",
    "original_context": "息子はいるんですけど継ぐ気はなくて...",
    "reframe": {
      "perspective": "事業承継ニーズが明確",
      "positive_interpretation": "売却意思が固く、交渉がスムーズに進む可能性が高い",
      "verification_questions": [
        "従業員の方での承継は検討されましたか？",
        "第三者への譲渡についてはどうお考えですか？"
      ]
    }
  }
}
```

#### pin（クライアント → サーバー）
```json
{
  "type": "pin",
  "data": {
    "utterance_id": "uuid",
    "pinned": true,
    "note": "後で確認：具体的な売上規模"
  }
}
```

#### use_suggestion（クライアント → サーバー）
```json
{
  "type": "use_suggestion",
  "data": {
    "suggestion_id": "uuid"
  }
}
```

#### dismiss_suggestion（クライアント → サーバー）
```json
{
  "type": "dismiss_suggestion",
  "data": {
    "suggestion_id": "uuid",
    "reason": "already_asked"
  }
}
```

#### error（サーバー → クライアント）
```json
{
  "type": "error",
  "data": {
    "code": "STT_ERROR",
    "message": "音声認識サービスに接続できません",
    "recoverable": true,
    "retry_after_ms": 5000
  }
}
```

---

## 4. エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|----------------|------|
| `UNAUTHORIZED` | 401 | 認証エラー |
| `FORBIDDEN` | 403 | 権限エラー |
| `NOT_FOUND` | 404 | リソースが見つからない |
| `VALIDATION_ERROR` | 400 | 入力値エラー |
| `RATE_LIMITED` | 429 | レート制限超過 |
| `STT_ERROR` | 500 | 音声認識エラー |
| `AI_ERROR` | 500 | AI処理エラー |
| `INTERNAL_ERROR` | 500 | 内部エラー |

---

## 5. レート制限

| エンドポイント | 制限 |
|---------------|------|
| REST API（全体） | 100 req/min |
| WebSocket（音声） | 10 msg/sec |
| 成果物生成 | 10 req/hour |

超過時のレスポンス:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after_seconds": 60
  }
}
```

---

## 6. SDKサンプル

### 6.1 JavaScript (フロントエンド)

```javascript
class TonariClient {
  constructor(accessToken) {
    this.baseUrl = 'https://api.tonari-ma.com/api/v1';
    this.token = accessToken;
  }

  async getProjects() {
    const res = await fetch(`${this.baseUrl}/projects`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return res.json();
  }

  connectSession(sessionId) {
    const ws = new WebSocket(
      `wss://api.tonari-ma.com/ws/${sessionId}`,
      ['Authorization', this.token]
    );

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    return ws;
  }

  handleMessage(message) {
    switch (message.type) {
      case 'transcript':
        this.onTranscript?.(message.data);
        break;
      case 'extraction_update':
        this.onExtraction?.(message.data);
        break;
      case 'suggestion_update':
        this.onSuggestion?.(message.data);
        break;
      // ...
    }
  }
}
```

### 6.2 Python (バックエンド統合)

```python
import httpx
import websockets

class TonariClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.tonari-ma.com/api/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def create_project(self, name: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/projects",
                headers=self.headers,
                json={"name": name}
            )
            return response.json()

    async def connect_session(self, session_id: str):
        uri = f"wss://api.tonari-ma.com/ws/{session_id}"
        async with websockets.connect(uri, extra_headers=self.headers) as ws:
            async for message in ws:
                yield json.loads(message)
```
