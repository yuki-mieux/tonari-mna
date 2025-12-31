# Tonari v2 変更履歴

## 2025-12-13: 面接官支援特化リファクタリング

### 概要

汎用会話支援AIから、**人材紹介会社の面接官支援に特化**したプロダクトへピボット。

### ステータス

| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 1 | コードリファクタリング | ✅ 完了 |
| Phase 2 | AIプロンプト最適化 | ✅ 完了（コード変更済み） |
| Phase 3 | 初期ナレッジデータ | ⚠️ SQL作成済み・**投入未実行** |
| Phase 4 | DBスキーマ変更 | ❌ 未実行（計画のみ） |
| Phase 5 | フロントエンドUI刷新 | ✅ 完了 |

---

## Phase 1: コードリファクタリング ✅ 完了

### バックエンド構造変更

| Before | After | 理由 |
|--------|-------|------|
| `services/knowledge_manager.py` | 削除 | 重複 |
| `services/supabase_knowledge_manager.py` | 削除 | 未使用 |
| - | `services/knowledge.py` | 2ファイルを統合 |
| `dependencies.py` | 削除 | core/に移動 |
| - | `core/__init__.py` | 新規作成 |
| - | `core/auth.py` | 認証ロジックを分離 |
| - | `core/config.py` | 環境変数を一元管理 |

### 削除したデッドコード

- `customers.py`: 存在しない `_customer_dir()` メソッドを呼ぶコード100行以上を削除

### 新ディレクトリ構成

```
backend/app/
├── api/
│   ├── advice.py        # 面接アドバイス生成
│   └── customers.py     # 求職者・ナレッジ管理
├── core/                # ← 新規追加
│   ├── __init__.py
│   ├── auth.py          # JWT認証
│   └── config.py        # 設定管理
├── models/
│   └── schemas.py
├── services/
│   ├── agent.py         # AIエージェント
│   └── knowledge.py     # ← 統合後
└── main.py
```

---

## Phase 2: AIプロンプト最適化（面接特化） ✅ 完了

### システムプロンプト変更

**Before（汎用）:**
```
あなたは優秀な会話アシスタントです。
会話をリアルタイムで分析し、ユーザーに的確なアドバイスを提供します。
```

**After（面接特化）:**
```
あなたは人材紹介会社のベテラン面接官の相棒です。
面接をリアルタイムで分析し、面接官がより良い判断を下せるよう支援します。

## あなたの役割（優先度順）
1. 矛盾検知: 求職者の発言の一貫性をチェック
2. 確認漏れアラート: まだ聞いていない重要項目を提示
3. 深掘り提案: 曖昧な回答に対する追加質問を提案
4. 良いサイン/注意サインの指摘

## 絶対にやらないこと
- 合否判断をしない（責任は常に人間）
- 感情的な評価をしない
- 長文で説明しない
```

### 出力フォーマット変更

**Before:**
```
自由形式のアドバイス文
```

**After:**
```
【気づき】1-2文で最も重要な指摘
【確認推奨】まだ聞いていない重要な質問
【深掘り案】「〇〇について、もう少し詳しく教えてください」
```

### ツール定義変更

| Before | After | 用途 |
|--------|-------|------|
| `get_customer_info` | `get_candidate_info` | 求職者情報取得 |
| `get_customer_needs` | 削除 | 不要 |
| - | `get_checklist` | 面接チェックリスト参照 |
| `get_past_meetings` | `get_past_interviews` | 過去の面接記録 |
| `search_knowledge` | `search_knowledge` | 変更なし |

### クラス名変更

| Before | After |
|--------|-------|
| `HireMateAgent` | `InterviewAgent` |

---

## Phase 3: 初期ナレッジデータ ⚠️ SQL作成済み・投入未実行

`docs/seed_interview_checklist.sql` を作成。

### カテゴリ設計

| category | 用途 | 件数 |
|----------|------|------|
| `must_ask` | 必須確認項目 | 6件 |
| `red_flag` | 注意サイン | 7件 |
| `good_sign` | 良い兆候 | 6件 |
| `tip` | 面接テクニック | 7件 |

### 初期データ例

**必須確認（must_ask）:**
- 退職理由の確認
- 志望動機の確認
- 希望年収の確認
- 入社可能時期の確認
- 転職軸の確認
- 職務経歴の確認

**注意サイン（red_flag）:**
- 前職・上司批判が多い
- 実績が曖昧
- 転職理由の矛盾
- 質問がない・少ない
- 年収だけを重視
- 他責思考が強い
- 話が長い・まとまらない

**良い兆候（good_sign）:**
- 具体的な数字で実績を語れる
- 質問が的確・具体的
- 自己認識ができている
- 転職軸と志望動機が一貫
- 失敗から学んだ経験を語れる
- STAR形式で回答できる

**テクニック（tip）:**
- 沈黙を恐れない
- なぜを3回重ねる
- 具体化を促す
- 最後に本音を引き出す
- 行動ベースで聞く
- オープンクエスチョンを使う
- 相手の言葉を繰り返す

---

## Phase 4: DBスキーマ変更 ❌ 未実行（計画のみ）

現状のテーブル名（customers, knowledge, memos）は維持。
将来的に以下へリネームを検討：

| 現在 | 提案 |
|------|------|
| customers | candidates |
| knowledge | interview_checklist |
| memos | interview_records |

## Phase 5: フロントエンドUI刷新 ✅ 完了

### カラースキーム変更

| Before | After |
|--------|-------|
| クリーム/オレンジ系 | 白基調/ブルーアクセント（Apple風） |

### アイコン → テキストラベル（AI感排除）

| Before | After |
|--------|-------|
| 🧠 Tonari | Tonari |
| 🎙️ | 対面 |
| 🖥️ | 画面 |
| ⏹️ | 停止 |
| ⚙️ | 設定 |
| 📝 Live Transcript | 文字起こし |
| 📁 フォルダ | チェックリスト |
| 👥 顧客 | 求職者 |
| 🙋 自分 / 👤 相手 | 自分 / 相手 |

### 英語 → 日本語

| Before | After |
|--------|-------|
| Live | 面接 |
| AI Partner | サポート |
| STANDBY | 待機中 |
| LISTENING | 録音中 |
| STOPPED | 停止 |

### 用語変更

| Before | After |
|--------|-------|
| 顧客 | 求職者 |
| ナレッジ / 知識 | 準備 / チェックリスト |
| メモ | 面接記録 |

### MVP簡略化（削除した機能）

- AIモード切替（常時/質問時）→ 常時のみに統一
- プロンプト編集モーダル → コメントアウト
- モード選択（営業補佐/採用補佐/壁打ち/カスタム）→ 削除

### 変更ファイル

- `public/index.html` - HTML構造・ラベル変更
- `public/styles.css` - カラースキーム変更
- `public/app.js` - ステータステキスト・話者ラベル日本語化
- `CLAUDE.md` - プロダクトビジョン追加
- `docs/PIVOT_2025-12-13.md` - ピボット記録（新規作成）

---

## ファイル変更一覧

### 変更

- `backend/app/services/agent.py` - 面接特化プロンプト・ツール
- `backend/app/api/advice.py` - クラス名変更対応
- `backend/app/api/customers.py` - デッドコード削除
- `backend/app/main.py` - インポート更新
- `CLAUDE.md` - プロダクトビジョン追記
- `README.md` - 開発思想追記

### 新規作成

- `backend/app/core/__init__.py`
- `backend/app/core/auth.py`
- `backend/app/core/config.py`
- `backend/app/services/knowledge.py`
- `docs/seed_interview_checklist.sql`
- `docs/CHANGELOG_v2.md`（このファイル）

### 削除

- `backend/app/dependencies.py`
- `backend/app/services/knowledge_manager.py`
- `backend/app/services/supabase_knowledge_manager.py`

---

## 動作確認

```bash
# サーバー起動
cd /Users/yukitransmieux/Desktop/Claude\ Code/TONARI
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload --port 8000

# ブラウザでアクセス
open http://localhost:8000/app
```

---

最終更新: 2025-12-13
