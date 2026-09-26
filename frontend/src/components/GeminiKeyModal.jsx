import React, { useState, useEffect } from 'react'
import { Key, ShieldCheck, Zap, AlertTriangle, X, Check, Trash2, Plus, RefreshCw, ExternalLink, Sparkles } from 'lucide-react'

export default function GeminiKeyModal({ isOpen, onClose, onKeysUpdated }) {
  const [keysInput, setKeysInput] = useState('')
  const [poolStatus, setPoolStatus] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResults, setTestResults] = useState({})
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Fetch pool status from backend
  const fetchPoolStatus = async () => {
    setIsLoading(true)
    try {
      const res = await fetch('/api/gemini/pool-status')
      if (res.ok) {
        const data = await res.json()
        setPoolStatus(data)
      }
    } catch (err) {
      console.error('Failed to fetch Gemini pool status:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchPoolStatus()
      // Check localStorage for any local keys
      const localKeys = localStorage.getItem('cr_gemini_api_keys') || localStorage.getItem('cr_gemini_api_key') || ''
      if (localKeys && !keysInput) {
        setKeysInput(localKeys)
      }
    }
  }, [isOpen])

  if (!isOpen) return null

  // Add new keys to pool
  const handleAddKeys = async () => {
    if (!keysInput.trim()) return
    setIsLoading(true)
    try {
      const res = await fetch('/api/gemini/pool-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keys_text: keysInput,
          persist: true
        })
      })
      if (res.ok) {
        const data = await res.json()
        setPoolStatus(data.pool)
        localStorage.setItem('cr_gemini_api_keys', keysInput.trim())
        localStorage.setItem('cr_gemini_api_key', keysInput.trim())
        setSaveSuccess(true)
        setTimeout(() => setSaveSuccess(false), 2500)
        if (onKeysUpdated) onKeysUpdated(data.pool)
      }
    } catch (err) {
      alert('Error updating keys: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  // Remove a single key
  const handleRemoveKey = async (keyToRemove) => {
    try {
      const res = await fetch('/api/gemini/remove-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: keyToRemove })
      })
      if (res.ok) {
        const data = await res.json()
        setPoolStatus(data.pool)
        // Update localStorage
        const remainingKeys = data.pool.keys.map(k => k.key).join('\n')
        localStorage.setItem('cr_gemini_api_keys', remainingKeys)
        localStorage.setItem('cr_gemini_api_key', remainingKeys)
        setKeysInput(remainingKeys)
        if (onKeysUpdated) onKeysUpdated(data.pool)
      }
    } catch (err) {
      console.error('Error removing key:', err)
    }
  }

  // Test all keys in the pool
  const handleTestAllKeys = async () => {
    setIsTesting(true)
    try {
      const res = await fetch('/api/gemini/test-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keys_text: keysInput
        })
      })
      if (res.ok) {
        const data = await res.json()
        setPoolStatus(data.pool)
        const resultMap = {}
        data.results.forEach(r => {
          resultMap[r.masked] = r
        })
        setTestResults(resultMap)
        if (onKeysUpdated) onKeysUpdated(data.pool)
      }
    } catch (err) {
      alert('Error testing keys: ' + err.message)
    } finally {
      setIsTesting(false)
    }
  }

  const keysList = poolStatus?.keys || []
  const activeCount = poolStatus?.active_keys || 0
  const rateLimitedCount = poolStatus?.rate_limited_keys || 0

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(5, 7, 12, 0.85)',
      backdropFilter: 'blur(10px)',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'var(--bg-surface, #111318)',
        border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.12))',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '680px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 24px 64px rgba(0, 0, 0, 0.8), 0 0 32px rgba(99, 102, 241, 0.15)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(180deg, rgba(99, 102, 241, 0.08) 0%, transparent 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
            }}>
              <Key size={20} color="#fff" />
            </div>
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                Google Gemini Multi-Key Pool
                <span style={{
                  fontSize: '0.72rem',
                  padding: '2px 8px',
                  borderRadius: '20px',
                  background: activeCount > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                  color: activeCount > 0 ? '#10b981' : '#f59e0b',
                  border: activeCount > 0 ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
                  fontWeight: 600
                }}>
                  {activeCount} Active Key{activeCount !== 1 ? 's' : ''}
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Auto-rotates & fails over instantly when rate limits (429 / Quota) are reached
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '6px',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Tip Banner */}
          <div style={{
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            borderRadius: '12px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Sparkles size={18} color="#818cf8" />
              <span style={{ fontSize: '0.83rem', color: '#cbd5e1' }}>
                Create multiple free API keys in Google AI Studio to multiply your daily generation capacity!
              </span>
            </div>
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '0.78rem',
                color: '#818cf8',
                textDecoration: 'none',
                background: 'rgba(99, 102, 241, 0.15)',
                padding: '5px 10px',
                borderRadius: '6px',
                fontWeight: 600,
                whiteSpace: 'nowrap'
              }}
            >
              Get Free Keys <ExternalLink size={12} />
            </a>
          </div>

          {/* Key Input Field */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '8px' }}>
              Paste Gemini API Keys (1 or multiple, comma or newline separated):
            </label>
            <textarea
              rows={4}
              placeholder={`AIzaSyExampleKey1...\nAIzaSyExampleKey2...\nAIzaSyExampleKey3...`}
              value={keysInput}
              onChange={(e) => setKeysInput(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '10px',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                background: 'var(--bg-input, #0c0e14)',
                color: '#f8fafc',
                fontSize: '0.86rem',
                fontFamily: 'monospace',
                outline: 'none',
                resize: 'vertical'
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
              <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                Accepts multiple keys separated by commas or lines. Keys are securely stored locally.
              </span>
              <button
                onClick={handleAddKeys}
                disabled={isLoading || !keysInput.trim()}
                style={{
                  background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                  color: '#fff',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  fontSize: '0.84rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  opacity: (!keysInput.trim() || isLoading) ? 0.6 : 1
                }}
              >
                {saveSuccess ? <Check size={14} color="#10b981" /> : <Plus size={14} />}
                {saveSuccess ? 'Saved & Activated!' : 'Save to Pool'}
              </button>
            </div>
          </div>

          {/* Active Keys Section */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={16} color="#10b981" />
                <span>Configured Pool Keys ({keysList.length})</span>
              </div>
              <button
                onClick={handleTestAllKeys}
                disabled={isTesting || keysList.length === 0}
                style={{
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: '#94a3b8',
                  padding: '5px 12px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <RefreshCw size={12} className={isTesting ? 'spin-anim' : ''} />
                {isTesting ? 'Testing All Keys...' : '⚡ Live Test All Keys'}
              </button>
            </div>

            {keysList.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '28px 16px',
                background: 'rgba(255, 255, 255, 0.02)',
                borderRadius: '10px',
                border: '1px dashed rgba(255, 255, 255, 0.1)',
                color: '#64748b',
                fontSize: '0.85rem'
              }}>
                No API keys in pool yet. Paste one or more keys above to enable AI features with failover.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {keysList.map((kObj, idx) => {
                  const testRes = testResults[kObj.masked]
                  const isLimited = kObj.status === 'rate_limited' || (testRes && testRes.status === 'rate_limited')
                  const isInvalid = kObj.status === 'invalid' || (testRes && testRes.status === 'invalid')
                  const isActive = !isLimited && !isInvalid

                  return (
                    <div
                      key={kObj.masked || idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '10px 14px',
                        background: 'var(--bg-card, #16181f)',
                        border: '1px solid rgba(255, 255, 255, 0.06)',
                        borderRadius: '10px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{
                          fontSize: '0.75rem',
                          fontFamily: 'monospace',
                          color: '#64748b',
                          background: 'rgba(255, 255, 255, 0.05)',
                          padding: '2px 6px',
                          borderRadius: '4px'
                        }}>
                          #{idx + 1}
                        </span>
                        <span style={{ fontFamily: 'monospace', fontSize: '0.86rem', color: '#e2e8f0' }}>
                          {kObj.masked}
                        </span>
                        
                        {/* Status Badge */}
                        {isActive && (
                          <span style={{
                            fontSize: '0.72rem',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: 'rgba(16, 185, 129, 0.12)',
                            color: '#10b981',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
                            Active Ready
                          </span>
                        )}
                        {isLimited && (
                          <span style={{
                            fontSize: '0.72rem',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: 'rgba(245, 158, 11, 0.12)',
                            color: '#f59e0b',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <AlertTriangle size={10} />
                            Rate Limited (Cooldown)
                          </span>
                        )}
                        {isInvalid && (
                          <span style={{
                            fontSize: '0.72rem',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: 'rgba(239, 68, 68, 0.12)',
                            color: '#ef4444',
                            fontWeight: 600
                          }}>
                            Invalid Key
                          </span>
                        )}

                        {/* Latency if available */}
                        {(kObj.last_latency_ms || testRes?.latency_ms) && (
                          <span style={{
                            fontSize: '0.72rem',
                            color: '#818cf8',
                            background: 'rgba(99, 102, 241, 0.1)',
                            padding: '2px 6px',
                            borderRadius: '6px',
                            fontWeight: 600
                          }}>
                            ⚡ {testRes?.latency_ms || kObj.last_latency_ms}ms
                          </span>
                        )}

                        {/* Success counter */}
                        {kObj.success_count > 0 && (
                          <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                            ✓ {kObj.success_count} used
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => handleRemoveKey(kObj.key || kObj.masked)}
                        title="Remove key from pool"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#64748b',
                          cursor: 'pointer',
                          padding: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'color 0.2s ease'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.color = '#ef4444'}
                        onMouseLeave={(e) => e.currentTarget.style.color = '#64748b'}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(0, 0, 0, 0.2)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Zap size={14} color="#6366f1" />
            <span>Multi-Model Support: 2.0 Flash • 1.5 Flash • 2.0 Flash-Lite • 1.5 Pro</span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              color: '#f8fafc',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              padding: '8px 20px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
