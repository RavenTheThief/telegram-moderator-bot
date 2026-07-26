import React, { useEffect, useState } from 'react';
import { Users, AlertTriangle, ShieldOff, CheckCircle2, UserCheck, Search, RefreshCw } from 'lucide-react';
import { usersAPI } from '../services/api';

export default function UsersManagement({ chatId }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionMessage, setActionMessage] = useState('');

  useEffect(() => {
    if (chatId) {
      fetchUsers();
    }
  }, [chatId]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await usersAPI.getChatUsers(chatId);
      setUsers(res.data);
    } catch (err) {
      console.error("Failed to fetch users", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUnwarn = async (userId) => {
    try {
      await usersAPI.unwarnUser(chatId, userId);
      showMessage("Предупреждения сброшены!");
      fetchUsers();
    } catch (err) {
      alert("Ошибка при снятии варнов");
    }
  };

  const handleUnmute = async (userId) => {
    try {
      await usersAPI.unmuteUser(chatId, userId);
      showMessage("Мут успешно снят!");
      fetchUsers();
    } catch (err) {
      alert("Ошибка при снятии мута");
    }
  };

  const handleUnban = async (userId) => {
    try {
      await usersAPI.unbanUser(chatId, userId);
      showMessage("Пользователь успешно разбанен!");
      fetchUsers();
    } catch (err) {
      alert("Ошибка при снятии бана");
    }
  };

  const showMessage = (msg) => {
    setActionMessage(msg);
    setTimeout(() => setActionMessage(''), 3000);
  };

  const filteredUsers = users.filter((u) => {
    const term = searchTerm.toLowerCase();
    const fullname = `${u.first_name || ''} ${u.last_name || ''}`.toLowerCase();
    return (
      fullname.includes(term) ||
      (u.username && u.username.toLowerCase().includes(term)) ||
      String(u.id).includes(term)
    );
  });

  if (!chatId) {
    return (
      <div className="p-12 text-center text-gray-400 bg-dark-800/40 rounded-2xl border border-gray-800">
        Пожалуйста, выберите чат из меню слева для управления пользователями.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-400" />
            Управление Пользователями Чата
          </h2>
          <p className="text-xs text-gray-400">Просмотр и снятие наказаний напрямую из веб-панели</p>
        </div>

        <button
          onClick={fetchUsers}
          className="flex items-center space-x-1.5 bg-dark-700 hover:bg-dark-600 text-gray-300 px-3.5 py-2 rounded-xl text-xs font-semibold border border-gray-700 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Обновить</span>
        </button>
      </div>

      {actionMessage && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center space-x-3 text-emerald-400 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Поиск участника по имени, username или Telegram ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-dark-800/80 border border-gray-800 text-white rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Users Table */}
      <div className="bg-dark-800/60 border border-gray-800 rounded-2xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка списка пользователей...</div>
        ) : filteredUsers.length === 0 ? (
          <div className="p-12 text-center text-gray-400">Участники не найдены</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-dark-700/50 text-xs font-semibold text-gray-400 uppercase border-b border-gray-800">
                <tr>
                  <th className="px-6 py-3.5">Пользователь</th>
                  <th className="px-6 py-3.5">Статус</th>
                  <th className="px-6 py-3.5">Предупреждения</th>
                  <th className="px-6 py-3.5 text-right">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/80">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-dark-700/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-white">
                        {u.first_name} {u.last_name || ''}
                      </div>
                      <div className="text-xs text-gray-400 font-mono">
                        {u.username ? `@${u.username}` : `ID: ${u.id}`}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {u.is_banned ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          Забанен
                        </span>
                      ) : u.is_restricted ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          Замучен
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Активен
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-1.5">
                        <AlertTriangle className={`w-4 h-4 ${u.warns_count > 0 ? 'text-amber-400' : 'text-gray-600'}`} />
                        <span className={`font-bold text-sm ${u.warns_count > 0 ? 'text-amber-400' : 'text-gray-400'}`}>
                          {u.warns_count}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right space-x-2 whitespace-nowrap">
                      {u.warns_count > 0 && (
                        <button
                          onClick={() => handleUnwarn(u.id)}
                          className="px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-semibold transition-colors"
                          title="Сбросить предупреждения"
                        >
                          Снять варны
                        </button>
                      )}
                      {u.is_restricted && (
                        <button
                          onClick={() => handleUnmute(u.id)}
                          className="px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold transition-colors"
                          title="Снять ограничение на отправку сообщений"
                        >
                          Снять мут
                        </button>
                      )}
                      {u.is_banned && (
                        <button
                          onClick={() => handleUnban(u.id)}
                          className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-semibold transition-colors"
                          title="Разбанить пользователя"
                        >
                          Разбанить
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
