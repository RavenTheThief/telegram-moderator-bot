import React from 'react';

export default function StatCard({ title, value, icon: Icon, color = 'blue', subtitle }) {
  const colorStyles = {
    blue: 'from-blue-500/10 to-indigo-500/10 border-blue-500/20 text-blue-400',
    emerald: 'from-emerald-500/10 to-teal-500/10 border-emerald-500/20 text-emerald-400',
    amber: 'from-amber-500/10 to-orange-500/10 border-amber-500/20 text-amber-400',
    rose: 'from-rose-500/10 to-red-500/10 border-rose-500/20 text-rose-400',
    purple: 'from-purple-500/10 to-violet-500/10 border-purple-500/20 text-purple-400',
  };

  return (
    <div className={`p-5 rounded-2xl bg-gradient-to-br ${colorStyles[color]} border backdrop-blur-md shadow-xl transition-transform hover:-translate-y-1`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">{title}</p>
          <h3 className="text-2xl font-bold text-white mt-1">{value}</h3>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-dark-800/80 border border-gray-700/50 shadow-inner`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}
