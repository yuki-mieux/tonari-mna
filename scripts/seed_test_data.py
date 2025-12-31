"""
テスト株式会社用のseedデータを投入するスクリプト
"""
from supabase import create_client

# Supabase設定
SUPABASE_URL = "https://lwwimcjuqctssjcxmyaj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3d2ltY2p1cWN0c3NqY3hteWFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUzNzA2NjMsImV4cCI6MjA4MDk0NjY2M30.fi2oLyUQ3rPXUyz4877dXQb9a2m_jubUoYCxjbvh2xQ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# テスト株式会社のIDを取得
result = supabase.table("customers").select("id").eq("name", "テスト株式会社").execute()
if not result.data:
    print("テスト株式会社が見つかりません")
    exit(1)

customer_id = result.data[0]["id"]
print(f"顧客ID: {customer_id}")

# Seedデータ
seed_knowledge = [
    {
        "customer_id": customer_id,
        "title": "会社概要",
        "content": """# テスト株式会社 会社概要

## 基本情報
- 設立: 2015年4月
- 従業員数: 150名
- 本社: 東京都渋谷区
- 事業: BtoB SaaSプロダクト開発・販売

## 主要製品
- CloudManager Pro: クラウドインフラ管理ツール
- DataSync Enterprise: データ連携プラットフォーム

## 経営陣
- 代表取締役: 山田太郎
- CTO: 佐藤花子
- 営業部長: 鈴木一郎""",
        "category": "basic_info"
    },
    {
        "customer_id": customer_id,
        "title": "課題・ニーズ",
        "content": """# テスト株式会社の課題・ニーズ

## 現状の課題
1. **営業効率の低下**
   - 営業担当が手動でレポートを作成している
   - 顧客情報が散在していて検索に時間がかかる

2. **社内コミュニケーション**
   - 部門間の情報共有が不十分
   - リモートワーク下でのコラボレーションに課題

3. **データ活用**
   - 蓄積されたデータを活用できていない
   - 分析基盤が整っていない

## 優先度の高いニーズ
- 営業活動の自動化・効率化
- AIを活用した業務改善
- 社員のAIリテラシー向上""",
        "category": "basic_info"
    },
    {
        "customer_id": customer_id,
        "title": "過去の商談メモ（2024年11月）",
        "content": """# 2024年11月15日 商談メモ

## 参加者
- 先方: 鈴木部長、田中課長
- 当社: 岡本

## 議題
AI研修プログラムの提案

## 主なやり取り
- 鈴木部長「社員のAIスキルにばらつきがある。底上げしたい」
- 田中課長「特に営業部門でChatGPTをもっと活用したい」
- 予算は年間500万円程度を想定
- 来年1月からのトライアル研修を希望

## Next Action
- トライアル研修の提案書を作成
- 1月開始で10名規模のプログラムを提案""",
        "category": "minutes"
    },
    {
        "customer_id": customer_id,
        "title": "競合情報",
        "content": """# 競合情報

## 検討中の他社サービス
1. **A社のAI研修**
   - 価格: 月額10万円/10名
   - 特徴: オンライン完結型
   - 弱点: カスタマイズ性が低い

2. **B社のDXコンサル**
   - 価格: 年間1000万円〜
   - 特徴: 手厚いサポート
   - 弱点: 高コスト

## 当社の差別化ポイント
- 実践的なワークショップ形式
- 業界特化のカリキュラム
- 助成金活用で実質コスト削減""",
        "category": "data"
    },
    {
        "customer_id": customer_id,
        "title": "キーパーソン情報",
        "content": """# キーパーソン情報

## 鈴木一郎（営業部長）
- 決裁権限: 500万円まで
- 関心事: 営業チームの生産性向上
- 性格: 数字重視、ROIを気にする
- 趣味: ゴルフ（ハンデ15）

## 田中美咲（営業課長）
- 役割: 現場のとりまとめ
- 関心事: 部下の育成、働き方改革
- 性格: 慎重派、事例を重視
- よく使うフレーズ:「他社さんの事例は？」

## 山田社長
- 最終決裁者
- IT投資には積極的
- DX推進を経営方針として掲げている""",
        "category": "basic_info"
    }
]

# 既存のknowledgeを確認
existing = supabase.table("knowledge").select("title").eq("customer_id", customer_id).execute()
existing_titles = [k["title"] for k in existing.data] if existing.data else []

# Seedデータを投入
for item in seed_knowledge:
    if item["title"] in existing_titles:
        print(f"スキップ（既存）: {item['title']}")
        continue

    result = supabase.table("knowledge").insert(item).execute()
    if result.data:
        print(f"追加: {item['title']}")
    else:
        print(f"エラー: {item['title']}")

print("\n完了！")
