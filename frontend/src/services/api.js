import axios from 'axios';

// Use relative API path when served via Nginx proxy, or custom VITE_API_URL
const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined ? import.meta.env.VITE_API_URL : '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/api/auth/login', { username, password }),
  getMe: () => api.get('/api/auth/me'),
};

export const chatsAPI = {
  getChats: () => api.get('/api/chats'),
  getStats: () => api.get('/api/chats/stats'),
  getChatById: (id) => api.get(`/api/chats/${id}`),
  deleteChat: (id) => api.delete(`/api/chats/${id}`),
};

export const settingsAPI = {
  getSettings: (chatId) => api.get(`/api/chats/${chatId}/settings`),
  updateSettings: (chatId, settings) => api.put(`/api/chats/${chatId}/settings`, settings),
  getStopWords: (chatId) => api.get(`/api/chats/${chatId}/stopwords`),
  addStopWord: (chatId, word, isRegex) => api.post(`/api/chats/${chatId}/stopwords`, { word, is_regex: isRegex }),
  addBulkStopWords: (chatId, words, isRegex) => api.post(`/api/chats/${chatId}/stopwords/bulk`, { words, is_regex: isRegex }),
  deleteStopWord: (chatId, stopWordId) => api.delete(`/api/chats/${chatId}/stopwords/${stopWordId}`),
};

export const logsAPI = {
  getChatLogs: (chatId, action = null, limit = 100) => 
    api.get(`/api/chats/${chatId}/logs`, { params: { action, limit } }),
  getAllLogs: (action = null, limit = 100) => 
    api.get('/api/logs/all', { params: { action, limit } }),
  cleanChatLogs: (chatId, days = 30) => 
    api.delete(`/api/chats/${chatId}/logs/clean`, { params: { days } }),
  cleanAllLogs: (days = 30) => 
    api.delete('/api/logs/all/clean', { params: { days } }),
};

export const usersAPI = {
  getChatUsers: (chatId) => api.get(`/api/chats/${chatId}/users`),
  unwarnUser: (chatId, userId) => api.post(`/api/chats/${chatId}/users/${userId}/unwarn`),
  unmuteUser: (chatId, userId) => api.post(`/api/chats/${chatId}/users/${userId}/unmute`),
  unbanUser: (chatId, userId) => api.post(`/api/chats/${chatId}/users/${userId}/unban`),
};

export default api;
