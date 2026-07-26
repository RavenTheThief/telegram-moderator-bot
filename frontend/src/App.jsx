import React, { useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ChatSettings from './pages/ChatSettings';
import AuditLogs from './pages/AuditLogs';
import UsersManagement from './pages/UsersManagement';
import { authAPI, chatsAPI } from './services/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('RavenThief');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [chats, setChats] = useState([]);
  const [selectedChatId, setSelectedChatId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    try {
      const res = await authAPI.getMe();
      setUsername(res.data.username);
      setIsAuthenticated(true);
      await fetchChats();
    } catch (err) {
      localStorage.removeItem('token');
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchChats = async () => {
    try {
      const res = await chatsAPI.getChats();
      setChats(res.data);
      if (res.data.length > 0 && !selectedChatId) {
        setSelectedChatId(res.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load chats", err);
    }
  };

  const handleLoginSuccess = (user) => {
    setUsername(user);
    setIsAuthenticated(true);
    fetchChats();
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center text-gray-400 font-medium">
        Загрузка приложения...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-dark-900 text-slate-100 flex flex-col">
      <Navbar username={username} onLogout={handleLogout} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          chats={chats}
          selectedChatId={selectedChatId}
          setSelectedChatId={setSelectedChatId}
        />

        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && (
            <Dashboard
              chats={chats}
              onSelectChat={(id) => setSelectedChatId(id)}
              onNavigateToSettings={() => setActiveTab('settings')}
            />
          )}

          {activeTab === 'settings' && (
            <ChatSettings chatId={selectedChatId} />
          )}

          {activeTab === 'logs' && (
            <AuditLogs chatId={selectedChatId} />
          )}

          {activeTab === 'users' && (
            <UsersManagement chatId={selectedChatId} />
          )}
        </main>
      </div>
    </div>
  );
}
