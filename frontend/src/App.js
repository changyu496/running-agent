import React, { useState, useEffect } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { loadApiConfig, isLoggedIn } from './services/api';
import Layout from './components/Layout';
import Login from './pages/Login';
import Home from './pages/Home';
import MemoAnalysis from './pages/MemoAnalysis';
import VideoAnalysis from './pages/VideoAnalysis';
import Records from './pages/Records';
import RecordDetail from './pages/RecordDetail';
import Stats from './pages/Stats';
import Guidance from './pages/Guidance';

function App() {
  const [configReady, setConfigReady] = useState(false);
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  useEffect(() => {
    loadApiConfig()
      .then(() => setConfigReady(true))
      .catch(() => setConfigReady(true)); // 失败时仍继续，使用默认 localhost
  }, []);

  useEffect(() => {
    const onLogout = () => setLoggedIn(false);
    window.addEventListener('auth:logout', onLogout);
    return () => window.removeEventListener('auth:logout', onLogout);
  }, []);

  if (!configReady) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'system-ui' }}>
        加载中...
      </div>
    );
  }

  if (!loggedIn) {
    return <Login onSuccess={() => setLoggedIn(true)} />;
  }

  return (
    <Router>
      <Layout onLogout={() => setLoggedIn(false)}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/memo" element={<MemoAnalysis />} />
          <Route path="/video" element={<VideoAnalysis />} />
          <Route path="/records" element={<Records />} />
          <Route path="/records/:id" element={<RecordDetail />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/guidance" element={<Guidance />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
