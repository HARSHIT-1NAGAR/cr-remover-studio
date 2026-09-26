import React from 'react'
import { Clapperboard, Sparkles, Bot, Shield, Zap, Cpu, Rocket, Key } from 'lucide-react'

const MODES = [
  { key: 'autopilot', label: '⚡ Auto-Pilot Factory', icon: Rocket },
  { key: 'ai_shorts', label: 'AI Shorts Studio', icon: Sparkles },
  { key: 'auto_viral', label: 'Viral Hunter', icon: Bot },
  { key: 'studio', label: 'CR Bypass', icon: Shield },
]


export default function Header({ systemInfo, activeMode, onModeChange, onOpenKeyModal, keyCount = 0 }) {
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

      {/* Hardware Status & Gemini Key Pool */}
      <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Gemini Multi-Key Pool Button */}
        <button
          onClick={onOpenKeyModal}
          style={{
            background: keyCount > 0 ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.05)',
            border: keyCount > 0 ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid rgba(255, 255, 255, 0.1)',
            color: keyCount > 0 ? '#c7d2fe' : '#94a3b8',
            padding: '6px 12px',
            borderRadius: 'var(--radius-full, 9999px)',
            fontSize: '0.78rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: keyCount > 0 ? '0 0 12px rgba(99, 102, 241, 0.2)' : 'none'
          }}
          title="Manage Gemini Multi-API Key Pool (Failover on Limit)"
        >
          <Key size={13} color={keyCount > 0 ? '#818cf8' : '#94a3b8'} />
          <span>{keyCount > 0 ? `AI Keys (${keyCount})` : 'Set Gemini Keys'}</span>
          {keyCount > 0 && (
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
          )}
        </button>

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

