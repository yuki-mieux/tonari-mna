# フロントエンド設計書

## 概要
TONARI for M&AのフロントエンドはTypeScript + TailwindCSSで構築し、リアルタイム面談支援UIを提供する。

## 使用技術

| 技術 | バージョン | 用途 |
|------|-----------|------|
| TypeScript | 5.0+ | 言語 |
| Vite | 5.0+ | ビルドツール |
| React | 18.0+ | UIフレームワーク |
| TailwindCSS | 3.4+ | スタイリング |
| Zustand | 4.0+ | 状態管理 |
| @supabase/supabase-js | 2.0+ | Supabase連携 |

## フォルダ構成

```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── src/
│   ├── main.tsx                 # エントリーポイント
│   ├── App.tsx                  # ルートコンポーネント
│   ├── app/                     # 画面/ルーティング
│   │   ├── routes.tsx           # ルート定義
│   │   ├── Layout.tsx           # 共通レイアウト
│   │   ├── Dashboard.tsx        # ダッシュボード
│   │   ├── Session.tsx          # 面談画面
│   │   ├── ProjectDetail.tsx    # プロジェクト詳細
│   │   └── Output.tsx           # 成果物確認
│   ├── components/              # 再利用UI部品
│   │   ├── ui/                  # 基本UI（Button, Input等）
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── Loading.tsx
│   │   ├── Header.tsx           # ヘッダー
│   │   ├── ConversationLog.tsx  # 会話ログ
│   │   ├── ExtractionPanel.tsx  # 抽出情報パネル
│   │   ├── AnalysisPanel.tsx    # 分析パネル
│   │   ├── SuggestionPanel.tsx  # サジェストパネル
│   │   └── ProgressBar.tsx      # 進捗バー
│   ├── features/                # 機能単位のUI
│   │   ├── session/             # 面談関連
│   │   │   ├── AudioRecorder.tsx
│   │   │   ├── SessionControls.tsx
│   │   │   └── SessionSummary.tsx
│   │   ├── project/             # プロジェクト関連
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectCard.tsx
│   │   │   └── ProjectForm.tsx
│   │   └── output/              # 成果物関連
│   │       ├── NonNamePreview.tsx
│   │       ├── IMPreview.tsx
│   │       └── DownloadButton.tsx
│   ├── hooks/                   # カスタムフック
│   │   ├── useWebSocket.ts      # WebSocket管理
│   │   ├── useAudio.ts          # 音声キャプチャ
│   │   ├── useAuth.ts           # 認証
│   │   └── useSession.ts        # セッション状態
│   ├── lib/                     # APIクライアント・ユーティリティ
│   │   ├── api.ts               # REST API呼び出し
│   │   ├── websocket.ts         # WebSocket接続
│   │   └── supabase.ts          # Supabaseクライアント
│   ├── stores/                  # 状態管理（Zustand）
│   │   ├── sessionStore.ts      # セッション状態
│   │   ├── extractionStore.ts   # 抽出情報状態
│   │   └── authStore.ts         # 認証状態
│   ├── styles/                  # グローバルスタイル
│   │   └── globals.css          # TailwindベースCSS
│   └── types/                   # 型定義
│       ├── api.ts               # APIレスポンス型
│       ├── websocket.ts         # WebSocketメッセージ型
│       └── supabase.ts          # Supabase生成型
└── public/                      # 静的アセット
    └── favicon.svg
```

## 各モジュールの役割

### app/
- ページコンポーネント
- React Routerでのルーティング
- 画面レイアウト

### components/
- 再利用可能なUIコンポーネント
- ui/には汎用的なプリミティブ
- 業務固有のコンポーネントはトップレベルに

### features/
- 機能単位でまとめたコンポーネント群
- 関連するコンポーネント・ロジックを同じディレクトリに

### hooks/
- カスタムフック
- ロジックの再利用
- 副作用の分離

### lib/
- APIクライアント
- 外部サービス連携
- ユーティリティ関数

### stores/
- Zustandによる状態管理
- グローバル状態の一元管理

### types/
- TypeScript型定義
- API/WebSocketのスキーマ型

## 画面構成

### ダッシュボード（/）
- プロジェクト一覧
- 新規プロジェクト作成
- 最近のセッション

### 面談画面（/session/:id）
- 2カラムレイアウト
- 左: 会話ログ
- 右: 抽出情報・分析・サジェスト（タブ切替）
- フッター: 進捗・アクション

### プロジェクト詳細（/project/:id）
- 抽出情報サマリー
- セッション履歴
- 成果物生成

### 成果物確認（/output/:id）
- ノンネーム/IMプレビュー
- ダウンロード
- 編集

## コンポーネント設計

### 命名規則
- PascalCase（例: `ConversationLog.tsx`）
- 機能を表す名前

### Props設計
```typescript
// 良い例: 明確な型定義
interface ConversationLogProps {
  utterances: Utterance[];
  onPin: (id: string) => void;
  isRecording: boolean;
}

// 悪い例: any型、過剰なprops
interface BadProps {
  data: any;
  // ...10個以上のprops
}
```

### 状態管理方針
- ローカル状態: useState（コンポーネント内で完結）
- グローバル状態: Zustand（複数コンポーネントで共有）
- サーバー状態: React Query（将来的に検討）

## スタイリング方針

### TailwindCSS
- ユーティリティファースト
- カスタムクラスは最小限
- デザイントークンはtailwind.config.jsで定義

### カラースキーム
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',
        secondary: '#6B7280',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
      }
    }
  }
}
```

### レスポンシブ
- モバイルファースト
- ブレークポイント: sm(640px), md(768px), lg(1024px), xl(1280px)

## WebSocket通信

### 接続管理
```typescript
// hooks/useWebSocket.ts
function useWebSocket(sessionId: string) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const wsRef = useRef<WebSocket | null>(null);

  // 接続・再接続・切断ロジック
}
```

### メッセージハンドリング
```typescript
// 受信メッセージの型安全なハンドリング
switch (message.type) {
  case 'transcript':
    handleTranscript(message.data);
    break;
  case 'extraction_update':
    handleExtraction(message.data);
    break;
  // ...
}
```

## 起動コマンド

```bash
# 開発
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview

# 型チェック
npm run type-check

# リント
npm run lint
```
