# AGENT-memo.md

## 最終更新
2025-12-31 14:55:00

## 進捗

### 完了
- [x] プロダクト要件定義書（`docs/requirements/01_product_requirements.md`）
- [x] 水野メソッドシステム化仕様（`docs/requirements/02_mizuno_method_spec.md`）
- [x] 画面設計・UI仕様（`docs/requirements/03_ui_specification.md`）
- [x] 技術アーキテクチャ設計（`docs/requirements/04_technical_architecture.md`）
- [x] API仕様（`docs/requirements/05_api_specification.md`）
- [x] AGENT.md（開発規約）の配置・カスタマイズ
- [x] docs/の規約準拠での再構成
- [x] backend-design.md の作成
- [x] frontend-design.md の作成
- [x] db-design.md の作成
- [x] ai-pipeline-design.md の作成
- [x] プロジェクト構造の初期化（uv, pyproject.toml）
- [x] バックエンド基盤実装
  - `backend/app/models/mna_schemas.py` - Pydanticスキーマ定義（約35項目のIM抽出フィールド含む）
  - `backend/app/services/mna_extraction.py` - 情報抽出サービス（Claude API連携）
  - `backend/app/services/mna_suggestion.py` - サジェスト生成サービス（水野メソッド実装）
  - `backend/app/api/mna_session.py` - セッションAPI（REST + WebSocket）
  - `backend/app/api/mna_project.py` - プロジェクト管理API
- [x] フロントエンドをTypeScript + TailwindCSS + Viteに変更
  - `frontend/src/types/` - API型定義、WebSocket型定義
  - `frontend/src/lib/api.ts` - APIクライアント
  - `frontend/src/hooks/useWebSocket.ts` - WebSocket管理フック
  - `frontend/src/stores/sessionStore.ts` - Zustandによるセッション状態管理
  - `frontend/src/components/` - UIコンポーネント（Button, Card, Badge, ConversationLog, ExtractionPanel, SuggestionPanel, ProgressBar）
  - `frontend/src/app/` - 画面コンポーネント（Layout, Dashboard, Session）

### 進行中
- [ ] 音声キャプチャ実装（ブラウザ MediaRecorder API）
- [ ] Deepgram WebSocket連携（リアルタイムSTT）
- [ ] 成果物生成機能（ノンネーム/IM）

### TODO
- [ ] Supabaseマイグレーション作成・適用
- [ ] 認証機能実装
- [ ] PPT生成サービス実装（python-pptx）
- [ ] E2Eテスト作成
- [ ] Railwayデプロイ設定

## 技術的な決定事項

### フロントエンド
- **Vite + React + TypeScript**: 高速ビルド、型安全性
- **TailwindCSS v4**: `@import "tailwindcss"` 形式、`@theme` でカスタムカラー定義
- **Zustand**: 軽量な状態管理
- **React Router v6**: SPAルーティング

### バックエンド
- **FastAPI**: 非同期対応、WebSocket対応
- **Claude claude-sonnet-4-20250514**: 情報抽出・分析・サジェスト生成
- **インメモリセッション管理**: 本番ではRedisに置き換え予定

### 水野メソッド実装
- **4層モデル**: surface → structure → essence → exit
- **リフレーミングパターン**: `NEGATIVE_PATTERNS` 辞書でルールベース + AI生成
- **サジェスト優先度計算**: レイヤー距離 + 出口ボーナス + 文脈関連性

## ファイル構造

```
TONARI-MnA/
├── AGENT.md                    # 開発規約（カスタマイズ済み）
├── CLAUDE.md                   # Claude Codeコンテキスト
├── pyproject.toml              # Python依存関係（uv管理）
├── backend/
│   └── app/
│       ├── main.py             # FastAPIアプリ（M&Aルーター登録済み）
│       ├── models/
│       │   ├── schemas.py      # 既存スキーマ
│       │   └── mna_schemas.py  # M&A用スキーマ（NEW）
│       ├── services/
│       │   ├── mna_extraction.py  # 情報抽出サービス（NEW）
│       │   └── mna_suggestion.py  # サジェスト生成サービス（NEW）
│       └── api/
│           ├── mna_session.py  # セッションAPI（NEW）
│           └── mna_project.py  # プロジェクトAPI（NEW）
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── index.css           # TailwindCSS v4形式
│       ├── types/              # 型定義
│       ├── lib/                # APIクライアント
│       ├── hooks/              # カスタムフック
│       ├── stores/             # Zustandストア
│       ├── components/         # UIコンポーネント
│       └── app/                # 画面コンポーネント
└── docs/
    ├── AGENT-memo.md           # このファイル
    ├── backend-design.md
    ├── frontend-design.md
    ├── db-design.md
    ├── ai-pipeline-design.md
    ├── requirements/           # 要件定義
    └── tools/                  # ツールドキュメント
```

## 参考資料
- MTG本質抽出: `docs/mtg_essence_2024_12.md`
- 福島さんMTG文字起こし（3件）: 分析済み、水野メソッド抽出完了
- IMサンプル: ファンドブック作成の35ページPPT

## コンテキスト
- プロジェクト名: TONARI for M&A
- コンセプト: 「水野メソッドの民主化」
- ターゲット: 個人M&Aアドバイザー、アベンジャーズクラブ受講生
- 技術スタック: FastAPI + Deepgram + Claude API + Supabase + TypeScript/TailwindCSS
