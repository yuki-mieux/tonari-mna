-- =====================================================
-- Tonari データベース完全セットアップSQL
-- =====================================================
--
-- 【実行方法】
-- 1. Supabaseダッシュボードを開く
--    https://supabase.com/dashboard/project/znvfqvyhwnmwzyjkiedq
--
-- 2. 左メニュー「SQL Editor」をクリック
--
-- 3. このSQLを全てコピー＆ペーストして「Run」ボタン
--
-- =====================================================

-- =====================================================
-- STEP 1: knowledgeテーブル作成
-- =====================================================
CREATE TABLE IF NOT EXISTS knowledge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content TEXT,
  category TEXT DEFAULT 'general',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- STEP 2: memosテーブル作成
-- =====================================================
CREATE TABLE IF NOT EXISTS memos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
  summary TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- STEP 3: RLSポリシー設定
-- =====================================================

-- knowledge テーブル
ALTER TABLE knowledge ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view knowledge for their customers" ON knowledge;
CREATE POLICY "Users can view knowledge for their customers" ON knowledge
  FOR SELECT USING (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

DROP POLICY IF EXISTS "Users can insert knowledge for their customers" ON knowledge;
CREATE POLICY "Users can insert knowledge for their customers" ON knowledge
  FOR INSERT WITH CHECK (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

DROP POLICY IF EXISTS "Users can update knowledge for their customers" ON knowledge;
CREATE POLICY "Users can update knowledge for their customers" ON knowledge
  FOR UPDATE USING (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

DROP POLICY IF EXISTS "Users can delete knowledge for their customers" ON knowledge;
CREATE POLICY "Users can delete knowledge for their customers" ON knowledge
  FOR DELETE USING (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

-- memos テーブル
ALTER TABLE memos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view memos for their customers" ON memos;
CREATE POLICY "Users can view memos for their customers" ON memos
  FOR SELECT USING (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

DROP POLICY IF EXISTS "Users can insert memos for their customers" ON memos;
CREATE POLICY "Users can insert memos for their customers" ON memos
  FOR INSERT WITH CHECK (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

DROP POLICY IF EXISTS "Users can update memos for their customers" ON memos;
CREATE POLICY "Users can update memos for their customers" ON memos
  FOR UPDATE USING (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

DROP POLICY IF EXISTS "Users can delete memos for their customers" ON memos;
CREATE POLICY "Users can delete memos for their customers" ON memos
  FOR DELETE USING (
    customer_id IN (SELECT id FROM customers WHERE user_id = auth.uid())
  );

-- =====================================================
-- STEP 4: 面接チェックリスト用顧客を作成
-- =====================================================
DO $$
DECLARE
  v_user_id UUID;
  v_customer_id UUID;
BEGIN
  -- 最初のユーザーIDを取得
  SELECT id INTO v_user_id FROM auth.users LIMIT 1;

  IF v_user_id IS NULL THEN
    RAISE NOTICE 'ユーザーが存在しません。先にユーザーを作成してください。';
    RETURN;
  END IF;

  -- 面接チェックリスト用顧客を作成（既存なら取得）
  SELECT id INTO v_customer_id
  FROM customers
  WHERE name = '面接チェックリスト' AND user_id = v_user_id;

  IF v_customer_id IS NULL THEN
    INSERT INTO customers (name, description, user_id)
    VALUES ('面接チェックリスト', '全面接官共通のチェックリスト', v_user_id)
    RETURNING id INTO v_customer_id;
  END IF;

  -- =====================================================
  -- STEP 5: 面接チェックリストデータを投入
  -- =====================================================

  -- 既存データを削除（重複防止）
  DELETE FROM knowledge WHERE customer_id = v_customer_id;

  -- 必須確認項目（must_ask）
  INSERT INTO knowledge (customer_id, title, content, category) VALUES
  (v_customer_id, '退職理由の確認', '「なぜ前職を辞めた/辞めたいのですか？」必ず確認。他責傾向（会社が悪い、上司が悪い）がないか注意深く聞く。ポジティブな理由（成長したい、新しい挑戦）かネガティブな理由かを見極める。', 'must_ask'),
  (v_customer_id, '志望動機の確認', '「なぜこの業界/職種を選んだのですか？」具体性を確認。「なんとなく」「給与が良さそう」だけでは弱い。業界理解度、キャリアビジョンとの整合性をチェック。', 'must_ask'),
  (v_customer_id, '希望年収の確認', '「現在の年収と希望年収を教えてください」現年収と希望のギャップを確認。大幅アップを希望する場合は根拠を聞く。「〇〇ができるので」と具体的に言えるか。', 'must_ask'),
  (v_customer_id, '入社可能時期の確認', '「いつから入社可能ですか？」現職の引き継ぎ期間、退職交渉の状況を確認。すぐ入社できる場合は「なぜすぐ辞められるのか」も確認。', 'must_ask'),
  (v_customer_id, '転職軸の確認', '「今回の転職で最も重視することは何ですか？」優先順位を明確にしてもらう。年収・やりがい・ワークライフバランス・成長機会など、何を重視するかで紹介先が変わる。', 'must_ask'),
  (v_customer_id, '職務経歴の確認', '「これまでの経歴を簡単に教えてください」転職回数、在籍期間、役割の変遷を確認。短期離職が多い場合は理由を深掘り。', 'must_ask');

  -- 注意サイン（red_flag）
  INSERT INTO knowledge (customer_id, title, content, category) VALUES
  (v_customer_id, '前職・上司批判が多い', '前職の会社や上司への不満ばかり話す場合は要注意。次の職場でも同じパターンを繰り返す可能性が高い。「具体的にどう改善しようとしましたか？」と聞いてみる。', 'red_flag'),
  (v_customer_id, '実績が曖昧', '「頑張りました」「色々やりました」「チームで達成しました」など曖昧な表現ばかりの場合は要注意。「具体的な数字を教えてください」「あなたの役割は何でしたか」と深掘り。', 'red_flag'),
  (v_customer_id, '転職理由の矛盾', '面接の最初と後半で言っていることが違う場合は要注意。本音と建前が混在している可能性。矛盾を感じたら「先ほど〇〇とおっしゃいましたが、今の話とどう繋がりますか？」と確認。', 'red_flag'),
  (v_customer_id, '質問がない・少ない', '「何か質問はありますか？」に「特にありません」は要注意。入社意欲が低い、または情報収集力・好奇心に欠ける可能性。「本当に何もないですか？」と一度確認。', 'red_flag'),
  (v_customer_id, '年収だけを重視', '年収の話ばかりで、仕事内容や成長機会への関心が薄い場合は要注意。定着リスクが高い。「年収以外で重視することは？」と確認。', 'red_flag'),
  (v_customer_id, '他責思考が強い', '失敗や問題を全て外部要因のせいにする傾向がある場合は要注意。「そのとき、あなた自身は何ができたと思いますか？」と自己責任の視点を確認。', 'red_flag'),
  (v_customer_id, '話が長い・まとまらない', '質問に対して話が長く、結論が見えない場合は要注意。コミュニケーション能力、論理的思考力に課題がある可能性。「一言でまとめると？」と促す。', 'red_flag');

  -- 良い兆候（good_sign）
  INSERT INTO knowledge (customer_id, title, content, category) VALUES
  (v_customer_id, '具体的な数字で実績を語れる', '「売上120%達成」「3名のチームをリード」「コスト20%削減」など、具体的な数字で実績を語れる人は信頼性が高い。数字の根拠も聞いてみる。', 'good_sign'),
  (v_customer_id, '質問が的確・具体的', '「御社の〇〇事業の今後の展開は？」「チームの構成を教えてください」など、具体的で的確な質問ができる人は準備ができている証拠。入社意欲も高い。', 'good_sign'),
  (v_customer_id, '自己認識ができている', '自分の強み・弱みを客観的に語れる人は成長意欲が高い。「弱みをどう克服しようとしていますか？」と聞いてみる。', 'good_sign'),
  (v_customer_id, '転職軸と志望動機が一貫', '転職で重視することと、この会社を選んだ理由が整合している人は本気度が高い。ミスマッチも起きにくい。', 'good_sign'),
  (v_customer_id, '失敗から学んだ経験を語れる', '過去の失敗を隠さず、そこから何を学んだかを語れる人は成長力がある。「その経験を今後どう活かしますか？」と聞く。', 'good_sign'),
  (v_customer_id, 'STAR形式で回答できる', 'Situation（状況）、Task（課題）、Action（行動）、Result（結果）の流れで話せる人は論理的で信頼性が高い。', 'good_sign');

  -- 面接テクニック（tip）
  INSERT INTO knowledge (customer_id, title, content, category) VALUES
  (v_customer_id, '沈黙を恐れない', '候補者が考えている時間は待つ。急かさない。沈黙は候補者が本音を整理している時間かもしれない。5秒程度は待ってみる。', 'tip'),
  (v_customer_id, 'なぜを3回重ねる', '表面的な回答には「なぜそう思いましたか？」「なぜその選択をしたのですか？」を重ねる。3回目あたりで本音が出てくることが多い。', 'tip'),
  (v_customer_id, '具体化を促す', '曖昧な回答には「例えば？」「具体的には？」で掘り下げる。具体例が出てこない場合は経験が浅いか、話を盛っている可能性。', 'tip'),
  (v_customer_id, '最後に本音を引き出す', '面接の最後に「最後に何か聞いておきたいことはありますか？」と聞く。緊張がほぐれた状態で本音が出やすい。', 'tip'),
  (v_customer_id, '行動ベースで聞く', '「どう思いますか？」ではなく「実際にどうしましたか？」と行動ベースで聞く。思考より行動の方が嘘をつきにくい。', 'tip'),
  (v_customer_id, 'オープンクエスチョンを使う', '「はい/いいえ」で答えられる質問より、「〜について教えてください」と自由に話してもらう質問を多用する。', 'tip'),
  (v_customer_id, '相手の言葉を繰り返す', '候補者の言葉を繰り返すことで「ちゃんと聞いている」と伝わり、信頼関係が築ける。「〇〇ということですね」と確認しながら進める。', 'tip');

  RAISE NOTICE '✅ セットアップ完了！';
  RAISE NOTICE '  - 顧客ID: %', v_customer_id;
  RAISE NOTICE '  - ナレッジ件数: 26件';
END $$;

-- =====================================================
-- 確認
-- =====================================================
SELECT
  c.name AS customer_name,
  COUNT(k.id) AS knowledge_count
FROM customers c
LEFT JOIN knowledge k ON k.customer_id = c.id
GROUP BY c.id, c.name
ORDER BY c.name;
