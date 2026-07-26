import React from 'react';
import { LayoutDashboard, Sliders, FileText, Users, MessageSquare } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, chats, selectedChatId, setSelectedChatId }) {
  const menuItems = [
    { id: 'dashboard', label: 'Главный Дашборд', icon: LayoutDashboard },
    { id: 'settings', label: 'Настройки Чата', icon: Sliders },
    { id: 'logs', label: 'Журнал Аудита', icon: FileText },
    { id: 'users', label: 'Пользователи Чата', icon: Users },
  ];

  return (
    <aside className="w-64 bg-dark-800/60 border-r border-gray-800 p-4 flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        {/* Chat Selector */}
        <div>
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Выберите Группу / Чат
          </label>
          <div className="relative">
            <select
              value={selectedChatId || ''}
              onChange={(e) => setSelectedChatId(Number(e.target.value))}
              className="w-full bg-dark-700 border border-gray-700 text-white rounded-xl px-3 py-2.5 text-sm appearance-none focus:outline-none focus:border-blue-500 transition-colors cursor-pointer pr-8"
            >
              {chats.length === 0 ? (
                <option value="">Нет подключенных чатов</option>
              ) : (
                chats.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} ({c.username ? `@${c.username}` : c.id})
                  </option>
                ))
              )}
            </select>
            <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="space-y-1.5">
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Меню управления
          </label>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-dark-700/50'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-blue-400' : 'text-gray-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-3 bg-dark-700/40 rounded-xl border border-gray-800 text-xs text-gray-400">
        <p className="font-medium text-gray-300">Telegram SuperModer v1.0</p>
        <p className="mt-1 text-gray-400">Aiogram 3 & FastAPI</p>
      </div>
    </aside>
  );
}
