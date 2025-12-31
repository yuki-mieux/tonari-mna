# 聖人君子AI - リアルタイム・マネジメント支援ツール

管理職の1on1・会議をリアルタイムで支援し、パワハラを未然に防ぐAIパートナー。

## 概要

| 項目 | 内容 |
|------|------|
| **ミッション** | 「管理職の隣にいる、最高の相棒」 |
| **ターゲット** | 大手企業の管理職（マネジメント層） |
| **コンセプト** | パワハラの「摘発」ではなく「リアルタイム・ナビゲーション」 |

## 解決する課題

### 従来のパワハラ対策の限界

| 課題 | 現状 | 聖人君子AIの解決策 |
|------|------|------------------|
| 無自覚 | 行為者の54%が自覚なし | リスク発言を即時検知・気づきを促す |
| 選択肢不足 | 怒りを抑えても代わりの言葉がない | 具体的な言い換え選択肢を提示 |
| 断面的支援 | 年1回の研修で終わり | 日々の会話でリアルタイム支援 |
| 事後対応 | 起きてから対処 | 未然防止・行動変容 |

## 主要機能（3タブ構成）

### 1. リアルタイムタブ
会話をリアルタイムで文字起こしし、リスク発言を即時検知

| 機能 | 説明 |
|------|------|
| 文字起こし | Deepgram APIによるリアルタイムSTT |
| 話者分離 | 自分と相手の発言を色分け |
| リスク検知 | パワハラリスクのある発言をハイライト |

### 2. 言い換え提案タブ
リスク発言に対する代替表現を提案

| 例 | 元の発言 | 提案 |
|----|---------|------|
| 1 | 「なぜできないの？」 | 「具体的にどこで詰まっていますか？」 |
| 2 | 「何度言ったらわかる」 | 「一緒に原因を考えましょう」 |
| 3 | 「君には無理」 | 「どんなサポートがあれば進められそう？」 |

### 3. 振り返りタブ
セッション終了後のサマリーと改善ポイント

- 良かった点のフィードバック
- 改善できる点の提案
- 次回へのアクションアイテム

## 技術スタック

| 項目 | 技術 |
|------|------|
| 音声認識 | Deepgram API（WebSocket、リアルタイムSTT） |
| AI分析 | Claude API（claude-sonnet-4-20250514） |
| フロントエンド | バニラHTML/CSS/JavaScript |
| バックエンド | FastAPI (Python) |
| データベース | Supabase（PostgreSQL + Auth + RLS） |
| パッケージ管理 | uv |
| ホスティング | Railway |

## API構成

| エンドポイント | 機能 |
|---------------|------|
| `POST /api/harassment_check` | リスク発言検知 |
| `POST /api/rephrase` | 言い換え提案 |
| `POST /api/reflection` | 壁打ち・振り返り |
| `GET/POST /api/sessions` | セッション管理 |

## ディレクトリ構成

```
TONARI-ハラスメント/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPIアプリ
│   │   ├── api/
│   │   │   ├── harassment_check.py    # リスク発言検知
│   │   │   ├── rephrase.py            # 言い換え提案
│   │   │   └── reflection.py          # 振り返り支援
│   │   ├── core/
│   │   │   ├── auth.py                # 認証
│   │   │   └── config.py              # 設定
│   │   └── services/
│   │       └── agent.py               # Claude API
│   └── .env                           # 環境変数
├── public/
│   ├── index.html                     # HTML
│   ├── styles.css                     # CSS
│   └── app.js                         # JavaScript
├── 関連資材/                           # 顧客資料
├── CLAUDE.md                          # 開発コンテキスト
└── README.md                          # このファイル
```

## ローカル開発

### 環境構築

```bash
# 依存関係インストール
uv sync
```

### サーバー起動

```bash
# 起動
uv run uvicorn backend.app.main:app --reload --port 8000

# アクセス
open http://localhost:8000/app
```

### サーバー停止

```bash
# Ctrl+C または
lsof -ti:8000 | xargs kill -9
```

## 環境変数

| 変数 | 用途 |
|------|------|
| `ANTHROPIC_API_KEY` | Claude API |
| `DEEPGRAM_API_KEY` | Deepgram API |
| `SUPABASE_URL` | Supabaseプロジェクト |
| `SUPABASE_ANON_KEY` | Supabase匿名キー |

## Railwayデプロイ

### 1. 前提条件

- GitHubアカウント
- [Railway](https://railway.app/)アカウント
- このリポジトリをGitHubにプッシュ済み

### 2. デプロイ手順

#### Step 1: Railwayプロジェクト作成

1. [Railway](https://railway.app/) にログイン
2. 「New Project」をクリック
3. 「Deploy from GitHub repo」を選択
4. このリポジトリを選択

#### Step 2: 環境変数設定

RailwayのプロジェクトSettings > Variablesで以下を設定：

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
DEEPGRAM_API_KEY=xxxxx
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx
```

#### Step 3: デプロイ確認

1. 「Deploy」タブでビルドログを確認
2. ビルド完了後、生成されたURLにアクセス
3. `https://your-app.up.railway.app/app` でアプリを開く

### 3. デプロイ設定ファイル

プロジェクトには以下のデプロイ設定が含まれています：

- `Procfile` - 起動コマンド
- `railway.toml` - Railway固有設定
- `requirements.txt` - Python依存関係

### 4. カスタムドメイン（オプション）

1. RailwayのSettings > Domains
2. 「Add Custom Domain」
3. DNSレコードを設定

## ベースプロジェクト

このプロジェクトは「Tonari」（面接官向けリアルタイム会話支援AI）をベースに開発しています。

### 変更点

| Tonari（面接官支援） | 聖人君子AI（管理職支援） |
|-------------------|---------------------|
| 求職者の発言をチェック | 部下との会話をリスク分析 |
| 求人マッチング提案 | 言い換え提案 |
| 深掘り質問の提案 | コミュニケーション改善提案 |

## 顧客事例（グローイング社実績）

### 導入企業
- 本田技研工業（Honda）: 3,500名以上受講
- ヤマハ: 人事コンプライアンスグループで導入
- ハウス食品: 営業本部HRBPで導入

### 効果
- エンゲージメントサーベイの心理的安全性指標が向上
- 「壁打ち」がパワハラ防止の共通認識ワードに
- 上司-部下間の関係性スコアが大幅上昇

## 開発フェーズ

### Phase 1: MVP（PoC用）
- [x] リアルタイム文字起こし
- [x] 話者分離（自分/相手）
- [x] リスク発言検知（API実装済み）
- [x] 振り返り生成（API実装済み）
- [x] シンプルなカードベースUI
- [ ] 言い換え提案（rephrase API）
- [ ] 実動作テスト

### Phase 2: プラットフォーム化
- [ ] パワハラリスクスコア連携
- [ ] 部下データ連携
- [ ] 組織ダッシュボード
- [ ] オンプレ/ローカルLLM対応

## 現在の状態（2024-12-24）

| 項目 | 状態 |
|------|------|
| ブランチ | `feature/ui-mockup-v4` |
| ローカル動作 | ✅ http://localhost:8000/app |
| Railwayデプロイ | ⏸️ 準備完了（未実施） |

### 次回やること

1. リスク検知の実動作テスト（マイクで話して検知確認）
2. 振り返り機能テスト（セッション終了→モーダル）
3. 本番デプロイ（Railway別プロジェクト）
4. rephrase API実装

## 関連資料

`関連資材/` フォルダに以下の資料があります：
- 価値設計思考に基づくMTG議事録
- Honda導入事例
- ヤマハ導入事例
- ハウス食品導入事例

詳細は [CLAUDE.md](CLAUDE.md) を参照。

## ライセンス

Private - 開発中
