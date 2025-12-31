/**
 * TONARI for M&A - メインアプリケーション
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Dashboard } from './app/Dashboard';
import { Session } from './app/Session';
import { Layout } from './app/Layout';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="session/:sessionId" element={<Session />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
