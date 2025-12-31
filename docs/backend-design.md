# バックエンド設計書

## 概要
TONARI for M&AのバックエンドはFastAPIで構築し、リアルタイム音声処理とAI推論を担当する。

## 使用技術

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.12+ | 実行環境 |
| FastAPI | 0.109+ | Webフレームワーク |
| uvicorn | 0.27+ | ASGIサーバー |
| pydantic | 2.0+ | バリデーション・スキーマ |
| supabase-py | 2.0+ | Supabase連携 |
| anthropic | 0.40+ | Claude API |
| deepgram-sdk | 3.0+ | 音声文字起こし |
| python-pptx | 0.6+ | IM生成 |
| jinja2 | 3.1+ | プロンプトテンプレート |

## フォルダ構成

```
backend/
├── __init__.py
├── main.py                  # アプリ起点、ルーター登録
├── core/                    # 設定・認証・共通ユーティリティ
│   ├── __init__.py
│   ├── config.py            # 環境変数・設定（pydantic Settings）
│   └── auth.py              # Supabase JWT検証
├── models/                  # Pydanticスキーマ（入出力）
│   ├── __init__.py
│   ├── session.py           # セッション関連スキーマ
│   ├── extraction.py        # 抽出情報スキーマ
│   ├── analysis.py          # 分析結果スキーマ
│   └── suggestion.py        # サジェストスキーマ
├── api/                     # ルーティング（エンドポイント定義）
│   ├── __init__.py
│   ├── health.py            # ヘルスチェック
│   ├── projects.py          # プロジェクトCRUD
│   ├── sessions.py          # セッションCRUD
│   ├── websocket.py         # WebSocketハンドラ
│   └── outputs.py           # 成果物生成
├── services/                # ビジネスロジック
│   ├── __init__.py
│   ├── stt.py               # Deepgram連携
│   ├── extraction.py        # 情報抽出ロジック
│   ├── analysis.py          # 構造分析ロジック
│   ├── suggestion.py        # サジェスト生成ロジック
│   ├── reframing.py         # リフレーミングロジック
│   └── output.py            # ノンネーム/IM生成
├── repositories/            # DBアクセス層（Supabase）
│   ├── __init__.py
│   ├── project.py           # projectsテーブル操作
│   ├── session.py           # sessionsテーブル操作
│   └── extraction.py        # extractionsテーブル操作
├── prompts/                 # LLMプロンプト（Jinja2テンプレート）
│   ├── extraction.j2        # 情報抽出プロンプト
│   ├── analysis.j2          # 構造分析プロンプト
│   ├── suggestion.j2        # サジェスト生成プロンプト
│   ├── reframing.j2         # リフレーミングプロンプト
│   └── output.j2            # 成果物生成プロンプト
├── templates/               # 成果物テンプレート
│   └── im_template.pptx     # IMのPPTXテンプレート
└── modules/                 # 外部連携モジュール
    ├── __init__.py
    ├── llm.py               # Claude APIラッパー
    └── deepgram.py          # Deepgramラッパー
```

## 各モジュールの役割

### core/
- **config.py**: pydantic Settingsで環境変数を管理。`.env`から読み込み。
- **auth.py**: Supabase JWTトークンの検証。FastAPIの依存性注入で使用。

### models/
- Pydanticモデルで入出力スキーマを定義
- APIリクエスト/レスポンスのバリデーション
- WebSocketメッセージのスキーマ

### api/
- FastAPIのルーター定義
- エンドポイントごとにファイル分割
- servicesを呼び出してビジネスロジックを実行

### services/
- ビジネスロジックの実装
- 外部API（Claude, Deepgram）との連携
- repositoriesを呼び出してDB操作

### repositories/
- Supabaseへのデータアクセス
- CRUD操作のカプセル化
- RLSを考慮したクエリ

### prompts/
- Jinja2テンプレートでプロンプトを管理
- 変数埋め込みで動的生成
- バージョン管理しやすい

### modules/
- 外部サービスとの連携ラッパー
- レート制限、リトライ、エラーハンドリング

## データフロー

### リアルタイム音声処理
```
クライアント
    │ WebSocket (WSS)
    ▼
api/websocket.py
    │
    ├──▶ modules/deepgram.py ──▶ Deepgram API
    │         │
    │         ▼ テキスト
    │
    ├──▶ services/extraction.py
    │         │
    │         ├──▶ modules/llm.py ──▶ Claude API
    │         │
    │         ▼ 抽出情報
    │
    ├──▶ services/analysis.py ──▶ 構造分析
    │
    ├──▶ services/suggestion.py ──▶ サジェスト
    │
    └──▶ WebSocket送信 ──▶ クライアント
```

### 成果物生成
```
api/outputs.py
    │
    ├──▶ repositories/extraction.py ──▶ 抽出情報取得
    │
    ├──▶ services/output.py
    │         │
    │         ├──▶ modules/llm.py ──▶ 文章生成
    │         │
    │         └──▶ python-pptx ──▶ PPTX生成
    │
    └──▶ Supabase Storage ──▶ ファイル保存
```

## エラーハンドリング方針

### 基本原則
- エラーは隠蔽しない
- HTTPExceptionで明示的にエラーを返す
- tryは非同期処理のみ許可

### エラーコード
| コード | HTTPステータス | 用途 |
|--------|---------------|------|
| UNAUTHORIZED | 401 | 認証失敗 |
| FORBIDDEN | 403 | 権限なし |
| NOT_FOUND | 404 | リソースなし |
| VALIDATION_ERROR | 400 | 入力不正 |
| RATE_LIMITED | 429 | レート制限 |
| STT_ERROR | 500 | Deepgramエラー |
| AI_ERROR | 500 | Claudeエラー |

## 起動コマンド

```bash
# 開発
uv run uvicorn backend.main:app --reload --port 8000

# 本番
uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```
