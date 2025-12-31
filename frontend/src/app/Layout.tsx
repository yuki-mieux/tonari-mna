/**
 * 共通レイアウト
 */
import { Outlet, Link } from 'react-router-dom';

export function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* ロゴ */}
            <Link to="/" className="flex items-center">
              <span className="text-xl font-bold text-primary-600">TONARI</span>
              <span className="ml-2 text-sm text-gray-500">for M&A</span>
            </Link>

            {/* ナビゲーション */}
            <nav className="flex items-center gap-4">
              <Link
                to="/"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                ダッシュボード
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main>
        <Outlet />
      </main>
    </div>
  );
}
