import React from 'react';
import { ShieldCheck, LogOut, User, Bell } from 'lucide-react';

export default function Navbar({ username, onLogout }) {
  return (
    <header className="h-16 border-b border-gray-800 bg-dark-800/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2 rounded-xl shadow-lg shadow-blue-500/20">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg text-white leading-none">SuperModer Admin</h1>
          <span className="text-xs text-emerald-400 font-medium flex items-center gap-1 mt-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Система активна
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex items-center space-x-2 bg-dark-700/60 px-3 py-1.5 rounded-lg border border-gray-700/50">
          <User className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-gray-200">{username || 'RavenThief'}</span>
          <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded font-semibold border border-blue-500/30">ADMIN</span>
        </div>

        <button
          onClick={onLogout}
          className="flex items-center space-x-1.5 text-sm text-gray-400 hover:text-rose-400 bg-dark-700/40 hover:bg-rose-500/10 px-3 py-1.5 rounded-lg border border-gray-700/50 hover:border-rose-500/30 transition-all"
          title="Выйти из аккаунта"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Выйти</span>
        </button>
      </div>
    </header>
  );
}
