# AGENT.md - TONARI for M&A

## 1. 一般事項
- ユーザーは日本語話者です．思考は英語で良いですが，最終的な回答は日本語で行ってください．
- 以下の指示は基本的にPythonコードを生成することを目的としています．
- このリポジトリで開発・提案・実装方針を考える際は、基本的に以下の前提を優先してください（不明点がある場合は確認質問を出す）。

## 2. 環境とツール類
### パッケージ管理ツール：uv
- 依存関係は`pyproject.toml`で管理する（絶対に直接編集しない）
- `uv add <パッケージ名>`で追加
- 開発用の依存は`uv add --dev <パッケージ名>`で追加
- 実行は`uv run <cmd>`を基本にする

### バックエンド：FastAPI
- PythonのAPIサーバーはFastAPIを前提に設計する
- 起動コマンドは`uv run uvicorn backend.main:app --reload`
- WebSocketはFastAPIのWebSocket機能を使用

### データベース・認証・ストレージ：Supabase
- DB/認証はSupabaseを前提に設計する
- 接続情報は`.env`で管理し、コード内に直書きしない
- 詳しいコマンドは、[supabase](docs/tools/supabase.md)を参照

### フロントエンド：TypeScript + TailwindCSS
- UIはTypeScriptとTailwindCSSを前提にする
- UIのコンポーネント設計は`frontend/src/components/`と`frontend/src/features/`に寄せる
- Viteを使用してビルド

### リアルタイム音声処理：Deepgram
- 音声文字起こしはDeepgram WebSocket APIを使用
- 日本語対応モデルを使用
- 接続情報は`.env`で管理

### AI処理：Claude API (Anthropic)
- LLM処理はClaude API（claude-sonnet-4-20250514）を使用
- 構造化出力にはTool useまたはJSON modeを活用
- プロンプトは`backend/prompts/`にJinja2テンプレートで管理

### サーバー：Railway
- 本番デプロイはRailwayを前提にする
- 環境変数はRailway側で管理し、ローカルは`.env`で合わせる
- 詳しいコマンドは、[railway](docs/tools/railway.md)を参照

### 開発系：ruff, mypy, pytest
- `uv run ruff check . --fix && uv run ruff format .`で整形する
- `uv run mypy .`で型チェックする
- `uv run pytest`でテストする
- ruff / mypy / pytest が未導入なら`uv add --dev ruff mypy pytest`で追加する

## 3. コーディング規約
### 命名規則
- 目的が伝わる最小限の命名を優先し、曖昧な略語や1文字変数を避ける
### 構造と分割（可読性）
- ネストは浅く保つ。過剰なif分岐の入れ子はリファクタして整理する
- 1〜2行程度の極小ヘルパー関数は作らない（型変換など再利用性が明確な場合のみ許可）
- 1〜2文だけの薄いファイルは作らない（意味のある単位でまとめる）
### 変更範囲の最小化（AIによる過剰変更の抑制）
- 使っていないファイルや未参照のテンプレートは残さない
- 既存ファイルの小さな修正で済む場合、新規ファイルを増やさない
- 不要な抽象化や過剰な分割は避け、理解しやすい構成を優先する
### エラー処理と例外設計
- エラーは起こす。Noneや空リストを返して隠蔽しない
- 例外の握りつぶしは禁止。try/exceptの再スローも禁止
- tryは非同期処理に関する場合以外使用禁止
### 型とドキュメント
- 型アノテーションを原則として追加する。`pydantic`を有効活用する
- docstringを必ず追加する。クラス・関数の説明と、Args, Attributes, Returns, Raises を充実させる
### コメントとテスト表現
- 何をしているかではなく、why/why not を書く
- テストのコメントは A should / A should not / A must / A must not 形式にする

### 例
```python
def example_function(param1: int, param2: str) -> bool:
    """This function demonstrates an example.

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        flag (bool): Returns True if successful, False otherwise.
    """
    return True

class ExampleClass:
    """This class demonstrates an example.

    Attributes:
        attribute1 (int): Description of attribute1.
        attribute2 (str): Description of attribute2.
    """

    def __init__(self, attribute1: int, attribute2: str) -> None:
        self.attribute1 = attribute1
        self.attribute2 = attribute2
```

## 4. docsの活用
- `docs/`を参照・または更新しながらコードを生成してください．
- 以下は参照・作成するべきdocsの例です
    - `docs/backend-design.md`: バックエンドの設計方針
        - フォルダ構成
        - 各モジュールの役割
        - 使用技術
    - `docs/frontend-design.md`: フロントエンドの設計方針
        - フォルダ構成
        - 各モジュールの役割
        - 使用技術
    - `docs/api-examples.md`: APIの使用例
        - 各エンドポイントの使用例
        - リクエスト・レスポンスのサンプル
    - `docs/db-design.md`: DBの設計方針
        - テーブル定義
        - ER図
        - 永続化の流れ
    - `docs/ai-pipeline-design.md`: AIパイプラインの設計方針
        - 使用モデル
        - 入出力の流れ
        - プロンプト設計
    - `docs/AGENT-memo.md`: 作業途中・後任の人間やAIエージェント向けメモ
        - 変更日 (zsh -lc 'date "+%Y-%m-%d %H:%M:%S"'で取得しなさい)
        - 進捗
        - 注意点
        - TODO

## 5. プロジェクト固有の設計方針

### 水野メソッドのシステム化
このプロジェクトの核心は「水野メソッドの民主化」です。
- 4つの思考パターン（多層的情報収集、仮説駆動、リフレーミング、出口逆算）をAIに実装
- 詳細は`docs/requirements/02_mizuno_method_spec.md`を参照

### リアルタイム処理の設計
- Deepgram → FastAPI WebSocket → Claude API → クライアント
- 音声は5〜10秒バッファリングしてからClaude APIに送信
- 詳細は`docs/ai-pipeline-design.md`を参照

### 成果物生成
- ノンネーム: テキスト形式で自動生成
- IM（インフォメーションメモランダム）: python-pptxでPPTX生成
- テンプレートは`backend/templates/`に配置

## 6. ディレクトリ構成
```
TONARI-MnA/
├── .venv/
├── .env
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
├── AGENT.md                     # この開発規約
├── docs/                        # 設計・運用ドキュメント
│   ├── requirements/            # 要件定義（既存）
│   ├── backend-design.md
│   ├── frontend-design.md
│   ├── api-examples.md
│   ├── db-design.md
│   ├── ai-pipeline-design.md
│   ├── AGENT-memo.md
│   └── tools/                   # ツール別リファレンス
│       ├── supabase.md
│       └── railway.md
├── backend/                     # バックエンド (FastAPI)
│   ├── __init__.py
│   ├── main.py                  # アプリ起点
│   ├── core/                    # 設定・認証・共通ユーティリティ
│   │   ├── __init__.py
│   │   ├── config.py            # 環境変数・設定
│   │   └── auth.py              # Supabase認証
│   ├── models/                  # Pydanticスキーマ
│   │   ├── __init__.py
│   │   ├── session.py           # セッション関連
│   │   ├── extraction.py        # 抽出情報
│   │   ├── analysis.py          # 分析結果
│   │   └── suggestion.py        # サジェスト
│   ├── api/                     # ルーティング
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── projects.py
│   │   ├── sessions.py
│   │   ├── websocket.py         # WebSocketハンドラ
│   │   └── outputs.py           # 成果物生成
│   ├── services/                # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── stt.py               # Deepgram連携
│   │   ├── extraction.py        # 情報抽出
│   │   ├── analysis.py          # 構造分析
│   │   ├── suggestion.py        # サジェスト生成
│   │   ├── reframing.py         # リフレーミング
│   │   └── output.py            # ノンネーム/IM生成
│   ├── repositories/            # DBアクセス層
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── session.py
│   │   └── extraction.py
│   ├── prompts/                 # LLMプロンプト（Jinja2）
│   │   ├── extraction.j2
│   │   ├── analysis.j2
│   │   ├── suggestion.j2
│   │   ├── reframing.j2
│   │   └── output.j2
│   ├── templates/               # 成果物テンプレート
│   │   └── im_template.pptx
│   └── modules/                 # 外部連携
│       ├── __init__.py
│       ├── llm.py               # Claude API
│       └── deepgram.py          # Deepgram
├── frontend/                    # フロントエンド (TypeScript)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.ts              # エントリーポイント
│   │   ├── app/                 # 画面/ルーティング
│   │   ├── components/          # 再利用UI部品
│   │   │   ├── Header.tsx
│   │   │   ├── ConversationLog.tsx
│   │   │   ├── ExtractionPanel.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   │   └── SuggestionPanel.tsx
│   │   ├── features/            # 機能単位のUI
│   │   │   ├── session/         # 面談画面
│   │   │   ├── project/         # プロジェクト管理
│   │   │   └── output/          # 成果物
│   │   ├── hooks/               # カスタムフック
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useAudio.ts
│   │   │   └── useAuth.ts
│   │   ├── lib/                 # APIクライアント
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── stores/              # 状態管理
│   │   │   └── sessionStore.ts
│   │   ├── styles/              # グローバルスタイル
│   │   │   └── globals.css
│   │   └── types/               # 型定義
│   │       ├── api.ts
│   │       └── supabase.ts
│   └── public/                  # 静的アセット
├── tests/                       # Pythonテスト (pytest)
│   ├── __init__.py
│   ├── test_extraction.py
│   ├── test_analysis.py
│   └── test_suggestion.py
├── supabase/                    # Supabaseマイグレーション
│   └── migrations/
└── scripts/                     # 開発/運用スクリプト
    └── seed.py
```

## 7. フロント・UI/UXの条件
- 処理に時間がかかる場合は、ローディング中の表示をする
- 必須入力項目は「*」をつけ、未入力時のエラー文言を明確にする
- 削除など不可逆操作には確認画面を出す
- ダウンロードはアイコンなどで操作意図が伝わるようにする
- 主要画面は情報の優先順位を明確にし、1画面の要素密度を上げすぎない
- フォームは入力補助と即時バリデーションを入れ、失敗時の復帰が容易な導線にする
- モバイルとデスクトップの両方で崩れないレスポンシブ設計にする
- 色だけで状態を示さない。ラベル、形、アイコンで冗長化する
- アクセシビリティは最低限担保する（フォーカス、コントラスト、キーボード操作）
- UIの一貫性を最優先し、コンポーネントと余白ルールを統一する
- 画面遷移や保存成功は即時に分かるフィードバックを出す

## 8. TONARI固有のUI要件
- 面談中は会話に集中できるUIを最優先
- リアルタイム更新は視覚的に邪魔にならないように
- サジェストは「理由」を必ず表示
- 抽出進捗は一目で把握できるように
- ピン留め操作は最小限のクリックで
