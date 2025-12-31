-- =====================================================
-- ユーザーのメール確認を手動で完了するSQL
-- =====================================================
-- Supabaseダッシュボード → SQL Editor で実行

-- ユーザーのメールを確認済みにする
UPDATE auth.users
SET
  email_confirmed_at = NOW(),
  confirmed_at = NOW(),
  updated_at = NOW()
WHERE email = 'yuki.t@transmieux.com';

-- 確認
SELECT id, email, email_confirmed_at, confirmed_at
FROM auth.users
WHERE email = 'yuki.t@transmieux.com';
