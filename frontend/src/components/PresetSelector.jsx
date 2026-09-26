import React from 'react'
import { Zap, Smartphone, Sparkles, Mic, Sliders } from 'lucide-react'

const PRESET_ICONS = {
  youtube_bypass: { icon: Zap, color: 'var(--amber)' },
  insta_shorts: { icon: Smartphone, color: '#ec4899' },
  ai_deep_clean: { icon: Sparkles, color: 'var(--accent2)' },
  vocal_only: { icon: Mic, color: 'var(--green)' },
}

export default function PresetSelector({ selectedPreset, onSelectPreset, presets }) {
  if (!presets) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <div className="card-title-icon"><Sliders size={14} /></div>
            Presets
          </div>
        </div>
        <div className="card-body">
          <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Loading presets…</div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-icon"><Sliders size={14} /></div>
          Transformation Presets
        </div>
      </div>
      <div className="card-body">
        <div className="preset-grid">
          {Object.entries(presets).map(([key, config]) => {
            const meta = PRESET_ICONS[key] || { icon: Sliders, color: 'var(--accent)' }
            const Icon = meta.icon
            const isSelected = selectedPreset === key
            return (
              <button
                key={key}
                className={`preset-card ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectPreset(key)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <Icon size={13} color={isSelected ? 'var(--accent)' : meta.color} />
                  <span className="preset-card-name">{config.name}</span>
                </div>
                <div className="preset-card-desc">{config.description}</div>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
