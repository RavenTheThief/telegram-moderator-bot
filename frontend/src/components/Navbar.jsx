import React from 'react';
import { ShieldCheck, LogOut, User, Menu, X } from 'lucide-react';

export default function Navbar({ username, userRole, onLogout, isMobileMenuOpen, onToggleMobileMenu }) {
  return (
    <header className="h-16 border-b border-gray-800 bg-dark-800/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-3">
        {/* Mobile Hamburger Toggle Button */}
        <button
          onClick={onToggleMobileMenu}
          className="md:hidden p-2 rounded-xl text-gray-300 hover:text-white bg-dark-700/60 border border-gray-700/50"
          aria-label="Toggle navigation menu"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2 rounded-xl shadow-lg shadow-blue-500/20">
          <ShieldCheck className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-sm sm:text-lg text-white leading-none">SuperModer</h1>
          <span className="text-[10px] sm:text-xs text-emerald-400 font-medium flex items-center gap-1 mt-0.5">
            <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Активен
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-2 sm:space-x-4">
        <div className="flex items-center space-x-2 bg-dark-700/60 px-2.5 sm:px-3 py-1.5 rounded-lg border border-gray-700/50 text-xs sm:text-sm">
          <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-400 shrink-0" />
          <span className="font-medium text-gray-200 truncate max-w-[100px] sm:max-w-none">{username || 'Admin'}</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold border ${
            userRole === 'support'
              ? 'bg-purple-500/20 text-purple-300 border-purple-500/30'
              : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
          }`}>
            {userRole === 'support' ? 'SUPPORT' : 'ADMIN'}
          </span>
        </div>

        <button
          onClick={onLogout}
          className="flex items-center space-x-1.5 text-xs sm:text-sm text-gray-400 hover:text-rose-400 bg-dark-700/40 hover:bg-rose-500/10 px-2.5 sm:px-3 py-1.5 rounded-lg border border-gray-700/50 hover:border-rose-500/30 transition-all"
          title="Выйти из аккаунта"
        >
          <LogOut className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          <span className="hidden sm:inline">Выйти</span>
        </button>
      </div>
    </header>
  );
}
