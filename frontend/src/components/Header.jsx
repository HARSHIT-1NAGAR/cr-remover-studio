import React from 'react'
import { Clapperboard, Sparkles, Bot, Shield, Zap, Cpu, Rocket } from 'lucide-react'

const MODES = [
  { key: 'autopilot', label: '⚡ Auto-Pilot Factory', icon: Rocket },
  { key: 'ai_shorts', label: 'AI Shorts Studio', icon: Sparkles },
  { key: 'auto_viral', label: 'Viral Hunter', icon: Bot },
  { key: 'studio', label: 'CR Bypass', icon: Shield },
]


export default function Header({ systemInfo, activeMode, onModeChange }) {
  return (
    <header className="app-header">
      {/* Brand */}
      <div className="brand">
        <div className="brand-logo">
          <Clapperboard size={17} color="#fff" />
        </div>
        <div>
          <div className="brand-name">
            CR Remover <span>Studio</span>
          </div>
        </div>
        <span className="brand-version">v2.0</span>
      </div>

      {/* Navigation Tabs */}
      <nav className="nav-tabs">
        {MODES.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            className={`nav-tab ${activeMode === key ? 'active' : ''}`}
            onClick={() => onModeChange(key)}
          >
            <span className="nav-tab-icon">
              <Icon size={14} />
            </span>
            {label}
          </button>
        ))}
      </nav>

      {/* Hardware Status */}
      <div className="header-right">
        <div className={`status-badge ${systemInfo?.nvenc_accelerated ? 'online' : ''}`}>
          <div className="status-dot" style={{ background: systemInfo?.nvenc_accelerated ? 'var(--green)' : 'var(--text-muted)' }} />
          <Zap size={11} />
          <span>{systemInfo?.nvenc_accelerated ? 'NVENC GPU' : 'CPU Encode'}</span>
        </div>
        <div className="status-badge" style={{ display: window.innerWidth > 900 ? 'flex' : 'none' }}>
          <Cpu size={11} />
          <span>Ryzen 5600H</span>
        </div>
      </div>
    </header>
  )
}
