import React, { useState, useEffect, useRef } from 'react'
import { Rocket, Sparkles, Key, CheckCircle2, Folder, Copy, Check, Loader2, AlertCircle, Play, Download, ThumbsUp, ThumbsDown, Trash2, CheckCheck, X, Flame, Clock, Globe, Filter, Compass, Award } from 'lucide-react'

export default function AutoViralStudio() {
  const [topic, setTopic] = useState('Dark Psychology Facts')
  const [count, setCount] = useState(3)
  const [geminiApiKey, setGeminiApiKey] = useState('')
  const [selectedPreset, setSelectedPreset] = useState('youtube_bypass')
  
  // 5 New Viral Filters
  const [minViews, setMinViews] = useState(500000)
  const [recency, setRecency] = useState('this_year')
  const [languageLock, setLanguageLock] = useState('en')
  const [channelFeed, setChannelFeed] = useState('')
  const [activeTab, setActiveTab] = useState('topic') // 'topic' | 'curated'

  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStage, setCurrentStage] = useState('')
  const [errorMessage, setErrorMessage] = useState(null)
  const [results, setResults] = useState([])
  const [copiedIndex, setCopiedIndex] = useState(null)
  const [actionLoading, setActionLoading] = useState({})

  const pollTimerRef = useRef(null)

  const quickTopics = [
    'Dark Psychology Facts',
    'Mind Bending Paradoxes',
    'Crazy Unbelievable Facts',
    'Satisfying ASMR Restoration',
    'Sigma Motivation & Discipline',
    'Minecraft Parkour Facts'
  ]

  const curatedNiches = [
    { id: 'psychology', name: '🧠 Dark Psychology', channels: '@Psych2go, @BrainyDose', topic: 'Psychology Facts' },
    { id: 'paradoxes', name: '🌌 Mind Paradoxes', channels: '@Kurzgesagt, @WhatIfScienceShow', topic: 'Mind Bending Paradoxes' },
    { id: 'facts', name: '🤯 Unbelievable Facts', channels: '@BeAmazed, @FactVerse', topic: 'Crazy Facts' },
    { id: 'motivation', name: '⚡ High-Stakes Motivation', channels: '@Motiversity, @MotivationHub', topic: 'Sigma Male Motivation' },
    { id: 'restoration', name: '🛠️ ASMR Restoration', channels: '@RestorationVideos', topic: 'Satisfying Restoration' }
  ]

  // Load saved Gemini API Key from localStorage
  useEffect(() => {
    const savedKey = localStorage.getItem('cr_gemini_api_key')
    if (savedKey) {
      setGeminiApiKey(savedKey)
    }
  }, [])

  const handleSaveApiKey = (val) => {
    setGeminiApiKey(val)
    localStorage.setItem('cr_gemini_api_key', val)
  }

  const handleSelectCurated = (niche) => {
    setChannelFeed(niche.id)
    setTopic(niche.topic)
  }

  const handleStartAutoPipeline = async () => {
    if (!topic.trim()) {
      alert('Please enter a topic, niche keyword, or select a curated channel!')
      return
    }

    setIsProcessing(true)
    setProgress(5)
    setCurrentStage('Initializing Gemini AI Viral Strategist...')
    setErrorMessage(null)
    setResults([])

    try {
      const res = await fetch('/api/auto-viral/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic.trim(),
          count: parseInt(count),
          gemini_api_key: geminiApiKey.trim(),
          preset: selectedPreset,
          min_views: parseInt(minViews),
          recency: recency,
          language_lock: languageLock,
          channel_feed: channelFeed
        })
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to start pipeline')
      }

      const data = await res.json()
      pollStatus(data.job_id)
    } catch (err) {
      setErrorMessage(err.message)
      setIsProcessing(false)
    }
  }

  const pollStatus = (jobId) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current)

    pollTimerRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/auto-viral/status/${jobId}`)
        if (!res.ok) return
        const data = await res.json()

        setProgress(data.progress || 0)
        setCurrentStage(data.current_stage || 'Processing...')

        if (data.status === 'completed') {
          clearInterval(pollTimerRef.current)
          setIsProcessing(false)
          setResults(data.results || [])
        } else if (data.status === 'failed') {
          clearInterval(pollTimerRef.current)
          setIsProcessing(false)
          setErrorMessage(data.error_message || 'Pipeline encountered an error')
        }
      } catch (e) {
        console.error('Polling error:', e)
      }
    }, 1500)
  }

  // Handle Accept (Save to Downloads)
  const handleAcceptVideo = async (item, idx) => {
    setActionLoading((prev) => ({ ...prev, [idx]: 'accepting' }))
    try {
      const res = await fetch('/api/auto-viral/accept', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clean_id: item.clean_id,
          filename: item.filename,
          titles: item.titles,
          hook: item.hook,
          description: item.description,
          original_title: item.original_title
        })
      })

      if (!res.ok) throw new Error('Failed to save to Downloads')

      setResults((prev) =>
        prev.map((v, i) => (i === idx ? { ...v, status: 'accepted' } : v))
      )
    } catch (e) {
      alert('Error saving video: ' + e.message)
    } finally {
      setActionLoading((prev) => ({ ...prev, [idx]: null }))
    }
  }

  // Handle Reject (Discard & Delete Temp)
  const handleRejectVideo = async (item, idx) => {
    setActionLoading((prev) => ({ ...prev, [idx]: 'rejecting' }))
    try {
      await fetch('/api/auto-viral/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clean_id: item.clean_id })
      })

      setResults((prev) =>
        prev.map((v, i) => (i === idx ? { ...v, status: 'rejected' } : v))
      )
    } catch (e) {
      console.error('Error rejecting video:', e)
    } finally {
      setActionLoading((prev) => ({ ...prev, [idx]: null }))
    }
  }

  // Accept All Pending Videos
  const handleAcceptAll = async () => {
    for (let i = 0; i < results.length; i++) {
      if (results[i].status !== 'accepted' && results[i].status !== 'rejected') {
        await handleAcceptVideo(results[i], i)
      }
    }
  }

  // Reject All Pending Videos
  const handleRejectAll = async () => {
    for (let i = 0; i < results.length; i++) {
      if (results[i].status !== 'accepted' && results[i].status !== 'rejected') {
        await handleRejectVideo(results[i], i)
      }
    }
  }

  const copyToClipboard = (text, idx) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const pendingCount = results.filter((r) => r.status === 'pending').length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Main Configuration Card */}
      <div className="glass-card">
        <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Rocket size={22} color="var(--accent-pink)" />
            <span className="gradient-text">AI Auto-Viral Shorts Studio</span>
          </div>

          {/* Mode Tabs */}
          <div style={{ display: 'flex', background: 'rgba(255, 255, 255, 0.05)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <button
              onClick={() => { setActiveTab('topic'); setChannelFeed(''); }}
              style={{
                background: activeTab === 'topic' ? 'var(--accent-purple)' : 'transparent',
                color: activeTab === 'topic' ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                padding: '5px 12px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              🔍 Topic Search
            </button>
            <button
              onClick={() => setActiveTab('curated')}
              style={{
                background: activeTab === 'curated' ? 'var(--accent-purple)' : 'transparent',
                color: activeTab === 'curated' ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                padding: '5px 12px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              ⭐ Top Curated Channels
            </button>
          </div>
        </div>

        <div className="card-subtitle">
          Gemini AI researches viral search hooks, enforces <b>15s–60s</b> duration, pulls <b>1M+ view</b> Shorts, scores retention, and applies GPU anti-copyright transforms.
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', marginTop: '14px' }}>
          
          {/* Active Tab 1: Topic Search */}
          {activeTab === 'topic' ? (
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '8px' }}>
                🔍 Topic / Niche Keyword (or @channel handle):
              </label>
              <input
                type="text"
                placeholder="e.g. Dark Psychology Facts, Mind Bending Paradoxes, @Kurzgesagt..."
                value={topic}
                onChange={(e) => { setTopic(e.target.value); setChannelFeed(''); }}
                style={{
                  width: '100%',
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem',
                  outline: 'none'
                }}
              />

              {/* Quick Topic Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '10px' }}>
                {quickTopics.map((item) => (
                  <button
                    key={item}
                    onClick={() => { setTopic(item); setChannelFeed(''); }}
                    style={{
                      background: topic === item ? 'rgba(139, 92, 246, 0.25)' : 'rgba(255, 255, 255, 0.05)',
                      border: topic === item ? '1px solid var(--accent-purple)' : '1px solid var(--border-subtle)',
                      color: topic === item ? '#fff' : 'var(--text-secondary)',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      cursor: 'pointer'
                    }}
                  >
                    + {item}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Active Tab 2: Curated Channels */
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-pink)', display: 'block', marginBottom: '8px' }}>
                ⭐ Select a Proven Mega-Viral Channel Hub:
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                {curatedNiches.map((niche) => (
                  <div
                    key={niche.id}
                    onClick={() => handleSelectCurated(niche)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: channelFeed === niche.id ? 'rgba(236, 72, 153, 0.15)' : 'var(--bg-input)',
                      border: channelFeed === niche.id ? '1px solid var(--accent-pink)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>{niche.name}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{niche.channels}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 5 Pro Viral Filters Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '14px', background: 'rgba(255, 255, 255, 0.02)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            
            {/* 1. Min View Count */}
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px' }}>
                <Flame size={13} />
                <span>Min View Count:</span>
              </label>
              <select
                value={minViews}
                onChange={(e) => setMinViews(parseInt(e.target.value))}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', background: 'var(--bg-input)', color: '#fff', border: '1px solid var(--border-subtle)', fontSize: '0.82rem', outline: 'none' }}
              >
                <option value={1000000}>🥇 1M+ Views (Proven Viral)</option>
                <option value={500000}>🥈 500K+ Views (Fast)</option>
                <option value={5000000}>💎 5M+ Mega-Viral</option>
                <option value={100000}>🥉 100K+ (Broad)</option>
              </select>
            </div>

            {/* 2. Recency / Velocity */}
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px' }}>
                <Clock size={13} />
                <span>Upload Recency:</span>
              </label>
              <select
                value={recency}
                onChange={(e) => setRecency(e.target.value)}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', background: 'var(--bg-input)', color: '#fff', border: '1px solid var(--border-subtle)', fontSize: '0.82rem', outline: 'none' }}
              >
                <option value="this_year">📅 This Year (Trending)</option>
                <option value="this_month">🚀 This Month (Fresh Explosive)</option>
                <option value="all_time">🏆 All-Time Legends</option>
              </select>
            </div>

            {/* 3. Language Lock */}
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px' }}>
                <Globe size={13} />
                <span>Language Lock:</span>
              </label>
              <select
                value={languageLock}
                onChange={(e) => setLanguageLock(e.target.value)}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', background: 'var(--bg-input)', color: '#fff', border: '1px solid var(--border-subtle)', fontSize: '0.82rem', outline: 'none' }}
              >
                <option value="en">🇬🇧 English Only (Filtered)</option>
                <option value="any">🌐 Any Language</option>
              </select>
            </div>

            {/* 4. Shorts Count */}
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)', display: 'block', marginBottom: '6px' }}>
                🎞️ Shorts Count:
              </label>
              <select
                value={count}
                onChange={(e) => setCount(parseInt(e.target.value))}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', background: 'var(--bg-input)', color: '#fff', border: '1px solid var(--border-subtle)', fontSize: '0.82rem', outline: 'none' }}
              >
                <option value={1}>1 Viral Short</option>
                <option value={3}>3 Viral Shorts (Recommended)</option>
                <option value={5}>5 Viral Shorts</option>
              </select>
            </div>

            {/* 5. Preset Profile */}
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent-purple)', display: 'block', marginBottom: '6px' }}>
                ⚡ GPU Transform Preset:
              </label>
              <select
                value={selectedPreset}
                onChange={(e) => setSelectedPreset(e.target.value)}
                style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', background: 'var(--bg-input)', color: '#fff', border: '1px solid var(--border-subtle)', fontSize: '0.82rem', outline: 'none' }}
              >
                <option value="youtube_bypass">⚡ YouTube Content ID Bypass</option>
                <option value="insta_shorts">📱 Instagram & TikTok Mode</option>
                <option value="ai_deep_clean">🤖 AI Deep Clean (Demucs)</option>
              </select>
            </div>

          </div>

          {/* Gemini API Key */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Key size={14} />
                <span>Google Gemini API Key (Flash-Lite Preloaded):</span>
              </label>
              <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>Active (3.1/2.0 Flash-Lite)</span>
            </div>
            <input
              type="password"
              placeholder="Paste Gemini API Key"
              value={geminiApiKey}
              onChange={(e) => handleSaveApiKey(e.target.value)}
              style={{
                width: '100%',
                padding: '11px 16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-input)',
                color: 'var(--text-primary)',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          {/* Action Button */}
          <button
            className="btn-primary"
            disabled={!topic.trim() || isProcessing}
            onClick={handleStartAutoPipeline}
            style={{ marginTop: '6px' }}
          >
            {isProcessing ? (
              <>
                <Loader2 size={20} style={{ animation: 'spin 1.5s linear infinite' }} />
                <span>Hunting 1M+ Shorts & Scoring Retention ({progress}%)...</span>
              </>
            ) : (
              <>
                <Rocket size={20} />
                <span>🚀 Hunt Viral Shorts (15s–60s) & AI Clean</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live Processing Card */}
      {isProcessing && (
        <div className="glass-card" style={{ border: '1px solid rgba(139, 92, 246, 0.4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <Loader2 size={24} color="#c4b5fd" style={{ animation: 'spin 1.5s linear infinite' }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '1rem' }}>Gemini AI Research & GPU Pipeline Running</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{currentStage}</div>
            </div>
            <div style={{ marginLeft: 'auto', fontWeight: 800, color: 'var(--accent-purple)', fontSize: '1.2rem' }}>
              {progress}%
            </div>
          </div>

          <div className="progress-bar-track" style={{ height: '10px' }}>
            <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      )}

      {/* Error Card */}
      {errorMessage && (
        <div className="glass-card" style={{ border: '1px solid rgba(239, 68, 68, 0.4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#ef4444' }}>
            <AlertCircle size={20} />
            <span style={{ fontWeight: 700 }}>Search Note:</span>
            <span style={{ fontSize: '0.9rem' }}>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Review Header Bar */}
      {results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-card" style={{ border: '1px solid rgba(139, 92, 246, 0.4)', padding: '18px 24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Award size={24} color="var(--accent-pink)" />
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1.15rem' }}>
                    {results.length} Proven Viral Shorts Ready for Review
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    All videos verified strictly between <b>15s and 60s</b> with <b>AI Retention Hook Scores</b>.
                  </div>
                </div>
              </div>

              {/* Bulk Actions */}
              {pendingCount > 0 && (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={handleAcceptAll}
                    style={{
                      background: 'linear-gradient(135deg, var(--accent-emerald), #059669)',
                      border: 'none',
                      color: 'white',
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
                    }}
                  >
                    <CheckCheck size={14} />
                    <span>Accept All ({pendingCount})</span>
                  </button>

                  <button
                    onClick={handleRejectAll}
                    style={{
                      background: 'rgba(239, 68, 68, 0.15)',
                      border: '1px solid rgba(239, 68, 68, 0.4)',
                      color: '#f87171',
                      padding: '8px 14px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <X size={14} />
                    <span>Reject All</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Video Result Cards */}
          {results.map((item, idx) => {
            const isAccepted = item.status === 'accepted'
            const isRejected = item.status === 'rejected'
            const isActionBusy = !!actionLoading[idx]

            if (isRejected) {
              return (
                <div
                  key={idx}
                  className="glass-card"
                  style={{
                    opacity: 0.5,
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    border: '1px solid rgba(239, 68, 68, 0.2)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Trash2 size={18} color="#ef4444" />
                    <span style={{ fontSize: '0.88rem', textDecoration: 'line-through', color: 'var(--text-muted)' }}>
                      {item.filename}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#ef4444', fontWeight: 600 }}>[Discarded & Deleted]</span>
                  </div>
                  <button
                    onClick={() => handleAcceptVideo(item, idx)}
                    style={{
                      background: 'transparent',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      cursor: 'pointer'
                    }}
                  >
                    Undo & Accept
                  </button>
                </div>
              )
            }

            return (
              <div
                key={idx}
                className="glass-card"
                style={{
                  padding: '24px',
                  border: isAccepted ? '1px solid rgba(16, 185, 129, 0.5)' : '1px solid var(--border-subtle)',
                  background: isAccepted ? 'rgba(16, 185, 129, 0.04)' : undefined
                }}
              >
                {/* Header of Video Card */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--accent-purple)', fontWeight: 800, textTransform: 'uppercase', background: 'rgba(139, 92, 246, 0.15)', padding: '2px 8px', borderRadius: '4px' }}>
                      Short #{idx + 1}
                    </span>
                    
                    {/* Gemini AI Viral Hook Score */}
                    <span style={{ fontSize: '0.8rem', color: '#10b981', background: 'rgba(16, 185, 129, 0.18)', border: '1px solid rgba(16, 185, 129, 0.5)', padding: '3px 10px', borderRadius: '4px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Award size={13} />
                      <span>{item.viral_score || 95}/100 Hook Score</span>
                    </span>

                    {/* View Count Badge */}
                    <span style={{ fontSize: '0.78rem', color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                      🔥 {item.formatted_views || '1M+ Views'}
                    </span>

                    {/* Duration Badge */}
                    <span style={{ fontSize: '0.78rem', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.4)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                      ⏱️ {item.formatted_duration || '45s'}
                    </span>

                    {/* English Verified */}
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', background: 'rgba(255, 255, 255, 0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                      🇬🇧 English
                    </span>
                  </div>

                  {/* Status Badge or Accept Buttons */}
                  {isAccepted ? (
                    <div className="status-pill active" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={14} color="#10b981" />
                      <span>Saved in ~/Downloads/CR_Remover_Ready/</span>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => handleAcceptVideo(item, idx)}
                        disabled={isActionBusy}
                        style={{
                          background: 'linear-gradient(135deg, var(--accent-emerald), #059669)',
                          border: 'none',
                          color: 'white',
                          padding: '8px 18px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.85rem',
                          fontWeight: 700,
                          cursor: isActionBusy ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        {actionLoading[idx] === 'accepting' ? (
                          <Loader2 size={14} style={{ animation: 'spin 1.5s linear infinite' }} />
                        ) : (
                          <ThumbsUp size={14} />
                        )}
                        <span>Accept & Save to Downloads</span>
                      </button>

                      <button
                        onClick={() => handleRejectVideo(item, idx)}
                        disabled={isActionBusy}
                        style={{
                          background: 'rgba(239, 68, 68, 0.12)',
                          border: '1px solid rgba(239, 68, 68, 0.4)',
                          color: '#f87171',
                          padding: '8px 14px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          cursor: isActionBusy ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        <ThumbsDown size={14} />
                        <span>Decline</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* AI Retention Hook Analysis Callout */}
                {item.retention_verdict && (
                  <div style={{ background: 'rgba(139, 92, 246, 0.08)', border: '1px solid rgba(139, 92, 246, 0.25)', borderRadius: 'var(--radius-sm)', padding: '10px 14px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={16} color="var(--accent-purple)" />
                    <span style={{ fontSize: '0.82rem', color: '#c4b5fd' }}>
                      <b>Hook Analysis ({item.hook_quality}):</b> {item.retention_verdict}
                    </span>
                  </div>
                )}

                {/* Grid: Left Video Player | Right Metadata & Titles */}
                <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', alignItems: 'start' }}>
                  
                  {/* Embedded Video Player */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div
                      style={{
                        position: 'relative',
                        borderRadius: 'var(--radius-md)',
                        overflow: 'hidden',
                        background: '#000',
                        aspectRatio: '9 / 16',
                        maxHeight: '440px',
                        border: '1px solid var(--border-subtle)',
                        boxShadow: '0 8px 25px rgba(0, 0, 0, 0.6)'
                      }}
                    >
                      <video
                        src={item.video_url}
                        controls
                        playsInline
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                      />
                    </div>

                    {isAccepted && (
                      <a
                        href={item.video_url}
                        download={item.filename}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '8px',
                          background: 'rgba(16, 185, 129, 0.15)',
                          border: '1px solid rgba(16, 185, 129, 0.4)',
                          color: '#34d399',
                          padding: '10px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.85rem',
                          fontWeight: 700,
                          textDecoration: 'none'
                        }}
                      >
                        <Download size={15} />
                        <span>Download MP4 File</span>
                      </a>
                    )}
                  </div>

                  {/* Right Column: Titles, Hook & Description */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    
                    {/* Title Options */}
                    <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--accent-pink)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Sparkles size={14} />
                        <span>🔥 3 High-CTR Titles (Click to Copy):</span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {item.titles?.map((titleStr, tIdx) => {
                          const isCopied = copiedIndex === `title_${idx}_${tIdx}`
                          return (
                            <div
                              key={tIdx}
                              onClick={() => copyToClipboard(titleStr, `title_${idx}_${tIdx}`)}
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '10px 14px',
                                background: 'rgba(255, 255, 255, 0.04)',
                                borderRadius: 'var(--radius-sm)',
                                cursor: 'pointer',
                                border: isCopied ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                                transition: 'all 0.15s ease'
                              }}
                            >
                              <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>{titleStr}</span>
                              {isCopied ? <Check size={16} color="#10b981" /> : <Copy size={16} color="var(--text-muted)" />}
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    {/* Pinned Hook */}
                    {item.hook && (
                      <div style={{ background: 'var(--bg-input)', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent-purple)' }}>
                            📌 Pinned Comment Hook (Boosts Reply Algorithm):
                          </span>
                          <button
                            onClick={() => copyToClipboard(item.hook, `hook_${idx}`)}
                            style={{ background: 'transparent', border: 'none', color: 'var(--accent-purple)', fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            {copiedIndex === `hook_${idx}` ? <Check size={12} /> : <Copy size={12} />}
                            <span>{copiedIndex === `hook_${idx}` ? 'Copied' : 'Copy Hook'}</span>
                          </button>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          "{item.hook}"
                        </div>
                      </div>
                    )}

                    {/* Description / Tags */}
                    <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                          📝 Description & SEO Hashtags:
                        </span>
                        <button
                          onClick={() => copyToClipboard(item.description, `desc_${idx}`)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--accent-cyan)',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          {copiedIndex === `desc_${idx}` ? <Check size={13} /> : <Copy size={13} />}
                          <span>{copiedIndex === `desc_${idx}` ? 'Copied Description' : 'Copy Description'}</span>
                        </button>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: '1.4', maxHeight: '110px', overflowY: 'auto' }}>
                        {item.description}
                      </div>
                    </div>

                  </div>

                </div>
              </div>
            )
          })}
        </div>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
