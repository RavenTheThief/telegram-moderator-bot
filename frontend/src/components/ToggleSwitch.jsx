import React from 'react';

export default function ToggleSwitch({ label, description, checked, onChange, disabled = false }) {
  return (
    <div className="flex items-center justify-between p-3.5 bg-dark-800/40 rounded-xl border border-gray-800 hover:border-gray-700/60 transition-colors">
      <div className="pr-4">
        <span className="text-sm font-medium text-gray-200 block">{label}</span>
        {description && <span className="text-xs text-gray-400 block mt-0.5">{description}</span>}
      </div>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
          checked ? 'bg-blue-600' : 'bg-dark-600'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}
