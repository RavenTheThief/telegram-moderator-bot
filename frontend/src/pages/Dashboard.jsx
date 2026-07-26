import React, { useEffect, useState } from 'react';
import { 
  MessageSquare, Users, UserX, AlertTriangle, Activity, ShieldAlert, Sliders, ExternalLink 
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import StatCard from '../components/StatCard';
import { chatsAPI } from '../services/api';

const COLORS = ['#3B82F6', '#EF4444', '#F59E0B', '#10B981', '#8B5CF6'];

export default function Dashboard({ chats, onSelectChat, onNavigateToSettings }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await chatsAPI.getStats();
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch dashboard stats", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-400">
        <Activity className="w-8 h-8 animate-spin mx-auto text-blue-500 mb-2" />
        Загрузка статистики...
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Подключено Чатов"
          value={stats?.total_chats || 0}
          icon={MessageSquare}
          color="blue"
          subtitle="Активные супергруппы"
        />
        <StatCard
          title="Всего Участников"
          value={stats?.total_users || 0}
          icon={Users}
          color="emerald"
          subtitle="Участники под защитой"
        />
        <StatCard
          title="Заблокировано (Banned)"
          value={stats?.total_banned_users || 0}
          icon={UserX}
          color="rose"
          subtitle="Нарушители правил"
        />
        <StatCard
          title="Выдано Предупреждений"
          value={stats?.total_warns || 0}
          icon={AlertTriangle}
          color="amber"
          subtitle="Всего предупреждений"
        />
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Area Chart */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-dark-800/60 border border-gray-800 backdrop-blur-md">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-400" />
                Активность Модерации (За 7 дней)
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">Динамика срабатывания фильтров и авто-действий</p>
            </div>
            <span className="text-xs bg-blue-500/10 text-blue-400 px-3 py-1 rounded-full border border-blue-500/20 font-semibold">
              7D Activity
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats?.activity_chart || []}>
                <defs>
                  <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#6B7280" fontSize={12} tickLine={false} />
                <YAxis stroke="#6B7280" fontSize={12} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', borderRadius: '12px', color: '#FFF' }}
                />
                <Area type="monotone" dataKey="events" name="Срабатываний" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorEvents)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Action Distribution Pie Chart */}
        <div className="p-6 rounded-2xl bg-dark-800/60 border border-gray-800 backdrop-blur-md">
          <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-purple-400" />
            Распределение Действий
          </h3>
          <p className="text-xs text-gray-400 mb-4">Типы примененных наказаний</p>

          <div className="h-64 flex items-center justify-center">
            {stats?.actions_chart?.length === 0 ? (
              <p className="text-xs text-gray-500">Нет данных для отображения</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats?.actions_chart || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {stats?.actions_chart?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', borderRadius: '12px', color: '#FFF' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Connected Chats Grid */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-emerald-400" />
          Подключенные Групповые Чаты ({chats.length})
        </h3>

        {chats.length === 0 ? (
          <div className="p-8 bg-dark-800/40 rounded-2xl border border-gray-800 text-center text-gray-400">
            <p>Добавьте бота в ваш Telegram-чат с правами администратора, чтобы он появился здесь.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {chats.map((chat) => (
              <div
                key={chat.id}
                className="p-5 rounded-2xl bg-dark-800/60 border border-gray-800 hover:border-gray-700 transition-all backdrop-blur-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-white text-base truncate max-w-[200px]">{chat.title}</h4>
                      <p className="text-xs text-gray-400 mt-0.5">{chat.username ? `@${chat.username}` : `ID: ${chat.id}`}</p>
                    </div>
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Активен
                    </span>
                  </div>

                  <div className="mt-4 pt-3 border-t border-gray-800/80 grid grid-cols-2 gap-2 text-xs text-gray-400">
                    <div>Тип: <span className="text-gray-200 capitalize">{chat.type}</span></div>
                    <div>Капча: <span className="text-blue-400">{chat.settings?.captcha_enabled ? 'Вкл' : 'Выкл'}</span></div>
                    <div>Антифлуд: <span className="text-blue-400">{chat.settings?.anti_flood_enabled ? 'Вкл' : 'Выкл'}</span></div>
                    <div>Варны: <span className="text-amber-400">До {chat.settings?.max_warns || 3}</span></div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-gray-800 flex items-center justify-between">
                  <button
                    onClick={() => {
                      onSelectChat(chat.id);
                      onNavigateToSettings();
                    }}
                    className="w-full flex items-center justify-center space-x-2 bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white px-4 py-2 rounded-xl border border-blue-500/30 text-xs font-semibold transition-all"
                  >
                    <Sliders className="w-4 h-4" />
                    <span>Управлять настройками</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
