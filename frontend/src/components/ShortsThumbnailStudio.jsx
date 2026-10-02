import React, { useState, useEffect } from 'react'
import {
  Image as ImageIcon,
  Sparkles,
  Download,
  RefreshCw,
  Sliders,
  Type,
  Flame,
  Check,
  FolderOpen,
  Eye,
  Film,
  Zap,
  Palette
} from 'lucide-react'

const STYLES = [
  { id: 'viral_yellow', name: '🔥 Viral Yellow', color: '#ffe600', badgeColor: '#ef4444', desc: 'MrBeast high-CTR yellow with bold black drop shadow & red badge' },
  { id: 'mrbeast_impact', name: '⚡ Bold Impact', color: '#ffffff', badgeColor: '#3b82f6', desc: 'Ultra-bold clean white typography with blue badge & contrast boost' },
  { id: 'neon_cyber', name: '💎 Cyber Glow', color: '#06b6d4', badgeColor: '#a855f7', desc: 'Electric cyan neon glow with purple cyber badge' },
  { id: 'crimson_shock', name: '🩸 Crimson Shock', color: '#f87171', badgeColor: '#dc2626', desc: 'Blood crimson warning text with urgent red badge' },
  { id: 'golden_luxury', name: '👑 Gold Luxury', color: '#facc15', badgeColor: '#10b981', desc: 'Metallic gold text with emerald green badge for wealth & success' },
  { id: 'dark_mystery', name: '👻 Dark Mystery', color: '#fbbf24', badgeColor: '#1f2937', desc: 'Amber text with deep shadow gradient for secrets & conspiracies' },
]

const QUICK_BADGES = [
  'MUST WATCH',
  'DO NOT SKIP',
  'SHOCKING',
  '99% FAIL',
  'SECRET REVEALED',
  'WAIT FOR END',
  'INSANE TWIST'
]

export default function ShortsThumbnailStudio({
  initialVideoPath = '',
  initialTopic = '',
  onOpenExportsModal
}) {
  const [topic, setTopic] = useState(initialTopic || 'Viral Video Secret')
  const [videoPath, setVideoPath] = useState(initialVideoPath || '')
  const [selectedStyle, setSelectedStyle] = useState('viral_yellow')
  const [hookText, setHookText] = useState('LOOK CLOSER 😱')
  const [badgeText, setBadgeText] = useState('MUST WATCH')
  const [timestampSec, setTimestampSec] = useState(1.2)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isExtractingFrames, setIsExtractingFrames] = useState(false)
  const [isGeneratingHooks, setIsGeneratingHooks] = useState(false)
  
  const [candidateFrames, setCandidateFrames] = useState([])
  const [suggestedHooks, setSuggestedHooks] = useState([
    'LOOK CLOSER 😱',
    'THEY LIED TO YOU ⚠️',
    'DON\'T DO THIS 🛑',
    '99% FAILED THIS 🧠',
    'THE SECRET REVEALED 🤫',
    'THIS CHANGED EVERYTHING ⚡'
  ])
  
  const [thumbnailResult, setThumbnailResult] = useState(null)
  const [copiedNotification, setCopiedNotification] = useState(false)

  // Auto-extract candidate frames if a video path is provided
  useEffect(() => {
    if (videoPath) {
      extractFrames(videoPath)
    }
  }, [videoPath])

  // Generate initial thumbnail on mount
  useEffect(() => {
    generateThumbnail()
  }, [])

  const extractFrames = async (targetPath = videoPath) => {
    if (!targetPath) return
    setIsExtractingFrames(true)
    try {
      const res = await fetch('/api/thumbnail/extract-frames', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_path: targetPath, count: 6 })
      })
      if (res.ok) {
        const data = await res.json()
        setCandidateFrames(data.frames || [])
      }
    } catch (err) {
      console.error('Frame extraction error:', err)
    } finally {
      setIsExtractingFrames(false)
    }
  }

  const generateAIHooks = async () => {
    if (!topic.trim()) return
    setIsGeneratingHooks(true)
    try {
      const res = await fetch('/api/thumbnail/ai-hooks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic.trim() })
      })
      if (res.ok) {
        const data = await res.json()
        if (data.hooks && data.hooks.length > 0) {
          setSuggestedHooks(data.hooks)
          setHookText(data.hooks[0])
        }
      }
    } catch (err) {
      console.error('AI hook generation error:', err)
    } finally {
      setIsGeneratingHooks(false)
    }
  }

  const generateThumbnail = async () => {
    setIsGenerating(true)
    try {
      const res = await fetch('/api/thumbnail/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: videoPath,
          topic: topic,
          hook_text: hookText,
          badge_text: badgeText,
          style_key: selectedStyle,
          timestamp_sec: timestampSec,
          save_to_desktop: true
        })
      })
      if (res.ok) {
        const data = await res.json()
        setThumbnailResult(data)
      }
    } catch (err) {
      console.error('Thumbnail generation error:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="shorts-thumbnail-studio" style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Studio Header Banner */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
        borderColor: 'rgba(99, 102, 241, 0.35)',
        padding: '20px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(245, 158, 11, 0.3)'
          }}>
            <ImageIcon size={24} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              YouTube Shorts & Reels Thumbnail Studio
              <span className="badge badge-purple" style={{ fontSize: '0.72rem' }}>1080x1920 HD</span>
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
              Extract optimal viral video frames, overlay 3D psychological text hooks, and generate high-CTR 9:16 covers.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {onOpenExportsModal && (
            <button
              onClick={onOpenExportsModal}
              className="btn-ghost"
              style={{ fontSize: '0.82rem', padding: '8px 14px' }}
            >
              <FolderOpen size={14} color="#38bdf8" />
              Exports Vault
            </button>
          )}
          <button
            onClick={generateThumbnail}
            disabled={isGenerating}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '9px 20px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
              color: '#fff',
              fontSize: '0.88rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(239, 68, 68, 0.3)'
            }}
          >
            <RefreshCw size={15} className={isGenerating ? 'spin-anim' : ''} />
            {isGenerating ? 'Rendering Cover…' : 'Render HD Cover'}
          </button>
        </div>
      </div>

      {/* Main Studio Grid: Left Controls (60%) vs Right Live Preview (40%) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.4fr) minmax(360px, 1fr)', gap: '20px', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: Controls & Customization */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* 1. Topic & Video Source */}
          <div className="card" style={{ padding: '16px', background: 'var(--card-bg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px' }}>
              <Film size={16} color="#38bdf8" />
              1. Video Topic & Frame Source
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.76rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Video Topic or Niche Keywords</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. 3 Psychological Secrets, Ghost Caught on Tape, Luxury Wealth..."
                    style={{
                      flex: 1,
                      padding: '9px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-color)',
                      background: 'var(--input-bg)',
                      color: 'var(--text-main)',
                      fontSize: '0.86rem'
                    }}
                  />
                  <button
                    onClick={generateAIHooks}
                    disabled={isGeneratingHooks || !topic.trim()}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 14px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid rgba(99, 102, 241, 0.4)',
                      background: 'rgba(99, 102, 241, 0.15)',
                      color: '#a5b4fc',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                    title="Generate AI Hook Suggestions"
                  >
                    <Sparkles size={13} className={isGeneratingHooks ? 'spin-anim' : ''} />
                    {isGeneratingHooks ? 'Generating…' : 'AI Hooks'}
                  </button>
                </div>
              </div>

              {/* Candidate Video Frames Scrubber */}
              {candidateFrames.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <label style={{ fontSize: '0.76rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                    Select Action Frame from Video ({candidateFrames.length} candidates extracted):
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '6px' }}>
                    {candidateFrames.map((f, idx) => (
                      <div
                        key={idx}
                        onClick={() => {
                          setTimestampSec(f.timestamp)
                          generateThumbnail()
                        }}
                        style={{
                          aspectRatio: '9/16',
                          borderRadius: '6px',
                          overflow: 'hidden',
                          border: Math.abs(timestampSec - f.timestamp) < 0.1 ? '2px solid #f59e0b' : '1px solid var(--border-color)',
                          cursor: 'pointer',
                          position: 'relative',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <img src={f.frame_url} alt={`Frame ${idx}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        <span style={{
                          position: 'absolute',
                          bottom: '2px',
                          right: '2px',
                          background: 'rgba(0,0,0,0.7)',
                          color: '#fff',
                          fontSize: '0.62rem',
                          padding: '1px 3px',
                          borderRadius: '2px'
                        }}>
                          {f.timestamp}s
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 2. 3D Hook Text & AI Suggestions */}
          <div className="card" style={{ padding: '16px', background: 'var(--card-bg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)' }}>
                <Type size={16} color="#eab308" />
                2. 3D Viral Hook Text (Click to Apply)
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Keep under 4 words for maximum mobile CTR</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <input
                type="text"
                value={hookText}
                onChange={(e) => setHookText(e.target.value.toUpperCase())}
                placeholder="e.g. LOOK CLOSER 😱, 99% FAILED 🧠, THEY LIED ⚠️..."
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  background: 'var(--input-bg)',
                  color: 'var(--text-main)',
                  fontSize: '0.95rem',
                  fontWeight: 800,
                  letterSpacing: '0.5px'
                }}
              />

              {/* Hook Suggestion Pills */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '2px' }}>
                {suggestedHooks.map((h, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setHookText(h)
                      generateThumbnail()
                    }}
                    style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      border: hookText === h ? '1px solid #f59e0b' : '1px solid var(--border-color)',
                      background: hookText === h ? 'rgba(245, 158, 11, 0.2)' : 'var(--surface-bg)',
                      color: hookText === h ? '#fbbf24' : 'var(--text-muted)',
                      fontSize: '0.76rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 3. Top Pill Badge */}
          <div className="card" style={{ padding: '16px', background: 'var(--card-bg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px' }}>
              <Flame size={16} color="#ef4444" />
              3. Top Retention Pill Badge
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={badgeText}
                  onChange={(e) => setBadgeText(e.target.value.toUpperCase())}
                  placeholder="e.g. MUST WATCH, DO NOT SKIP, SHOCKING..."
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)',
                    background: 'var(--input-bg)',
                    color: 'var(--text-main)',
                    fontSize: '0.84rem',
                    fontWeight: 700
                  }}
                />
                <button
                  onClick={() => setBadgeText('')}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)',
                    background: 'var(--surface-bg)',
                    color: 'var(--text-muted)',
                    fontSize: '0.78rem',
                    cursor: 'pointer'
                  }}
                >
                  Clear Badge
                </button>
              </div>

              {/* Quick Badge Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {QUICK_BADGES.map((b, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setBadgeText(b)
                      generateThumbnail()
                    }}
                    style={{
                      padding: '3px 9px',
                      borderRadius: '100px',
                      border: badgeText === b ? '1px solid #ef4444' : '1px solid var(--border-color)',
                      background: badgeText === b ? 'rgba(239, 68, 68, 0.2)' : 'var(--surface-bg)',
                      color: badgeText === b ? '#fca5a5' : 'var(--text-muted)',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    🔥 {b}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 4. High-CTR Style Preset Cards */}
          <div className="card" style={{ padding: '16px', background: 'var(--card-bg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px' }}>
              <Palette size={16} color="#8b5cf6" />
              4. High-CTR Typography & Contrast Style
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px' }}>
              {STYLES.map(s => {
                const isSelected = selectedStyle === s.id
                return (
                  <div
                    key={s.id}
                    onClick={() => {
                      setSelectedStyle(s.id)
                      generateThumbnail()
                    }}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--surface-bg)',
                      border: isSelected ? '2px solid #818cf8' : '1px solid var(--border-color)',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 700, color: s.color }}>
                        {s.name}
                      </span>
                      {isSelected && <Check size={13} color="#818cf8" />}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>
                      {s.desc}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Live 9:16 Mobile Mockup & Export */}
        <div style={{ position: 'sticky', top: '20px', display: 'flex', flexDirection: 'column', gap: '14px', alignItems: 'center' }}>
          
          <div style={{
            width: '100%',
            maxWidth: '340px',
            aspectRatio: '9/16',
            borderRadius: '24px',
            border: '4px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(99, 102, 241, 0.2)',
            overflow: 'hidden',
            background: '#090a0f',
            position: 'relative'
          }}>
            {thumbnailResult?.cover_url ? (
              <img
                src={`${thumbnailResult.cover_url}?t=${Date.now()}`}
                alt="Shorts Thumbnail Preview"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : (
              <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '10px' }}>
                <ImageIcon size={36} />
                <span style={{ fontSize: '0.84rem' }}>{isGenerating ? 'Rendering HD Thumbnail…' : 'No Cover Rendered'}</span>
              </div>
            )}

            {/* Shorts UI Overlay (Simulating real YouTube Shorts / Reels screen) */}
            <div style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              right: '50px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              pointerEvents: 'none'
            }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#fff', textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}>
                @CR_Remover_Studio
              </span>
              <span style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.85)', textShadow: '0 1px 3px rgba(0,0,0,0.8)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {topic} #shorts #viral #fyp
              </span>
            </div>

            {/* Right Action Icons Mockup */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              right: '10px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '12px',
              pointerEvents: 'none'
            }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '11px', color: '#fff' }}>👍</span>
              </div>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '11px', color: '#fff' }}>💬</span>
              </div>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '11px', color: '#fff' }}>↗️</span>
              </div>
            </div>
          </div>

          {/* Download & Action Buttons */}
          {thumbnailResult?.cover_url && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%', maxWidth: '340px' }}>
              <a
                href={thumbnailResult.cover_url}
                download={`cover_${Date.now()}.jpg`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  width: '100%',
                  padding: '11px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                  color: '#fff',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  textDecoration: 'none',
                  boxShadow: '0 4px 12px rgba(34, 197, 94, 0.3)'
                }}
              >
                <Download size={16} />
                Download HD Cover (1080x1920)
              </a>

              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                📁 Auto-saved to <code style={{ color: 'var(--accent)' }}>~/Desktop/CR_Remover_Exports/05_Thumbnails_Covers/</code>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
