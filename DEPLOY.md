# TONARI for M&A - デプロイ手順

## アーキテクチャ

```
┌─────────────────┐       ┌─────────────────┐
│     Vercel      │ ───── │    Railway      │
│   (Frontend)    │       │   (Backend)     │
│  React + Vite   │       │    FastAPI      │
└─────────────────┘       └─────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              ┌─────────────┐           ┌─────────────┐
              │  Supabase   │           │   Claude    │
              │ (Database)  │           │    API      │
              └─────────────┘           └─────────────┘
```

## 1. Railway（バックエンド）デプロイ

### 1.1 新規プロジェクト作成

1. [Railway](https://railway.app) にログイン
2. 「New Project」→「Deploy from GitHub repo」
3. このリポジトリを選択

### 1.2 環境変数設定

Railway のダッシュボードで以下の環境変数を設定：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `ANTHROPIC_API_KEY` | sk-ant-... | Claude API キー |
| `DEEPGRAM_API_KEY` | (取得後) | Deepgram API キー |
| `SUPABASE_URL` | https://xxx.supabase.co | Supabase URL |
| `SUPABASE_ANON_KEY` | eyJ... | Supabase Anon Key |
| `FRONTEND_URL` | https://your-app.vercel.app | フロントエンドURL（CORS用） |

### 1.3 デプロイ設定

`railway.toml` が自動で読み込まれます：

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd backend && gunicorn app.main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 -k uvicorn.workers.UvicornWorker"
healthcheckPath = "/health"
```

### 1.4 デプロイ確認

デプロイ後、以下のURLで確認：
- ヘルスチェック: `https://your-railway-app.railway.app/health`
- API ドキュメント: `https://your-railway-app.railway.app/docs`

---

## 2. Vercel（フロントエンド）デプロイ

### 2.1 新規プロジェクト作成

1. [Vercel](https://vercel.com) にログイン
2. 「Add New」→「Project」→ GitHub リポジトリを選択
3. **Root Directory** を `frontend` に設定

### 2.2 ビルド設定

| 設定 | 値 |
|------|-----|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

### 2.3 環境変数設定

| 変数名 | 値 |
|--------|-----|
| `VITE_API_URL` | `https://your-railway-app.railway.app` |
| `VITE_WS_URL` | `wss://your-railway-app.railway.app` |

### 2.4 デプロイ

「Deploy」ボタンをクリック。

---

## 3. Supabase セットアップ

### 3.1 プロジェクト作成

1. [Supabase](https://supabase.com) にログイン
2. 「New Project」で新規プロジェクト作成

### 3.2 テーブル作成

SQL Editor で `docs/db-design.md` のSQLを実行：

```sql
-- projects テーブル
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    company_name TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- sessions テーブル
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    status TEXT DEFAULT 'active'
);

-- 他のテーブルも同様に作成...
```

### 3.3 API キー取得

Settings → API から取得：
- `anon` key → `SUPABASE_ANON_KEY`
- URL → `SUPABASE_URL`

---

## 4. 外部サービス API キー取得

### Claude API (Anthropic)

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. API Keys → Create Key
3. `ANTHROPIC_API_KEY` として設定

### Deepgram (音声認識)

1. [Deepgram](https://deepgram.com/) にサインアップ
2. API Keys → Create Key
3. `DEEPGRAM_API_KEY` として設定

---

## 5. デプロイ後の確認

1. **バックエンド**
   - `/health` が `{"status": "healthy"}` を返す
   - `/docs` で Swagger UI が表示される

2. **フロントエンド**
   - ダッシュボードが表示される
   - プロジェクト作成ができる

3. **統合テスト**
   - プロジェクト作成 → セッション開始 → 終了

---

## トラブルシューティング

### CORS エラー
- Railway の `FRONTEND_URL` が正しいか確認
- Vercel のドメインと一致しているか確認

### WebSocket 接続エラー
- `VITE_WS_URL` が `wss://` で始まっているか確認
- Railway のURLと一致しているか確認

### API キーエラー
- Railway の環境変数が正しく設定されているか確認
- Anthropic/Deepgram のキーが有効か確認
