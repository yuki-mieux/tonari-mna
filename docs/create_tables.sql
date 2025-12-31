-- =====================================================
-- Tonari データベース初期化SQL
-- =====================================================
--
-- 【実行方法】
-- 1. Supabaseダッシュボードを開く
--    https://supabase.com/dashboard/project/znvfqvyhwnmwzyjkiedq
-- 2. 左メニュー「SQL Editor」をクリック
-- 3. このSQLをコピー＆ペーストして「Run」
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
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert knowledge for their customers" ON knowledge;
CREATE POLICY "Users can insert knowledge for their customers" ON knowledge
  FOR INSERT WITH CHECK (
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update knowledge for their customers" ON knowledge;
CREATE POLICY "Users can update knowledge for their customers" ON knowledge
  FOR UPDATE USING (
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can delete knowledge for their customers" ON knowledge;
CREATE POLICY "Users can delete knowledge for their customers" ON knowledge
  FOR DELETE USING (
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

-- memos テーブル
ALTER TABLE memos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view memos for their customers" ON memos;
CREATE POLICY "Users can view memos for their customers" ON memos
  FOR SELECT USING (
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert memos for their customers" ON memos;
CREATE POLICY "Users can insert memos for their customers" ON memos
  FOR INSERT WITH CHECK (
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update memos for their customers" ON memos;
CREATE POLICY "Users can update memos for their customers" ON memos
  FOR UPDATE USING (
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can delete memos for their customers" ON memos;
CREATE POLICY "Users can delete memos for their customers" ON memos
  FOR DELETE USING (
    customer_id IN (
      SELECT id FROM customers WHERE user_id = auth.uid()
    )
  );

-- =====================================================
-- 完了メッセージ
-- =====================================================
SELECT 'テーブル作成とRLSポリシー設定が完了しました' AS message;
