import React, { useState, useEffect } from 'react'
import { Sparkles, Copy, Check, Hash, Type, MessageSquare, FileText, Share2, RefreshCw } from 'lucide-react'

const NICHES = [
  { id: 'general', label: '🔥 General Viral' },
  { id: 'dark_psychology', label: '🧠 Dark Psychology' },
  { id: 'crazy_facts', label: '🤯 Mindblowing Facts' },
  { id: 'stoic_wisdom', label: '🏛️ Stoic Wisdom' },
  { id: 'wealth_hacks', label: '💰 Wealth & Money' },
  { id: 'scary_mysteries', label: '👻 Creepy Mysteries' },
  { id: 'reddit_stories', label: '🎭 Drama & Stories' },
  { id: 'gaming', label: '🎮 Gaming & Action' },
]

const ANGLES = [
  { id: 'all_angles', label: '⚡ Mixed Viral Angles' },
  { id: 'curiosity_gap_shock', label: '😱 Curiosity & Shock' },
  { id: 'urgent_secret_warning', label: '⚠️ Urgent Warning & Secrets' },
  { id: 'psychological_paradox', label: '🧠 Psychology & Mind Paradox' },
  { id: 'high_stakes_climax', label: '🔥 High Stakes & Ending Twist' },
  { id: 'contrarian_debunk', label: '🛑 Contrarian & Debunk' },
]

export default function CRBypassMetadataLaunchpad({ videoFilename = '', jobResult = null, onOpenThumbnailStudio }) {
  const [topic, setTopic] = useState('')
  const [selectedNiche, setSelectedNiche] = useState('general')
  const [selectedAngle, setSelectedAngle] = useState('all_angles')
  const [isLoading, setIsLoading] = useState(false)
  const [metadata, setMetadata] = useState(null)
  const [copiedKey, setCopiedKey] = useState(null)
  const [activePlatformTab, setActivePlatformTab] = useState('youtube')

  // Clean filename to extract a clean topic
  useEffect(() => {
    let raw = videoFilename || jobResult?.output_filename || 'Viral Video'
    // Remove extension
    let clean = raw.replace(/\.[a-zA-Z0-9]+$/, '')
    // Remove typical prefixes
    clean = clean.replace(/^(cr_clean_|cleaned_|transformed_|voice_|output_|ai_short_)+/gi, '')
    // Replace underscores and dashes with spaces
    clean = clean.replace(/[-_]+/g, ' ')
    // Remove resolution artifacts like 1080p, 4k, 2160p, nvenc, libx264, etc.
    clean = clean.replace(/\b(1080p|2160p|4k|720p|nvenc|h264|hevc|libx264|pro)\b/gi, '')
    // Collapse spaces
    clean = clean.replace(/\s+/g, ' ').trim()
    
    if (!clean) clean = 'Viral Video Secrets'
    setTopic(clean)
    generateMetadata(clean, selectedNiche, selectedAngle)
  }, [videoFilename, jobResult])

  const generateMetadata = async (targetTopic = topic, niche = selectedNiche, angle = selectedAngle) => {
    if (!targetTopic.trim()) return
    setIsLoading(true)
    try {
      const res = await fetch('/api/metadata/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: targetTopic,
          niche: niche,
          script_summary: `Video topic: ${targetTopic} (Seed #${Date.now()})`,
          style_angle: angle,
          gemini_api_key: ''
        })
      })
      if (res.ok) {
        const data = await res.json()
        setMetadata(data)
      }
    } catch (err) {
      console.error('Metadata generation error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = (text, key) => {
    if (!text) return
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const HOOK_LABELS = [
    { label: '🔥 Curiosity Gap', color: '#f59e0b' },
    { label: '⚠️ Warning / Secret', color: '#ef4444' },
    { label: '🤯 Question Hook', color: '#38bdf8' },
    { label: '😱 Climax / Ending', color: '#ec4899' },
    { label: '⚡ Relatable Twist', color: '#8b5cf6' },
    { label: '🔄 Replay Trigger', color: '#10b981' },
  ]

  const getActivePlatformTags = () => {
    if (!metadata) return []
    if (activePlatformTab === 'youtube') return metadata.yt_tags || []
    if (activePlatformTab === 'instagram') return metadata.ig_tags || []
    if (activePlatformTab === 'tiktok') return metadata.tiktok_tags || []
    if (activePlatformTab === 'facebook') return metadata.fb_tags || []
    return metadata.yt_tags || []
  }

  return (
    <div className="cr-metadata-launchpad card" style={{ borderColor: 'rgba(99, 102, 241, 0.35)', background: 'var(--card-bg)' }}>
      {/* Header */}
      <div className="card-header" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '14px' }}>
        <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="card-title-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', borderColor: 'rgba(99, 102, 241, 0.3)' }}>
            <Sparkles size={16} color="#818cf8" />
          </div>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              Upload Launchpad: Viral Titles & Hashtags
              <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>1-Click Copy</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              AI-generated viral hooks, platform hashtags, and SEO captions tailored specifically to this video
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className="btn-ghost"
            onClick={() => generateMetadata(topic, selectedNiche, selectedAngle)}
            disabled={isLoading}
            style={{ fontSize: '0.8rem', padding: '6px 12px', background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)' }}
          >
            <RefreshCw size={13} className={isLoading ? 'spin-anim' : ''} />
            {isLoading ? 'Re-rolling…' : '🎲 Re-roll Fresh Hooks'}
          </button>
        </div>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', paddingTop: '16px' }}>
        {/* Topic Input & Niche / Angle Pills */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter video topic or keywords (e.g. 3 Psychological Tricks, Ghost Caught on Tape)..."
              style={{
                flex: 1,
                padding: '9px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                background: 'var(--input-bg)',
                color: 'var(--text-main)',
                fontSize: '0.88rem'
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') generateMetadata(topic, selectedNiche, selectedAngle)
              }}
            />
            <button
              onClick={() => generateMetadata(topic, selectedNiche, selectedAngle)}
              disabled={isLoading || !topic.trim()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '9px 18px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <Sparkles size={14} />
              {isLoading ? 'Generating…' : 'Generate Hooks'}
            </button>
          </div>

          {/* Creative Angle Filters */}
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 600 }}>
              🧠 Psychological Angle / Tone Filter:
            </div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {ANGLES.map(a => (
                <button
                  key={a.id}
                  onClick={() => {
                    setSelectedAngle(a.id)
                    generateMetadata(topic, selectedNiche, a.id)
                  }}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: selectedAngle === a.id ? '1px solid #f59e0b' : '1px solid var(--border-color)',
                    background: selectedAngle === a.id ? 'rgba(245, 158, 11, 0.2)' : 'var(--surface-bg)',
                    color: selectedAngle === a.id ? '#fbbf24' : 'var(--text-muted)',
                    fontSize: '0.74rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>

          {/* Niche Chips */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {NICHES.map(n => (
              <button
                key={n.id}
                onClick={() => {
                  setSelectedNiche(n.id)
                  generateMetadata(topic, n.id, selectedAngle)
                }}
                style={{
                  padding: '3px 9px',
                  borderRadius: '100px',
                  border: selectedNiche === n.id ? '1px solid #818cf8' : '1px solid var(--border-color)',
                  background: selectedNiche === n.id ? 'rgba(99, 102, 241, 0.2)' : 'var(--card-bg)',
                  color: selectedNiche === n.id ? '#a5b4fc' : 'var(--text-muted)',
                  fontSize: '0.72rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {n.label}
              </button>
            ))}
          </div>
        </div>

        {/* 1. VIRAL TITLES SECTION */}
        <div style={{ background: 'var(--surface-bg)', borderRadius: 'var(--radius-md)', padding: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.86rem', fontWeight: 700, color: 'var(--text-main)' }}>
              <Type size={15} color="#38bdf8" />
              ⚡ High-CTR Viral Titles (Click to Copy)
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Tailored algorithmic hooks & curiosity gaps</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '8px' }}>
            {metadata?.yt_titles && metadata.yt_titles.length > 0 ? (
              metadata.yt_titles.map((titleText, idx) => {
                const isCopied = copiedKey === `title_${idx}`
                const hookInfo = HOOK_LABELS[idx % HOOK_LABELS.length]
                return (
                  <div
                    key={idx}
                    onClick={() => handleCopy(titleText, `title_${idx}`)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-sm)',
                      background: isCopied ? 'rgba(34, 197, 94, 0.12)' : 'var(--card-bg)',
                      border: isCopied ? '1px solid #22c55e' : '1px solid var(--border-color)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      gap: '8px'
                    }}
                    title="Click to copy title"
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        color: hookInfo.color,
                        background: 'rgba(255,255,255,0.05)',
                        padding: '2px 6px',
                        borderRadius: '4px'
                      }}>
                        {hookInfo.label}
                      </span>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleCopy(titleText, `title_${idx}`) }}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '3px 8px',
                          borderRadius: 'var(--radius-xs)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          background: isCopied ? '#22c55e' : 'rgba(255,255,255,0.06)',
                          color: isCopied ? '#fff' : 'var(--text-muted)',
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        {isCopied ? <Check size={11} /> : <Copy size={11} />}
                        {isCopied ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)', lineHeight: '1.35' }}>
                      {titleText}
                    </div>
                  </div>
                )
              })
            ) : (
              <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '8px 0' }}>
                {isLoading ? 'Generating high-CTR titles…' : 'Enter topic above to generate titles'}
              </div>
            )}
          </div>
        </div>

        {/* 2. HASHTAGS BUNDLE (MAIN FEATURE) */}
        <div style={{ background: 'var(--surface-bg)', borderRadius: 'var(--radius-md)', padding: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.86rem', fontWeight: 700, color: 'var(--text-main)' }}>
              <Hash size={15} color="#ec4899" />
              #️⃣ Viral Trending Hashtags (Ready for Uploading)
            </div>

            {/* Copy All Button */}
            {metadata?.all_tags_bundle && (
              <button
                onClick={() => handleCopy(metadata.all_tags_bundle, 'all_tags')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  background: copiedKey === 'all_tags' ? '#22c55e' : 'linear-gradient(135deg, #ec4899, #f43f5e)',
                  color: '#fff',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: '0 2px 8px rgba(236, 72, 153, 0.25)'
                }}
              >
                {copiedKey === 'all_tags' ? <Check size={13} /> : <Copy size={13} />}
                {copiedKey === 'all_tags' ? 'All 15 Hashtags Copied!' : '🚀 Copy All Top 15 Hashtags'}
              </button>
            )}
          </div>

          {/* Platform Tabs */}
          <div className="tab-row" style={{ marginBottom: '10px', borderBottom: '1px solid var(--border-color)' }}>
            {[
              { id: 'youtube', label: '🔴 YouTube Shorts' },
              { id: 'instagram', label: '🟣 Instagram Reels' },
              { id: 'tiktok', label: '⚫ TikTok' },
              { id: 'facebook', label: '🔵 Facebook Reels' }
            ].map(tab => (
              <button
                key={tab.id}
                className={`tab-btn ${activePlatformTab === tab.id ? 'active' : ''}`}
                onClick={() => setActivePlatformTab(tab.id)}
                style={{ fontSize: '0.78rem', padding: '6px 12px' }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tags Display & Copy */}
          {metadata ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {getActivePlatformTags().map((tag, i) => (
                  <span
                    key={i}
                    onClick={() => handleCopy(tag, `tag_${i}`)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: copiedKey === `tag_${i}` ? 'rgba(34, 197, 94, 0.2)' : 'rgba(99, 102, 241, 0.12)',
                      border: copiedKey === `tag_${i}` ? '1px solid #22c55e' : '1px solid rgba(99, 102, 241, 0.25)',
                      color: copiedKey === `tag_${i}` ? '#4ade80' : '#c7d2fe',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    title="Click to copy single tag"
                  >
                    {tag.startsWith('#') ? tag : `#${tag}`}
                  </span>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                <button
                  onClick={() => handleCopy(getActivePlatformTags().join(' '), `platform_${activePlatformTab}`)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 14px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)',
                    background: copiedKey === `platform_${activePlatformTab}` ? 'rgba(34, 197, 94, 0.15)' : 'var(--card-bg)',
                    color: copiedKey === `platform_${activePlatformTab}` ? '#22c55e' : 'var(--text-main)',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {copiedKey === `platform_${activePlatformTab}` ? <Check size={13} /> : <Copy size={13} />}
                  {copiedKey === `platform_${activePlatformTab}` ? 'Platform Tags Copied!' : `Copy ${activePlatformTab.toUpperCase()} Tags`}
                </button>
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              {isLoading ? 'Loading trending tags…' : 'No hashtags available yet.'}
            </div>
          )}
        </div>

        {/* 3. SEO DESCRIPTION & PINNED COMMENT */}
        {metadata && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            {/* Description */}
            <div style={{ background: 'var(--surface-bg)', borderRadius: 'var(--radius-md)', padding: '12px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    <FileText size={14} color="#34d399" />
                    📝 Video Description
                  </div>
                  <button
                    onClick={() => handleCopy(metadata.yt_description, 'desc')}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: '4px',
                      padding: '3px 8px', borderRadius: '4px', border: 'none',
                      background: copiedKey === 'desc' ? '#22c55e' : 'rgba(255,255,255,0.08)',
                      color: '#fff', fontSize: '0.72rem', cursor: 'pointer'
                    }}
                  >
                    {copiedKey === 'desc' ? <Check size={11} /> : <Copy size={11} />}
                    {copiedKey === 'desc' ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4', maxHeight: '75px', overflowY: 'auto' }}>
                  {metadata.yt_description}
                </div>
              </div>
            </div>

            {/* Pinned Comment */}
            <div style={{ background: 'var(--surface-bg)', borderRadius: 'var(--radius-md)', padding: '12px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    <MessageSquare size={14} color="#f59e0b" />
                    📌 Pinned Comment (Algorithm Boost)
                  </div>
                  <button
                    onClick={() => handleCopy(metadata.pinned_comment, 'pinned')}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: '4px',
                      padding: '3px 8px', borderRadius: '4px', border: 'none',
                      background: copiedKey === 'pinned' ? '#22c55e' : 'rgba(255,255,255,0.08)',
                      color: '#fff', fontSize: '0.72rem', cursor: 'pointer'
                    }}
                  >
                    {copiedKey === 'pinned' ? <Check size={11} /> : <Copy size={11} />}
                    {copiedKey === 'pinned' ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.4', maxHeight: '75px', overflowY: 'auto' }}>
                  {metadata.pinned_comment}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
