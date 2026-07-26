import React, { useEffect, useState } from 'react';
import { FileText, Search, Filter, RefreshCw, Trash2, CheckCircle2 } from 'lucide-react';
import { logsAPI } from '../services/api';

export default function AuditLogs({ chatId }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cleaning, setCleaning] = useState(false);
  const [actionFilter, setActionFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [infoMessage, setInfoMessage] = useState('');

  useEffect(() => {
    fetchLogs();
  }, [chatId, actionFilter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let res;
      if (chatId) {
        res = await logsAPI.getChatLogs(chatId, actionFilter || null);
      } else {
        res = await logsAPI.getAllLogs(actionFilter || null);
      }
      setLogs(res.data);
    } catch (err) {
      console.error("Failed to fetch logs", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanLogs = async () => {
    if (!window.confirm("Удалить все логи старше 30 дней?")) return;
    setCleaning(true);
    try {
      if (chatId) {
        await logsAPI.cleanChatLogs(chatId, 30);
      } else {
        await logsAPI.cleanAllLogs(30);
      }
      setInfoMessage("Логи старше 30 дней успешно очищены!");
      setTimeout(() => setInfoMessage(''), 3000);
      fetchLogs();
    } catch (err) {
      alert("Ошибка при очистке логов");
    } finally {
      setCleaning(false);
    }
  };

  const filteredLogs = logs.filter((log) => {
    const term = searchTerm.toLowerCase();
    return (
      log.reason.toLowerCase().includes(term) ||
      (log.user_fullname && log.user_fullname.toLowerCase().includes(term)) ||
      (log.user_id && String(log.user_id).includes(term))
    );
  });

  const getActionBadge = (action) => {
    switch (action) {
      case 'ban_user':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">BAN</span>;
      case 'mute_user':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">MUTE</span>;
      case 'delete_message':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">DELETE</span>;
      case 'captcha_failed':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">CAPTCHA FAIL</span>;
      case 'captcha_passed':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">CAPTCHA PASS</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-500/10 text-gray-400 border border-gray-500/20">{action}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Журнал Событий & Аудита
          </h2>
          <p className="text-xs text-gray-400">
            {chatId ? `Просмотр логов для чата ID: ${chatId}` : 'Все зафиксированные действия в подключенных чатах'}
          </p>
        </div>

        <div className="flex items-center space-x-2 self-start sm:self-auto">
          <button
            onClick={handleCleanLogs}
            disabled={cleaning}
            className="flex items-center space-x-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 px-3.5 py-2 rounded-xl text-xs font-semibold border border-rose-500/30 transition-colors disabled:opacity-50"
            title="Удалить устаревшие логи старше 30 дней"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{cleaning ? 'Очистка...' : 'Очистить > 30 дней'}</span>
          </button>

          <button
            onClick={fetchLogs}
            className="flex items-center space-x-1.5 bg-dark-700 hover:bg-dark-600 text-gray-300 px-3.5 py-2 rounded-xl text-xs font-semibold border border-gray-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Обновить</span>
          </button>
        </div>
      </div>

      {infoMessage && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center space-x-3 text-emerald-400 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{infoMessage}</span>
        </div>
      )}

      {/* Filters & Search bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Поиск по пользователю, ID или причине..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-dark-800/80 border border-gray-800 text-white rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-blue-500"
          />
        </div>

        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="bg-dark-800/80 border border-gray-800 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 cursor-pointer"
        >
          <option value="">Все действия</option>
          <option value="delete_message">Удаление сообщений</option>
          <option value="mute_user">Муты (Mute)</option>
          <option value="ban_user">Баны (Ban)</option>
          <option value="captcha_failed">Провал Капчи</option>
          <option value="captcha_passed">Успех Капчи</option>
          <option value="unwarn">Снятие Варнов</option>
          <option value="unmute">Снятие Мута</option>
          <option value="unban">Разбан</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="bg-dark-800/60 border border-gray-800 rounded-2xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="p-12 text-center text-gray-400">Загрузка журнала аудита...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-gray-400">Записи не найдены</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-dark-700/50 text-xs font-semibold text-gray-400 uppercase border-b border-gray-800">
                <tr>
                  <th className="px-6 py-3.5">Дата / Время</th>
                  <th className="px-6 py-3.5">Действие</th>
                  <th className="px-6 py-3.5">Пользователь</th>
                  <th className="px-6 py-3.5">Причина / Детали</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/80">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-dark-700/30 transition-colors">
                    <td className="px-6 py-4 text-xs font-mono text-gray-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString('ru-RU')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getActionBadge(log.action)}
                    </td>
                    <td className="px-6 py-4">
                      {log.user_fullname ? (
                        <div>
                          <div className="font-semibold text-white">{log.user_fullname}</div>
                          <div className="text-xs text-gray-400 font-mono">ID: {log.user_id}</div>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400 font-mono">ID: {log.user_id || 'System'}</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-200">{log.reason}</div>
                      {log.details && <div className="text-xs text-gray-400 mt-0.5">{log.details}</div>}
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
