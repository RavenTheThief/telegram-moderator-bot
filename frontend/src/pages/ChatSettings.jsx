import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, AlertTriangle, MessageSquare, Volume2, Image, FileText, UserPlus, Sliders, Save, CheckCircle, Plus, Trash2, Code, Shuffle, ListPlus 
} from 'lucide-react';
import ToggleSwitch from '../components/ToggleSwitch';
import SliderControl from '../components/SliderControl';
import { settingsAPI } from '../services/api';

const ALL_CAPTCHA_TYPES = [
  { id: 'button', label: 'Кнопка "Я не робот"' },
  { id: 'math', label: 'Простая математика (+)' },
  { id: 'math_advanced', label: 'Сложная математика (-, *)' },
  { id: 'emoji', label: 'Эмодзи-капча (Найди иконку 🍎)' },
  { id: 'question', label: 'Вопросы на логику' },
  { id: 'category', label: 'Категории (Еда/Транспорт/Пес)' },
  { id: 'compare', label: 'Сравнение чисел (Больше/Меньше)' },
  { id: 'shapes', label: 'Цвета и Фигуры (Синий Квадрат)' },
  { id: 'sequence', label: 'Наименьшее/Наибольшее число' },
  { id: 'custom_question', label: 'Вопрос Сообщества (Свой ответ)' },
];

export default function ChatSettings({ chatId, chatTitle, onDeleteChat }) {
  const [settings, setSettings] = useState(null);
  const [stopWords, setStopWords] = useState([]);
  const [newStopWord, setNewStopWord] = useState('');
  const [bulkWordsText, setBulkWordsText] = useState('');
  const [isBulkMode, setIsBulkMode] = useState(false);
  const [isRegex, setIsRegex] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [addingBulk, setAddingBulk] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState('captcha');

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
        settingsAPI.getStopWords(chatId),
      ]);
      setSettings(settingsRes.data);
      setStopWords(stopWordsRes.data);
    } catch (err) {
      console.error("Failed to fetch settings", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setSavedSuccess(false);
    try {
      await settingsAPI.updateSettings(chatId, settings);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      alert("Ошибка сохранения настроек");
    } finally {
      setSaving(false);
    }
  };

  const handleAddStopWord = async (e) => {
    e.preventDefault();
    if (!newStopWord.trim()) return;
    try {
      const res = await settingsAPI.addStopWord(chatId, newStopWord.trim(), isRegex);
      setStopWords([res.data, ...stopWords]);
      setNewStopWord('');
      setIsRegex(false);
    } catch (err) {
      alert("Ошибка добавления стоп-слова");
    }
  };

  const handleAddBulkStopWords = async (e) => {
    e.preventDefault();
    if (!bulkWordsText.trim()) return;
    setAddingBulk(true);
    try {
      const res = await settingsAPI.addBulkStopWords(chatId, bulkWordsText.trim(), isRegex);
      setStopWords(res.data);
      setBulkWordsText('');
      setIsRegex(false);
    } catch (err) {
      alert("Ошибка добавления списка стоп-слов");
    } finally {
      setAddingBulk(false);
    }
  };

  const handleDeleteStopWord = async (id) => {
    try {
      await settingsAPI.deleteStopWord(chatId, id);
      setStopWords(stopWords.filter(item => item.id !== id));
    } catch (err) {
      alert("Ошибка удаления стоп-слова");
    }
  };

  const updateField = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleToggleRotationType = (typeId) => {
    const currentRaw = settings.captcha_enabled_types || 'button,math,math_advanced,emoji,question,category,compare,shapes,sequence';
    let currentList = currentRaw.split(',').map(s => s.trim()).filter(Boolean);

    if (currentList.includes(typeId)) {
      currentList = currentList.filter(t => t !== typeId);
    } else {
      currentList.push(typeId);
    }

    updateField('captcha_enabled_types', currentList.join(','));
  };

  if (!chatId) {
    return (
      <div className="p-12 text-center text-gray-400 bg-dark-800/40 rounded-2xl border border-gray-800">
        Пожалуйста, выберите чат из списка слева для настройки правил модерации.
      </div>
    );
  }

  if (loading || !settings) {
    return (
      <div className="p-12 text-center text-gray-400">
        Загрузка настроек чата...
      </div>
    );
  }

  const tabs = [
    { id: 'captcha', label: '👋 Капча & Приветствие' },
    { id: 'filters', label: '🛡️ Контент & Ссылки' },
    { id: 'flood', label: '⚡ Антифлуд & Варны' },
    { id: 'stopwords', label: '🚫 Стоп-слова' },
    { id: 'protection', label: '🔒 Анти-рейд & Ограничения' },
  ];

  const enabledRotationList = (settings.captcha_enabled_types || '').split(',').map(s => s.trim());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-400" />
            Настройки: <span className="text-blue-400">{chatTitle || `ID ${chatId}`}</span>
          </h2>
          <p className="text-xs text-gray-400">Конфигурация правил безопасности и автоматических наказаний</p>
        </div>

        <div className="flex items-center space-x-2">
          {onDeleteChat && (
            <button
              onClick={() => onDeleteChat({ id: chatId, title: chatTitle || `ID ${chatId}` })}
              className="flex items-center space-x-1.5 px-3.5 py-2.5 rounded-xl font-semibold text-xs bg-rose-500/10 hover:bg-rose-600 text-rose-400 hover:text-white border border-rose-500/30 transition-all"
              title="Удалить этот чат из системы и вывести бота"
            >
              <Trash2 className="w-4 h-4" />
              <span className="hidden sm:inline">Удалить чат</span>
            </button>
          )}

          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-semibold text-xs transition-all shadow-lg ${
              savedSuccess 
                ? 'bg-emerald-600 text-white shadow-emerald-500/20' 
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-500/20'
            }`}
          >
            {savedSuccess ? (
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
              <label className="block text-sm font-medium text-gray-200 mb-2">Режим Капчи</label>
              <select
                value={settings.captcha_type}
                onChange={(e) => updateField('captcha_type', e.target.value)}
                className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="random">🔀 РОТАЦИЯ (Случайный выбор из списка)</option>
                <option value="button">Кнопка "Я не робот"</option>
                <option value="math">Простая математика (+)</option>
                <option value="math_advanced">Сложная математика (-, *)</option>
                <option value="emoji">Эмодзи-капча (Найди иконку 🍎)</option>
                <option value="question">Вопросы на логику</option>
                <option value="category">Поиск по Категориям (Еда/Пес)</option>
                <option value="compare">Сравнение чисел (Больше/Меньше)</option>
                <option value="shapes">Цвета и фигуры (Синий Квадрат)</option>
                <option value="sequence">Наименьшее/Наибольшее число</option>
                <option value="custom_question">⭐ Вопрос Сообщества (Свой ответ)</option>
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

          {/* ROTATION OPTIONS CHECKBOXES */}
          {settings.captcha_type === 'random' && (
            <div className="p-4 bg-blue-950/20 border border-blue-500/30 rounded-2xl space-y-3">
              <div className="flex items-center space-x-2 text-blue-400 font-bold text-sm">
                <Shuffle className="w-4 h-4" />
                <span>Настройка Ротации: Выберите капчи для случайного выбора</span>
              </div>
              <p className="text-xs text-gray-400">Каждому новому участнику будет приходить случайная капча из отмеченных ниже:</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 pt-1">
                {ALL_CAPTCHA_TYPES.map((typeObj) => {
                  const isChecked = enabledRotationList.includes(typeObj.id);
                  return (
                    <label
                      key={typeObj.id}
                      className={`flex items-center space-x-2.5 p-2.5 rounded-xl border text-xs font-medium cursor-pointer transition-all ${
                        isChecked
                          ? 'bg-blue-600/10 border-blue-500/40 text-blue-300'
                          : 'bg-dark-800/40 border-gray-800 text-gray-400 hover:border-gray-700'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggleRotationType(typeObj.id)}
                        className="rounded border-gray-700 bg-dark-700 text-blue-500 focus:ring-0"
                      />
                      <span>{typeObj.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {/* CUSTOM COMMUNITY QUESTION INPUTS */}
          {(settings.captcha_type === 'custom_question' || (settings.captcha_type === 'random' && enabledRotationList.includes('custom_question'))) && (
            <div className="p-4 bg-purple-950/20 border border-purple-500/30 rounded-2xl space-y-3">
              <h4 className="font-bold text-purple-300 text-sm">⭐ Настройка Своего Вопроса Группы</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">Текст вопроса для нового участника</label>
                  <input
                    type="text"
                    placeholder="Например: Какая главная тематика нашего сервера?"
                    value={settings.custom_captcha_question || ''}
                    onChange={(e) => updateField('custom_captcha_question', e.target.value)}
                    className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg p-2.5 text-sm focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">Правильный ответ (Текст на кнопке)</label>
                  <input
                    type="text"
                    placeholder="Например: Игры и Программирование"
                    value={settings.custom_captcha_answer || ''}
                    onChange={(e) => updateField('custom_captcha_answer', e.target.value)}
                    className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg p-2.5 text-sm focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>
            </div>
          )}

          <SliderControl
            label="Таймаут прохождения капчи"
            value={settings.captcha_timeout}
            min={30}
            max={600}
            unit="сек"
            onChange={(val) => updateField('captcha_timeout', val)}
          />

          <hr className="border-gray-800 my-4" />

          <ToggleSwitch
            label="Приветственное сообщение"
            description="Отправлять сообщение в чат после успешного прохождения капчи"
            checked={settings.welcome_message_enabled}
            onChange={(val) => updateField('welcome_message_enabled', val)}
          />

          {settings.welcome_message_enabled && (
            <div className="p-4 bg-dark-800/40 rounded-xl border border-gray-800 space-y-2">
              <label className="block text-sm font-medium text-gray-200">Текст приветствия</label>
              <textarea
                value={settings.welcome_text}
                onChange={(e) => updateField('welcome_text', e.target.value)}
                rows={3}
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

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <div className="p-3.5 bg-dark-800/40 rounded-xl border border-gray-800">
              <label className="block text-sm font-medium text-gray-200 mb-1">
                Авто-сбрасывание варнов (Время жизни)
              </label>
              <p className="text-xs text-gray-400 mb-2">
                Через указанный период накопленные варны автоматически сгорают
              </p>
              <select
                value={settings.warn_expire_hours ?? 24}
                onChange={(e) => updateField('warn_expire_hours', parseInt(e.target.value))}
                className="w-full bg-dark-700 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value={0}>Отключено (Варны не сгорают)</option>
                <option value={1}>1 час</option>
                <option value={6}>6 часов</option>
                <option value={12}>12 часов</option>
                <option value={24}>24 часа (1 день)</option>
                <option value={48}>48 часов (2 дня)</option>
                <option value={72}>72 часа (3 дня)</option>
                <option value={168}>168 часов (1 неделя)</option>
              </select>
            </div>
          </div>

          {settings.warns_punishment === 'mute' && (
            <SliderControl
              label="Длительность Мута за Варны"
              value={settings.warns_mute_duration_minutes}
              min={5}
              max={10080}
              unit="мин"
              onChange={(val) => updateField('warns_mute_duration_minutes', val)}
            />
          )}
        </div>
      )}

      {/* TAB 4: STOP WORDS */}
      {activeTab === 'stopwords' && (
        <div className="space-y-6">
          {/* Toggle Mode Single vs Bulk */}
          <div className="flex items-center space-x-2 border-b border-gray-800 pb-3">
            <button
              type="button"
              onClick={() => setIsBulkMode(false)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                !isBulkMode
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              + Одно слово
            </button>
            <button
              type="button"
              onClick={() => setIsBulkMode(true)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1 ${
                isBulkMode
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <ListPlus className="w-3.5 h-3.5" />
              <span>📋 Массовый ввод (Списком)</span>
            </button>
          </div>

          {isBulkMode ? (
            <form onSubmit={handleAddBulkStopWords} className="p-4 bg-dark-800/40 rounded-xl border border-gray-800 space-y-4">
              <h4 className="font-bold text-white text-sm">Массовое добавление стоп-слов</h4>
              <p className="text-xs text-gray-400">
                Вставьте список слов через запятую или по одному слову на строке:
              </p>
              <textarea
                rows={5}
                placeholder={"спам, скам, мошенник\nказино\nкрипта"}
                value={bulkWordsText}
                onChange={(e) => setBulkWordsText(e.target.value)}
                className="w-full bg-dark-700 border border-gray-700 text-white rounded-xl p-3 text-sm focus:outline-none focus:border-blue-500 font-mono"
              />
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <label className="flex items-center space-x-2 cursor-pointer text-xs text-gray-400">
                  <input
                    type="checkbox"
                    checked={isRegex}
                    onChange={(e) => setIsRegex(e.target.checked)}
                    className="rounded border-gray-700 bg-dark-700 text-blue-500 focus:ring-0"
                  />
                  <span>Добавить список как Регулярные выражения (Regex)</span>
                </label>
                <button
                  type="submit"
                  disabled={addingBulk}
                  className="flex items-center justify-center space-x-1.5 bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-xl text-xs font-semibold transition-colors disabled:opacity-50"
                >
                  <Plus className="w-4 h-4" />
                  <span>{addingBulk ? 'Добавление...' : 'Загрузить список слов'}</span>
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleAddStopWord} className="p-4 bg-dark-800/40 rounded-xl border border-gray-800 space-y-4">
              <h4 className="font-bold text-white text-sm">Добавить Запрещенное Слово</h4>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  placeholder="Введение запрещенного слова или Regex..."
                  value={newStopWord}
                  onChange={(e) => setNewStopWord(e.target.value)}
                  className="flex-1 bg-dark-700 border border-gray-700 text-white rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
                />
                <button
                  type="submit"
                  className="flex items-center justify-center space-x-1.5 bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-xl text-xs font-semibold transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  <span>Добавить</span>
                </button>
              </div>

              <label className="flex items-center space-x-2 cursor-pointer text-xs text-gray-400">
                <input
                  type="checkbox"
                  checked={isRegex}
                  onChange={(e) => setIsRegex(e.target.checked)}
                  className="rounded border-gray-700 bg-dark-700 text-blue-500 focus:ring-0"
                />
                <span>Использовать как Регулярное выражение (Regex)</span>
              </label>
            </form>
          )}

          <div className="space-y-3">
            <h4 className="font-bold text-white text-sm">Список Запрещенных Слов ({stopWords.length})</h4>
            {stopWords.length === 0 ? (
              <p className="text-xs text-gray-500 p-4 border border-gray-800/80 rounded-xl">Нет добавленных стоп-слов</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {stopWords.map((sw) => (
                  <div
                    key={sw.id}
                    className="p-3 bg-dark-800/60 border border-gray-800 rounded-xl flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-2 truncate">
                      {sw.is_regex && <Code className="w-3.5 h-3.5 text-purple-400 shrink-0" />}
                      <span className="text-sm font-medium text-gray-200 truncate">{sw.word}</span>
                    </div>
                    <button
                      onClick={() => handleDeleteStopWord(sw.id)}
                      className="text-gray-500 hover:text-rose-400 p-1 transition-colors"
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

      {/* TAB 5: PROTECTION & EXTRAS */}
      {activeTab === 'protection' && (
        <div className="space-y-4">
          <ToggleSwitch
            label="Анти-Капс (Чрезмерные заглавные буквы)"
            description="Авто-удаление сообщений состоящих преимущественно из CAPS LOCK"
            checked={settings.anti_caps_enabled}
            onChange={(val) => updateField('anti_caps_enabled', val)}
          />

          {settings.anti_caps_enabled && (
            <SliderControl
              label="Порог заглавных букв (%)"
              value={settings.anti_caps_threshold_percent}
              min={50}
              max={100}
              unit="%"
              onChange={(val) => updateField('anti_caps_threshold_percent', val)}
            />
          )}

          <hr className="border-gray-800 my-4" />

          <ToggleSwitch
            label="Удалять сервисные сообщения Telegram"
            description="Автоматически чистить сообщения о входе/выходе участников и закреплении сообщений"
            checked={settings.clean_service_messages}
            onChange={(val) => updateField('clean_service_messages', val)}
          />

          <SliderControl
            label="Авто-удаление сообщений бота"
            description="Через сколько секунд удалять сервисные предупреждения бота из чата"
            value={settings.bot_auto_delete_seconds}
            min={0}
            max={300}
            unit="сек (0=не удалять)"
            onChange={(val) => updateField('bot_auto_delete_seconds', val)}
          />
        </div>
      )}
    </div>
  );
}
