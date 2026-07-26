import React, { useEffect, useState } from 'react';
import { 
  ShieldCheck, Filter, Zap, Lock, FileCode, Save, CheckCircle, AlertCircle, Plus, Trash2, Tag 
} from 'lucide-react';
import ToggleSwitch from '../components/ToggleSwitch';
import SliderControl from '../components/SliderControl';
import { settingsAPI } from '../services/api';

export default function ChatSettings({ chatId }) {
  const [activeTab, setActiveTab] = useState('captcha');
  const [settings, setSettings] = useState(null);
  const [stopWords, setStopWords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Stop words form state
  const [newWord, setNewWord] = useState('');
  const [newIsRegex, setNewIsRegex] = useState(false);

  useEffect(() => {
    if (chatId) {
      fetchData();
    }
  }, [chatId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [settingsRes, stopWordsRes] = await Promise.all([
        settingsAPI.getSettings(chatId),
        settingsAPI.getStopWords(chatId)
      ]);
      setSettings(settingsRes.data);
      setStopWords(stopWordsRes.data);
    } catch (err) {
      console.error("Failed to load chat settings", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      await settingsAPI.updateSettings(chatId, settings);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save settings", err);
      alert("Ошибка при сохранении настроек");
    } finally {
      setSaving(false);
    }
  };

  const handleAddStopWord = async (e) => {
    e.preventDefault();
    if (!newWord.trim()) return;
    try {
      const res = await settingsAPI.addStopWord(chatId, newWord.trim(), newIsRegex);
      setStopWords([res.data, ...stopWords]);
      setNewWord('');
    } catch (err) {
      console.error("Failed to add stop word", err);
    }
  };

  const handleDeleteStopWord = async (id) => {
    try {
      await settingsAPI.deleteStopWord(chatId, id);
      setStopWords(stopWords.filter(sw => sw.id !== id));
    } catch (err) {
      console.error("Failed to delete stop word", err);
    }
  };

  const updateField = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  if (!chatId) {
    return (
      <div className="p-12 text-center text-gray-400 bg-dark-800/40 rounded-2xl border border-gray-800">
        <AlertCircle className="w-10 h-10 mx-auto text-amber-500 mb-2" />
        Пожалуйста, выберите чат из бокового меню слева.
      </div>
    );
  }

  if (loading || !settings) {
    return <div className="p-8 text-center text-gray-400">Загрузка настроек чата...</div>;
  }

  const tabs = [
    { id: 'captcha', label: '🛡️ Капча & Приветствие', icon: ShieldCheck },
    { id: 'filters', label: '🚫 Контент-Фильтры', icon: Filter },
    { id: 'flood', label: '⚡ Флуд & Варны', icon: Zap },
    { id: 'limits', label: '🔒 Доп. Защита', icon: Lock },
    { id: 'stopwords', label: '📝 Стоп-Слова & Regex', icon: FileCode },
  ];

  return (
    <div className="space-y-6">
      {/* Settings Navigation Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Настройки Модератора</h2>
          <p className="text-xs text-gray-400">Управление параметрами чата (ID: {chatId})</p>
        </div>

        <button
          onClick={handleSaveSettings}
          disabled={saving}
          className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-5 py-2.5 rounded-xl shadow-lg shadow-blue-500/20 text-sm font-semibold transition-all disabled:opacity-50"
        >
          {saveSuccess ? (
            <>
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              <span>Сохранено!</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>{saving ? 'Сохранение...' : 'Сохранить изменения'}</span>
            </>
          )}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-gray-800/80 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-dark-800/40'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: CAPTCHA */}
      {activeTab === 'captcha' && (
        <div className="space-y-4">
          <ToggleSwitch
            label="Включить Капчу при входе"
            description="Проверка всех новых участников перед предоставлением прав отправки сообщений"
            checked={settings.captcha_enabled}
            onChange={(val) => updateField('captcha_enabled', val)}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3.5 bg-dark-800/40 rounded-xl border border-gray-800">
              <label className="block text-sm font-medium text-gray-200 mb-2">Тип Капчи</label>
              <select
                value={settings.captcha_type}
                onChange={(e) => updateField('captcha_type', e.target.value)}
                className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="button">Кнопка "Я не робот"</option>
                <option value="math">Математическая задача (Пример 4+3=?)</option>
              </select>
            </div>

            <div className="p-3.5 bg-dark-800/40 rounded-xl border border-gray-800">
              <label className="block text-sm font-medium text-gray-200 mb-2">Действие при непрохождении</label>
              <select
                value={settings.captcha_fail_action}
                onChange={(e) => updateField('captcha_fail_action', e.target.value)}
                className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="kick">Исключить (Kick - сможет перезайти)</option>
                <option value="ban">Заблокировать (Ban)</option>
              </select>
            </div>
          </div>

          <SliderControl
            label="Время на решение капчи"
            description="Таймаут в секундах, по истечении которого применяется наказание"
            value={settings.captcha_timeout}
            min={30}
            max={300}
            step={10}
            unit="сек"
            onChange={(val) => updateField('captcha_timeout', val)}
          />

          <ToggleSwitch
            label="Приветственное сообщение"
            description="Отправлять приветствие после успешного прохождения капчи"
            checked={settings.welcome_message_enabled}
            onChange={(val) => updateField('welcome_message_enabled', val)}
          />

          {settings.welcome_message_enabled && (
            <div className="p-4 bg-dark-800/40 rounded-xl border border-gray-800 space-y-2">
              <label className="block text-sm font-medium text-gray-200">Текст приветствия</label>
              <textarea
                rows={3}
                value={settings.welcome_text}
                onChange={(e) => updateField('welcome_text', e.target.value)}
                className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg p-3 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          )}
        </div>
      )}

      {/* TAB 2: FILTERS */}
      {activeTab === 'filters' && (
        <div className="space-y-4">
          <ToggleSwitch
            label="Фильтр ссылок"
            description="Удалять сообщения содержащие веб-ссылки и сторонние ресурсы"
            checked={settings.filter_links}
            onChange={(val) => updateField('filter_links', val)}
          />

          {settings.filter_links && (
            <div className="p-4 bg-dark-800/40 rounded-xl border border-gray-800 space-y-2">
              <label className="block text-sm font-medium text-gray-200">Белый список доменов (Разрешенные)</label>
              <p className="text-xs text-gray-400">Укажите домены через запятую (например: t.me, telegram.me, youtube.com)</p>
              <input
                type="text"
                value={settings.whitelisted_domains}
                onChange={(e) => updateField('whitelisted_domains', e.target.value)}
                className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg p-2.5 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ToggleSwitch
              label="Запрет GIF-анимаций"
              checked={settings.filter_gifs}
              onChange={(val) => updateField('filter_gifs', val)}
            />
            <ToggleSwitch
              label="Запрет Стикеров"
              checked={settings.filter_stickers}
              onChange={(val) => updateField('filter_stickers', val)}
            />
            <ToggleSwitch
              label="Запрет Голосовых сообщений"
              checked={settings.filter_voice}
              onChange={(val) => updateField('filter_voice', val)}
            />
            <ToggleSwitch
              label="Запрет Видео-сообщений (кружочки)"
              checked={settings.filter_video_notes}
              onChange={(val) => updateField('filter_video_notes', val)}
            />
            <ToggleSwitch
              label="Запрет Аудиофайлов"
              checked={settings.filter_audio}
              onChange={(val) => updateField('filter_audio', val)}
            />
            <ToggleSwitch
              label="Запрет Видеофайлов"
              checked={settings.filter_video}
              onChange={(val) => updateField('filter_video', val)}
            />
            <ToggleSwitch
              label="Запрет Документов / Файлов"
              checked={settings.filter_documents}
              onChange={(val) => updateField('filter_documents', val)}
            />
            <ToggleSwitch
              label="Анти-Каналы"
              description="Запрет сообщений от имени Telegram-каналов"
              checked={settings.filter_anti_channel}
              onChange={(val) => updateField('filter_anti_channel', val)}
            />
            <ToggleSwitch
              label="Анти-Пересылка"
              description="Запрет пересланных сообщений из других чатов"
              checked={settings.filter_anti_forward}
              onChange={(val) => updateField('filter_anti_forward', val)}
            />
          </div>
        </div>
      )}

      {/* TAB 3: FLOOD & WARNS */}
      {activeTab === 'flood' && (
        <div className="space-y-4">
          <ToggleSwitch
            label="Защита от Флуда (Redis Rate Limiting)"
            description="Ограничение количества сообщений за временной интервал"
            checked={settings.anti_flood_enabled}
            onChange={(val) => updateField('anti_flood_enabled', val)}
          />

          {settings.anti_flood_enabled && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <SliderControl
                label="Макс. сообщений"
                value={settings.anti_flood_max_messages}
                min={2}
                max={20}
                unit="сообщ."
                onChange={(val) => updateField('anti_flood_max_messages', val)}
              />
              <SliderControl
                label="Временное окно"
                value={settings.anti_flood_window_seconds}
                min={1}
                max={10}
                unit="сек"
                onChange={(val) => updateField('anti_flood_window_seconds', val)}
              />
              <SliderControl
                label="Длительность Мута"
                value={settings.anti_flood_mute_duration_minutes}
                min={1}
                max={1440}
                unit="мин"
                onChange={(val) => updateField('anti_flood_mute_duration_minutes', val)}
              />
            </div>
          )}

          <hr className="border-gray-800 my-4" />

          <h3 className="text-md font-bold text-white">Система Предупреждений (Warns)</h3>

          <SliderControl
            label="Лимит максимальных предупреждений (Max Warns)"
            description="Настройка количества варнов до автоматического применения наказания"
            value={settings.max_warns}
            min={1}
            max={10}
            unit="варнов"
            onChange={(val) => updateField('max_warns', val)}
          />

          <div className="p-3.5 bg-dark-800/40 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-200 mb-2">Наказание при достижении лимита</label>
            <select
              value={settings.warns_punishment}
              onChange={(e) => updateField('warns_punishment', e.target.value)}
              className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="mute">Мут (Временное ограничение отправки)</option>
              <option value="ban">Бан (Блокировка и исключение)</option>
            </select>
          </div>

          {settings.warns_punishment === 'mute' && (
            <SliderControl
              label="Длительность Мута за Варны"
              value={settings.warns_mute_duration_minutes}
              min={10}
              max={10080}
              step={10}
              unit="мин"
              onChange={(val) => updateField('warns_mute_duration_minutes', val)}
            />
          )}
        </div>
      )}

      {/* TAB 4: LIMITS */}
      {activeTab === 'limits' && (
        <div className="space-y-4">
          <ToggleSwitch
            label="Фильтр Капс Лок (Caps Lock)"
            description="Автоматическое удаление сообщений, написанных заглавными буквами"
            checked={settings.anti_caps_enabled}
            onChange={(val) => updateField('anti_caps_enabled', val)}
          />

          {settings.anti_caps_enabled && (
            <SliderControl
              label="Порог заглавных букв"
              value={settings.anti_caps_threshold_percent}
              min={50}
              max={100}
              unit="%"
              onChange={(val) => updateField('anti_caps_threshold_percent', val)}
            />
          )}

          <ToggleSwitch
            label="Авто-чистка системных сообщений"
            description="Удаление уведомлений 'Вошел в группу', 'Покинул группу', 'Закрепил сообщение'"
            checked={settings.clean_service_messages}
            onChange={(val) => updateField('clean_service_messages', val)}
          />

          <SliderControl
            label="Авто-удаление сообщений бота"
            description="Таймаут в секундах, через который бот сам удаляет свои сервисные предупреждения"
            value={settings.bot_auto_delete_seconds}
            min={0}
            max={300}
            step={5}
            unit="сек"
            onChange={(val) => updateField('bot_auto_delete_seconds', val)}
          />
        </div>
      )}

      {/* TAB 5: STOP WORDS */}
      {activeTab === 'stopwords' && (
        <div className="space-y-6">
          {/* Form to add new stop word */}
          <form onSubmit={handleAddStopWord} className="p-4 bg-dark-800/40 rounded-xl border border-gray-800 space-y-4">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Plus className="w-4 h-4 text-blue-400" />
              Добавить Стоп-Слово или Regex Шаблон
            </h4>

            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                required
                placeholder="Введите слово или регулярное выражение..."
                value={newWord}
                onChange={(e) => setNewWord(e.target.value)}
                className="flex-1 bg-dark-700 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500"
              />

              <label className="flex items-center space-x-2 px-3 py-2.5 bg-dark-700/60 rounded-xl border border-gray-700 text-xs font-medium text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newIsRegex}
                  onChange={(e) => setNewIsRegex(e.target.checked)}
                  className="rounded bg-dark-800 border-gray-600 text-blue-500 focus:ring-0"
                />
                <span>Regex шаблон</span>
              </label>

              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center space-x-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Добавить</span>
              </button>
            </div>
          </form>

          {/* List of active stop words */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider">
              Активные правила ({stopWords.length})
            </h4>

            {stopWords.length === 0 ? (
              <p className="text-xs text-gray-500 p-4 bg-dark-800/20 rounded-xl border border-gray-800 text-center">
                Список стоп-слов пуст. Добавьте запрещенные слова или выражения выше.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {stopWords.map((sw) => (
                  <div
                    key={sw.id}
                    className="p-3 bg-dark-800/60 border border-gray-800 rounded-xl flex items-center justify-between group hover:border-gray-700 transition-colors"
                  >
                    <div className="flex items-center space-x-2 overflow-hidden pr-2">
                      <Tag className="w-4 h-4 text-blue-400 shrink-0" />
                      <span className="text-sm text-gray-200 font-mono truncate">{sw.word}</span>
                      {sw.is_regex && (
                        <span className="text-[10px] bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded border border-purple-500/30">
                          REGEX
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteStopWord(sw.id)}
                      className="text-gray-500 hover:text-rose-400 p-1 rounded hover:bg-rose-500/10 transition-colors"
                      title="Удалить"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
