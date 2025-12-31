# 水野メソッド システム化仕様書

## 1. 概要

本ドキュメントは、水野さんのM&Aヒアリング手法（水野メソッド）をシステムとして再現するための技術仕様を定義する。

---

## 2. 水野メソッドの構成要素

### 2.1 4つのコアコンポーネント

```
┌─────────────────────────────────────────────────────────┐
│                   水野メソッド                          │
├─────────────┬─────────────┬─────────────┬──────────────┤
│  多層的     │  仮説駆動型  │  リフレー   │  出口から    │
│  情報収集   │  ヒアリング  │  ミング     │  逆算        │
├─────────────┼─────────────┼─────────────┼──────────────┤
│ 4レイヤー   │ 仮説→検証   │ ネガ→ポジ  │ 買い手起点   │
│ 同時観察    │ サイクル    │ 変換       │ 情報収集     │
└─────────────┴─────────────┴─────────────┴──────────────┘
```

---

## 3. 多層的情報収集エンジン

### 3.1 4レイヤーモデル

| レイヤー | 定義 | 取得情報例 | 質問パターン |
|----------|------|-----------|--------------|
| L1: 表層 | 客観的事実・数値 | 売上、従業員数、業種 | 「〇〇は何名ですか？」 |
| L2: 構造 | 事業が成り立つ仕組み | 取引構造、収益モデル | 「なぜ〇〇なのですか？」 |
| L3: 本質 | 会社の真の価値 | 技術力、顧客基盤、人材 | 「御社の強みは何ですか？」 |
| L4: 出口 | 買い手にとっての価値 | シナジー、参入障壁 | 「どんな会社と相性が良いと思いますか？」 |

### 3.2 レイヤー判定ロジック

```python
def classify_layer(extracted_info: dict) -> str:
    """
    抽出情報をレイヤーに分類する
    """
    L1_KEYWORDS = ["売上", "従業員", "設立", "資本金", "拠点"]
    L2_KEYWORDS = ["取引先", "仕入", "原価", "なぜ", "理由", "仕組み"]
    L3_KEYWORDS = ["強み", "特徴", "技術", "ノウハウ", "差別化"]
    L4_KEYWORDS = ["買い手", "シナジー", "相性", "メリット", "統合"]

    # キーワードマッチングでレイヤー判定
    # 複数レイヤーに該当する場合は最も深いレイヤーを返す
```

### 3.3 レイヤーバランス分析

各MTGでのレイヤー別情報取得率を可視化：

```
L1: ████████████████████ 90%  ← 十分
L2: ████████████░░░░░░░░ 60%  ← 要深掘り
L3: ████████░░░░░░░░░░░░ 40%  ← 要深掘り
L4: ████░░░░░░░░░░░░░░░░ 20%  ← 重点確認
```

---

## 4. 仮説駆動型ヒアリングエンジン

### 4.1 仮説生成ロジック

```python
class HypothesisEngine:
    """
    収集情報から仮説を生成し、検証質問を提案する
    """

    def generate_hypothesis(self, extracted_info: dict) -> list[Hypothesis]:
        """
        パターンマッチングによる仮説生成

        例：
        - 建設業 × 30年 × 15名 → 「安定した下請け基盤を持つ可能性」
        - 売上横ばい × 利益増 → 「選択と集中が進んでいる可能性」
        - 後継者不在 × 60代社長 → 「事業承継ニーズが顕在化している」
        """

    def generate_verification_question(self, hypothesis: Hypothesis) -> str:
        """
        仮説を検証するための質問を生成

        例：
        仮説「安定した下請け基盤」
        → 「主要取引先との取引年数を教えていただけますか？」
        """
```

### 4.2 仮説パターンライブラリ

| トリガー条件 | 生成される仮説 | 検証質問 |
|-------------|---------------|----------|
| 建設業 × 30年以上 | 安定した顧客基盤・技術蓄積 | 「主要取引先との取引年数は？」 |
| 製造業 × 高利益率 | 独自技術・参入障壁あり | 「競合と比べた御社の強みは？」 |
| 売上減少 × 利益維持 | 不採算事業の整理 | 「この数年で事業の見直しは？」 |
| 従業員10名以下 × 高売上 | 社長依存度が高い | 「社長がいなくても回る業務は？」 |
| 地方 × 許認可業種 | エリア独占の可能性 | 「同エリアの競合状況は？」 |

### 4.3 仮説の状態管理

```typescript
interface Hypothesis {
  id: string;
  content: string;           // 仮説内容
  confidence: number;        // 確信度 (0-1)
  status: 'pending' | 'verified' | 'rejected' | 'modified';
  supporting_evidence: string[];   // 支持する発言
  contradicting_evidence: string[]; // 矛盾する発言
  verification_questions: string[]; // 検証質問
}
```

---

## 5. リフレーミングエンジン

### 5.1 ネガティブワード検知

```python
NEGATIVE_PATTERNS = {
    "債務超過": {
        "reframe": "実質純資産の確認が必要",
        "questions": [
            "役員借入金はどのくらいありますか？",
            "含み益のある資産はありますか？"
        ],
        "potential_positive": "役員借入金を除けば実質プラスの可能性"
    },
    "赤字": {
        "reframe": "一時的要因か構造的要因かの確認",
        "questions": [
            "赤字の主な要因は何ですか？",
            "その要因は一時的なものですか？"
        ],
        "potential_positive": "一時的要因なら正常収益力は異なる可能性"
    },
    "後継者不在": {
        "reframe": "事業承継の明確なニーズ",
        "questions": [
            "従業員の方での承継は検討されましたか？",
            "第三者承継のご意向は？"
        ],
        "potential_positive": "売却意思が明確で交渉がスムーズな可能性"
    },
    "売上減少": {
        "reframe": "選択と集中の可能性",
        "questions": [
            "減少の主な理由は？",
            "利益率はどう推移していますか？"
        ],
        "potential_positive": "不採算事業の整理で収益体質改善の可能性"
    },
    "高齢化": {
        "reframe": "技術・ノウハウの蓄積",
        "questions": [
            "ベテラン従業員の持つ技術は？",
            "技術承継の仕組みはありますか？"
        ],
        "potential_positive": "長年の経験に基づく技術力・顧客関係"
    }
}
```

### 5.2 リフレーミング表示ロジック

```typescript
interface ReframingSuggestion {
  trigger_phrase: string;      // 検知されたネガティブワード
  original_context: string;    // 元の文脈
  reframe_perspective: string; // 別の見方
  verification_questions: string[]; // 確認すべき質問
  potential_positive: string;  // ポジティブに転換できる可能性
}

// 表示例
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 💡 リフレーミング提案
// ───────────────────────────────
// 検知: 「債務超過」
//
// 別の見方:
// 役員借入金を除けば実質純資産プラスの
// 可能性があります。
//
// 確認してみては？
// 「役員借入金はどのくらいありますか？」
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 6. 出口逆算エンジン

### 6.1 買い手類型の定義

```typescript
enum BuyerType {
  SAME_INDUSTRY_EXPANSION = "同業他社（エリア拡大）",
  SAME_INDUSTRY_SHARE = "同業他社（シェア拡大）",
  VERTICAL_INTEGRATION = "川上・川下統合",
  NEW_MARKET_ENTRY = "異業種参入",
  PE_FUND = "PEファンド",
  INDIVIDUAL = "個人（サーチファンド等）",
  EMPLOYEE = "従業員承継（MBO）"
}
```

### 6.2 買い手像推論ロジック

```python
def infer_buyer_types(extracted_info: dict) -> list[BuyerProfile]:
    """
    収集情報から想定買い手を推論

    ロジック:
    1. 業種 → 関連する買い手類型を抽出
    2. 規模 → 適合する買い手サイズを推定
    3. 地域 → エリア拡大ニーズのある企業を想定
    4. 強み → シナジーが見込める業種を推定
    """

    buyer_profiles = []

    # 例: 建設業 × 地方 × 安定収益
    if info["industry"] == "建設業" and info["location"] == "地方":
        buyer_profiles.append(BuyerProfile(
            type=BuyerType.SAME_INDUSTRY_EXPANSION,
            description="都市部の建設会社で地方進出を狙う企業",
            synergy="地方の顧客基盤・許認可の取得",
            key_info_needed=["主要取引先", "保有許認可", "施工実績"]
        ))

    return buyer_profiles
```

### 6.3 買い手起点の情報要求

```typescript
interface BuyerInfoRequirement {
  buyer_type: BuyerType;
  required_info: string[];      // 必須情報
  nice_to_have_info: string[];  // あれば良い情報
  deal_breaker: string[];       // これがNGだと見送る情報
}

// 例: 同業他社（エリア拡大）の場合
const requirement: BuyerInfoRequirement = {
  buyer_type: BuyerType.SAME_INDUSTRY_EXPANSION,
  required_info: [
    "対応可能な施工エリア",
    "主要取引先リスト",
    "保有許認可一覧",
    "技術者の資格・人数"
  ],
  nice_to_have_info: [
    "受注残高",
    "リピート率",
    "元請/下請比率"
  ],
  deal_breaker: [
    "重大な法令違反履歴",
    "主要取引先との契約終了予定"
  ]
};
```

---

## 7. サジェスト生成アルゴリズム

### 7.1 優先度計算

```python
def calculate_suggestion_priority(
    info_gap: list[str],           # 未取得情報
    hypothesis: list[Hypothesis],   # 現在の仮説
    buyer_requirements: list[str],  # 買い手が求める情報
    conversation_context: str       # 直近の会話文脈
) -> list[ScoredSuggestion]:
    """
    サジェストの優先度を計算

    スコアリング要素:
    1. 情報の重要度（必須 > あれば良い）
    2. 仮説検証への寄与度
    3. 買い手起点の重要度
    4. 会話の流れへの自然さ
    5. 取得タイミング（早めに聞くべき vs 後半で聞くべき）
    """

    suggestions = []

    for gap in info_gap:
        score = 0

        # 重要度スコア
        if gap in REQUIRED_INFO:
            score += 50
        elif gap in NICE_TO_HAVE_INFO:
            score += 20

        # 仮説検証スコア
        for h in hypothesis:
            if gap in h.verification_questions:
                score += 30 * h.confidence

        # 買い手起点スコア
        if gap in buyer_requirements:
            score += 40

        # 文脈自然さスコア（直近の話題との関連度）
        context_relevance = calculate_context_relevance(gap, conversation_context)
        score += 20 * context_relevance

        suggestions.append(ScoredSuggestion(
            info=gap,
            score=score,
            question=generate_question(gap, conversation_context),
            reason=generate_reason(gap, hypothesis, buyer_requirements)
        ))

    return sorted(suggestions, key=lambda x: x.score, reverse=True)
```

### 7.2 質問生成テンプレート

```python
QUESTION_TEMPLATES = {
    "売上高": {
        "direct": "直近の売上高を教えていただけますか？",
        "contextual": "先ほどの{context}に関連して、売上規模感を教えていただけますか？",
        "soft": "事業規模のイメージを掴みたいのですが、売上はどのくらいでしょうか？"
    },
    "従業員数": {
        "direct": "従業員の方は何名いらっしゃいますか？",
        "contextual": "{context}を担当されている方は何名くらいですか？",
        "soft": "組織の規模感として、何名体制でしょうか？"
    },
    "譲渡理由": {
        "direct": "今回、譲渡をお考えになった理由を教えていただけますか？",
        "contextual": "先ほど{context}とおっしゃっていましたが、それが今回のご決断に？",
        "soft": "差し支えなければ、今回のご相談の背景をお聞かせいただけますか？"
    }
    # ... 他の項目も同様
}
```

### 7.3 理由生成ロジック

```python
def generate_reason(
    info: str,
    hypothesis: list[Hypothesis],
    buyer_requirements: list[str]
) -> str:
    """
    「なぜこの質問が必要か」の理由を生成
    """
    reasons = []

    # 仮説検証の観点
    for h in hypothesis:
        if info in h.verification_questions:
            reasons.append(f"「{h.content}」の確認のため")

    # 買い手起点の観点
    if info in buyer_requirements:
        reasons.append("想定買い手が重視する情報")

    # 成果物作成の観点
    if info in IM_REQUIRED_FIELDS:
        reasons.append("IM作成の必須項目")

    return "・".join(reasons) if reasons else "基本情報として重要"
```

---

## 8. プロンプト設計

### 8.1 情報抽出プロンプト

```markdown
あなたはM&Aアドバイザーのアシスタントです。
以下の会話から、M&A検討に必要な情報を抽出してください。

## 抽出対象
- 基本情報（会社名、所在地、業種、設立年、従業員数）
- 財務情報（売上、利益、資産）
- 事業情報（事業内容、取引先、強み）
- 組織情報（組織体制、キーパーソン、後継者）
- 譲渡情報（理由、希望価格、時期）

## 出力形式
JSON形式で、各項目について以下を出力：
- value: 抽出した値（不明な場合はnull）
- confidence: 確信度（0.0-1.0）
- source: 根拠となる発言（引用）

## 会話
{conversation_text}
```

### 8.2 構造分析プロンプト

```markdown
あなたは経験豊富なM&Aアドバイザーです。
以下の企業情報から、この会社の事業構造と本質的な価値を分析してください。

## 企業情報
{extracted_info}

## 分析観点
1. 事業が成り立っている構造（なぜこの事業で利益が出ているか）
2. 競合優位性（他社にない強み）
3. リスク要因（買い手が懸念しそうな点）
4. 隠れた価値（表面的には見えにくい強み）

## 出力形式
各観点について、根拠とともに簡潔に分析結果を記述。
```

### 8.3 買い手像生成プロンプト

```markdown
あなたはM&Aマッチングの専門家です。
以下の企業情報から、この会社を買収したい企業像を推論してください。

## 売り手企業情報
{extracted_info}

## 推論すべき買い手類型
1. 同業他社（エリア拡大・シェア拡大）
2. 川上・川下統合を狙う企業
3. 異業種からの参入企業
4. PEファンド
5. 個人（サーチファンド等）

## 各類型について出力
- 適合度（高/中/低）
- 想定される具体的な企業像
- シナジー仮説
- この買い手が重視する情報

## 企業情報
{extracted_info}
```

---

## 9. 学習・改善サイクル

### 9.1 フィードバックループ

```
ユーザー行動 → システム学習 → 精度向上
     │
     ├── サジェスト採用率
     ├── 質問のカスタマイズ内容
     ├── 成果物の手動修正箇所
     └── MTG後の振り返りコメント
```

### 9.2 パターン蓄積

成功した案件から以下を蓄積：
- 業種別のヒアリングパターン
- 買い手マッチングの成功パターン
- 効果的だった質問フレーズ
- リフレーミングの成功事例

これらを水野メソッドのナレッジベースとして蓄積し、システムの精度を継続的に向上させる。
