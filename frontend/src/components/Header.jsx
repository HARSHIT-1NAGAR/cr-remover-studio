import React from 'react'
import { Clapperboard, Sparkles, Bot, Shield, Zap, Cpu, Rocket, Key, FolderOpen, Sun, Moon } from 'lucide-react'

const MODES = [
  { key: 'autopilot', label: '⚡ Auto-Pilot Factory', icon: Rocket },
  { key: 'ai_shorts', label: 'AI Shorts Studio', icon: Sparkles },
  { key: 'auto_viral', label: 'Viral Hunter', icon: Bot },
  { key: 'studio', label: 'CR Bypass', icon: Shield },
]


export default function Header({
  systemInfo,
  activeMode,
  onModeChange,
  onOpenKeyModal,
  onOpenExportsModal,
  keyCount = 0,
  theme = 'dark',
  onToggleTheme
}) {
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

      {/* Hardware Status, Desktop Vault & Gemini Key Pool */}
      <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Dark / Light Theme Toggle Button */}
        <button
          onClick={onToggleTheme}
          style={{
            background: theme === 'light' ? 'rgba(245, 158, 11, 0.12)' : 'var(--bg-card)',
            border: theme === 'light' ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid var(--border)',
            color: theme === 'light' ? '#d97706' : 'var(--text-secondary)',
            padding: '6px 11px',
            borderRadius: 'var(--radius-full, 9999px)',
            fontSize: '0.78rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: theme === 'light' ? '0 0 10px rgba(245, 158, 11, 0.2)' : 'none'
          }}
          title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
        >
          {theme === 'light' ? <Sun size={13} color="#f59e0b" /> : <Moon size={13} color="var(--accent)" />}
          <span>{theme === 'light' ? 'Light' : 'Dark'}</span>
        </button>

        {/* Desktop Exports Vault Button */}
        <button
          onClick={onOpenExportsModal}
          style={{
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            color: '#38bdf8',
            padding: '6px 12px',
            borderRadius: 'var(--radius-full, 9999px)',
            fontSize: '0.78rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 0 10px rgba(56, 189, 248, 0.15)'
          }}
          title="Open Organized Desktop Exports Vault (~/Desktop/CR_Remover_Exports/)"
        >
          <FolderOpen size={13} color="#38bdf8" />
          <span>Desktop Exports</span>
        </button>

        {/* Gemini Multi-Key Pool Button */}
        <button
          onClick={onOpenKeyModal}
          style={{
            background: keyCount > 0 ? 'rgba(99, 102, 241, 0.12)' : 'var(--bg-card)',
            border: keyCount > 0 ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid var(--border)',
            color: keyCount > 0 ? 'var(--accent)' : 'var(--text-muted)',
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
          <Key size={13} color={keyCount > 0 ? 'var(--accent)' : 'var(--text-muted)'} />
          <span>{keyCount > 0 ? `AI Keys (${keyCount})` : 'Set Gemini Keys'}</span>
          {keyCount > 0 && (
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 6px var(--green)' }} />
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

