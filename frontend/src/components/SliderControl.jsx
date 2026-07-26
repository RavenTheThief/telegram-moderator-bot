import React from 'react';

export default function SliderControl({ label, description, value, min, max, step = 1, unit = '', onChange }) {
  return (
    <div className="p-3.5 bg-dark-800/40 rounded-xl border border-gray-800 space-y-2">
      <div className="flex justify-between items-center">
        <div>
          <span className="text-sm font-medium text-gray-200 block">{label}</span>
          {description && <span className="text-xs text-gray-400 block mt-0.5">{description}</span>}
        </div>
        <span className="text-sm font-bold text-blue-400 px-2.5 py-1 bg-blue-500/10 rounded-lg border border-blue-500/20">
          {value} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-dark-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
      />
    </div>
  );
}
