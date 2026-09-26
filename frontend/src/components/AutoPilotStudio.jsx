import React, { useState, useEffect, useRef } from 'react'
import {
  Rocket, Calendar, Film, MessageSquare, Image as ImageIcon,
  Sparkles, Play, Pause, Download, Copy, Check, ChevronRight,
  Layers, Volume2, Music, Type, Zap, RefreshCw, AlertCircle, Eye,
  Clock, Hash, Share2, Award, ArrowUpRight, TrendingUp, Mic,
  Radio, Send, ShieldCheck, Smartphone, Users
} from 'lucide-react'

export default function AutoPilotStudio({ systemInfo }) {
  const [activeTab, setActiveTab] = useState('batch_factory') // batch_factory | trend_harvester | podcast_maker | calendar | broll_vault | reddit_maker | thumbnail_studio | telegram_bot
  
  // Batch Factory State
  const [niches, setNiches] = useState([])
  const [selectedNiche, setSelectedNiche] = useState('dark_psychology')
  const [batchCount, setBatchCount] = useState(5)
  const [voices, setVoices] = useState([])
  const [selectedVoice, setSelectedVoice] = useState('en-US-ChristopherNeural')
  const [selectedBgm, setSelectedBgm] = useState('phonk_drive')
  const [selectedSubStyle, setSelectedSubStyle] = useState('hormozi_yellow')
  const [selectedBroll, setSelectedBroll] = useState('neural_brain')
  const [geminiApiKey, setGeminiApiKey] = useState('')
  const [customTopics, setCustomTopics] = useState('')
  
  // Execution & Progress State
  const [isRenderingBatch, setIsRenderingBatch] = useState(false)
  const [batchProgress, setBatchProgress] = useState(0)
  const [batchStage, setBatchStage] = useState('')
  const [activeBatchId, setActiveBatchId] = useState(null)
  const [batchResults, setBatchResults] = useState([])
  const [batchExtra, setBatchExtra] = useState(null)
  
  // Live Trends State
  const [liveTrends, setLiveTrends] = useState([])
  const [isLoadingTrends, setIsLoadingTrends] = useState(false)
  const [selectedTrend, setSelectedTrend] = useState(null)
  const [trendScript, setTrendScript] = useState(null)
  const [isGeneratingTrendScript, setIsGeneratingTrendScript] = useState(false)

  // 2-Person Podcast State
  const [podcastTopic, setPodcastTopic] = useState('Why 90% of millionaires invest in real estate')
  const [podcastHostVoice, setPodcastHostVoice] = useState('en-US-ChristopherNeural')
  const [podcastGuestVoice, setPodcastGuestVoice] = useState('en-US-JennyNeural')
  const [podcastDialogue, setPodcastDialogue] = useState(null)
  const [isGeneratingPodcast, setIsGeneratingPodcast] = useState(false)
  const [podcastAudioRes, setPodcastAudioRes] = useState(null)

  // Telegram Bot State
  const [telegramToken, setTelegramToken] = useState('')
  const [telegramChatId, setTelegramChatId] = useState('')
  const [telegramStatus, setTelegramStatus] = useState('idle')
  const [isSendingTgTest, setIsSendingTgTest] = useState(false)

  // Stock Vault State
  const [brollCategories, setBrollCategories] = useState([])
  const [brollSearchQuery, setBrollSearchQuery] = useState('')
  const [brollSearchResults, setBrollSearchResults] = useState([])
  const [isSearchingBroll, setIsSearchingBroll] = useState(false)
  
  // Reddit Maker State
  const [redditSub, setRedditSub] = useState('r/AskReddit')
  const [redditPrompt, setRedditPrompt] = useState('')
  const [redditStory, setRedditStory] = useState(null)
  const [isGeneratingReddit, setIsGeneratingReddit] = useState(false)
  
  // Thumbnail Studio State
  const [thumbVideoPath, setThumbVideoPath] = useState('')
  const [thumbHookText, setThumbHookText] = useState('UNBELIEVABLE TRUTH')
  const [thumbBadge, setThumbBadge] = useState('MUST WATCH')
  const [thumbStyle, setThumbStyle] = useState('viral_yellow')
  const [generatedCoverUrl, setGeneratedCoverUrl] = useState(null)
  const [isGeneratingThumb, setIsGeneratingThumb] = useState(false)

  // Copy Feedback state
  const [copiedKey, setCopiedKey] = useState(null)

  // Load Initial Data
  useEffect(() => {
    // Load Niches
    fetch('/api/autopilot/niches')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) setNiches(data)
      })
      .catch(console.error)

    // Load Voices
    fetch('/api/ai-shorts/voices')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) setVoices(data)
      })
      .catch(console.error)

    // Load B-Roll Categories
    fetch('/api/broll/categories')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) setBrollCategories(data)
      })
      .catch(console.error)

    // Load Live Trends
    fetchTrends()

    // Load Saved Telegram Config
    const savedToken = localStorage.getItem('cr_tg_token')
    const savedChat = localStorage.getItem('cr_tg_chat')
    if (savedToken) setTelegramToken(savedToken)
    if (savedChat) setTelegramChatId(savedChat)
  }, [])

  const fetchTrends = async () => {
    setIsLoadingTrends(true)
    try {
      const res = await fetch('/api/trends/live')
      const data = await res.json()
      if (Array.isArray(data)) setLiveTrends(data)
    } catch (e) {
      console.error(e)
    } finally {
      setIsLoadingTrends(false)
    }
  }

  // Poll Batch Status
  useEffect(() => {
    let interval = null
    if (activeBatchId && isRenderingBatch) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/autopilot/status/${activeBatchId}`)
          if (res.ok) {
            const data = await res.json()
            setBatchProgress(data.progress || 0)
            setBatchStage(data.current_stage || '')
            if (data.extra) setBatchExtra(data.extra)
            
            if (data.status === 'completed') {
              setBatchResults(data.results || [])
              setIsRenderingBatch(false)
              clearInterval(interval)
            } else if (data.status === 'failed') {
              setIsRenderingBatch(false)
              alert(`Batch Error: ${data.error_message || 'Rendering failed'}`)
              clearInterval(interval)
            }
          }
        } catch (e) {
          console.error(e)
        }
      }, 2000)
    }
    return () => clearInterval(interval)
  }, [activeBatchId, isRenderingBatch])

  // Start Batch Action
  const handleStartBatch = async () => {
    setIsRenderingBatch(true)
    setBatchProgress(5)
    setBatchStage('Initializing autonomous rendering pipeline...')
    setBatchResults([])

    const topicsArr = customTopics
      .split('\n')
      .map(t => t.trim())
      .filter(t => t.length > 0)

    try {
      const res = await fetch('/api/autopilot/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          niche_id: selectedNiche,
          count: batchCount,
          voice_name: selectedVoice,
          bgm_track: selectedBgm,
          subtitle_style: selectedSubStyle,
          broll_category: selectedBroll,
          custom_topics: topicsArr.length > 0 ? topicsArr : null,
          gemini_api_key: geminiApiKey || ''
        })
      })
      const data = await res.json()
      setActiveBatchId(data.batch_id)
    } catch (err) {
      setIsRenderingBatch(false)
      alert(`Failed to launch batch: ${err.message}`)
    }
  }

  // Generate Script from Live Trend
  const handleTrendToScript = async (trend) => {
    setSelectedTrend(trend)
    setIsGeneratingTrendScript(true)
    try {
      const res = await fetch('/api/trends/to-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trend_title: trend.title,
          summary: trend.summary || '',
          gemini_api_key: geminiApiKey
        })
      })
      const data = await res.json()
      setTrendScript(data)
    } catch (e) {
      alert(`Trend scripting error: ${e.message}`)
    } finally {
      setIsGeneratingTrendScript(false)
    }
  }

  // Generate 2-Person Podcast Dialogue
  const handleGeneratePodcast = async () => {
    setIsGeneratingPodcast(true)
    try {
      const res = await fetch('/api/podcast/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: podcastTopic,
          host_voice: podcastHostVoice,
          guest_voice: podcastGuestVoice,
          gemini_api_key: geminiApiKey
        })
      })
      const data = await res.json()
      setPodcastDialogue(data.dialogue)
      setPodcastAudioRes(data.audio)
    } catch (e) {
      alert(`Podcast error: ${e.message}`)
    } finally {
      setIsGeneratingPodcast(false)
    }
  }

  // Telegram Bot Control
  const handleTelegramAction = async (action) => {
    if (!telegramToken || !telegramChatId) {
      alert('Please enter your Telegram Bot Token and Chat ID!')
      return
    }
    localStorage.setItem('cr_tg_token', telegramToken)
    localStorage.setItem('cr_tg_chat', telegramChatId)

    if (action === 'test_message') setIsSendingTgTest(true)
    try {
      const res = await fetch('/api/telegram/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_token: telegramToken,
          chat_id: telegramChatId,
          action: action
        })
      })
      const data = await res.json()
      if (action === 'start') {
        setTelegramStatus('online')
        alert('✅ Telegram Remote Control Bot is now active! Send commands like /batch 3 or /trend on your phone.')
      } else if (action === 'test_message') {
        alert('📬 Test message sent to your Telegram phone!')
      }
    } catch (e) {
      alert(`Telegram error: ${e.message}`)
    } finally {
      setIsSendingTgTest(false)
    }
  }

  // Search B-Roll
  const handleSearchBroll = async () => {
    setIsSearchingBroll(true)
    try {
      const res = await fetch('/api/broll/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: brollSearchQuery, count: 6 })
      })
      const data = await res.json()
      setBrollSearchResults(data)
    } catch (err) {
      console.error(err)
    } finally {
      setIsSearchingBroll(false)
    }
  }

  // Generate Reddit Story
  const handleGenerateReddit = async () => {
    setIsGeneratingReddit(true)
    try {
      const res = await fetch('/api/reddit/generate-story', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subreddit: redditSub,
          custom_prompt: redditPrompt,
          gemini_api_key: geminiApiKey
        })
      })
      const data = await res.json()
      setRedditStory(data)
    } catch (err) {
      alert(`Reddit generation error: ${err.message}`)
    } finally {
      setIsGeneratingReddit(false)
    }
  }

  // Generate Thumbnail
  const handleGenerateThumbnail = async () => {
    if (!thumbVideoPath) {
      alert('Please specify a video path or choose from rendered videos!')
      return
    }
    setIsGeneratingThumb(true)
    try {
      const res = await fetch('/api/thumbnail/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: thumbVideoPath,
          hook_text: thumbHookText,
          badge_text: thumbBadge,
          style_key: thumbStyle
        })
      })
      const data = await res.json()
      setGeneratedCoverUrl(data.cover_url)
    } catch (err) {
      alert(`Thumbnail error: ${err.message}`)
    } finally {
      setIsGeneratingThumb(false)
    }
  }

  // Copy helper with feedback
  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const currentNicheObj = niches.find(n => n.id === selectedNiche) || niches[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Top Banner / Navigation Sub-Tabs */}
      <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{
            width: '42px', height: '42px', borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--accent), #ec4899)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff'
          }}>
            <Rocket size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              Creator Auto-Pilot Suite <span style={{ fontSize: 'var(--text-xs)', background: 'var(--accent-glow)', color: 'var(--accent)', padding: '2px 8px', borderRadius: 'var(--radius-sm)' }}>YouTube & FB Reels</span>
            </h2>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', margin: 0 }}>
              Zero-Touch Production: Auto-Trends, Auto-SFX Staging, 2-Person Podcast Shorts & Phone Control
            </p>
          </div>
        </div>

        {/* Sub-Tab Switcher */}
        <div style={{ display: 'flex', flexWrap: 'wrap', background: 'var(--bg-secondary)', padding: '4px', borderRadius: 'var(--radius-md)', gap: '4px' }}>
          {[
            { id: 'batch_factory', label: 'Batch Factory', icon: Rocket },
            { id: 'trend_harvester', label: 'Live Trends', icon: TrendingUp },
            { id: 'podcast_maker', label: '2-Person Podcast', icon: Users },
            { id: 'calendar', label: 'Calendar', icon: Calendar, badge: batchResults.length > 0 ? batchResults.length : null },
            { id: 'broll_vault', label: 'Stock Vault', icon: Film },
            { id: 'reddit_maker', label: 'Reddit Drama', icon: MessageSquare },
            { id: 'thumbnail_studio', label: '9:16 Covers', icon: ImageIcon },
            { id: 'telegram_bot', label: 'Phone Bot', icon: Smartphone }
          ].map(tab => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  padding: '7px 12px', borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-xs)', fontWeight: 600,
                  border: 'none', cursor: 'pointer',
                  background: active ? 'var(--accent)' : 'transparent',
                  color: active ? '#fff' : 'var(--text-secondary)',
                  transition: 'all var(--transition)'
                }}
              >
                <Icon size={13} />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span style={{ background: '#22c55e', color: '#000', fontSize: '10px', padding: '1px 5px', borderRadius: '10px', fontWeight: 700 }}>
                    {tab.badge}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 1. BATCH FACTORY TAB */}
      {/* ========================================================================= */}
      {activeTab === 'batch_factory' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.4fr)', gap: 'var(--space-4)' }}>
          
          {/* Left: Configuration & Settings */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            
            {/* Niche Selection Grid */}
            <div className="card" style={{ padding: 'var(--space-4)' }}>
              <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, marginBottom: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Layers size={16} color="var(--accent)" />
                Select Channel Niche
              </h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)' }}>
                {niches.map(n => {
                  const isSel = selectedNiche === n.id
                  return (
                    <div
                      key={n.id}
                      onClick={() => {
                        setSelectedNiche(n.id)
                        if (n.default_voice) setSelectedVoice(n.default_voice)
                        if (n.default_bgm) setSelectedBgm(n.default_bgm)
                        if (n.default_broll) setSelectedBroll(n.default_broll)
                      }}
                      style={{
                        padding: '10px 12px', borderRadius: 'var(--radius-md)',
                        background: isSel ? 'var(--bg-secondary)' : 'rgba(255,255,255,0.02)',
                        border: `1px solid ${isSel ? 'var(--accent)' : 'var(--border)'}`,
                        cursor: 'pointer', transition: 'all var(--transition)',
                        display: 'flex', flexDirection: 'column', gap: '4px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: isSel ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                          {n.name.split('&')[0]}
                        </span>
                        <span style={{ fontSize: '9px', background: isSel ? 'var(--accent)' : 'var(--border)', color: '#fff', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                          {n.badge}
                        </span>
                      </div>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.2 }}>
                        {n.description.slice(0, 45)}…
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Batch Size & Production Settings */}
            <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <Zap size={16} color="var(--accent)" />
                  Batch Video Quantity
                </h3>
                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--accent)' }}>
                  {batchCount} Shorts
                </span>
              </div>

              {/* Quantity buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-2)' }}>
                {[3, 5, 10, 15].map(cnt => (
                  <button
                    key={cnt}
                    onClick={() => setBatchCount(cnt)}
                    style={{
                      padding: '8px', borderRadius: 'var(--radius-sm)',
                      background: batchCount === cnt ? 'var(--accent)' : 'var(--bg-secondary)',
                      color: batchCount === cnt ? '#fff' : 'var(--text-secondary)',
                      border: `1px solid ${batchCount === cnt ? 'var(--accent)' : 'var(--border)'}`,
                      fontWeight: 600, fontSize: 'var(--text-xs)', cursor: 'pointer'
                    }}
                  >
                    {cnt} Videos
                  </button>
                ))}
              </div>

              {/* Advanced Customization Rows */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                
                {/* Voice Selection */}
                <div>
                  <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                    🎙️ Neural Voice
                  </label>
                  <select
                    value={selectedVoice}
                    onChange={e => setSelectedVoice(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
                  >
                    {voices.map(v => (
                      <option key={v.id} value={v.id}>{v.name} ({v.gender})</option>
                    ))}
                  </select>
                </div>

                {/* Subtitle Style */}
                <div>
                  <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                    ✍️ Subtitle Style
                  </label>
                  <select
                    value={selectedSubStyle}
                    onChange={e => setSelectedSubStyle(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
                  >
                    <option value="hormozi_yellow">Hormozi (Yellow & Stroke)</option>
                    <option value="beast_green">MrBeast (Vibrant Green)</option>
                    <option value="neon_cyan">Cyber Cyan (Tech Glow)</option>
                    <option value="crimson_pulse">Crimson Red (Drama)</option>
                  </select>
                </div>

                {/* BGM Track */}
                <div>
                  <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                    🎵 Background Music
                  </label>
                  <select
                    value={selectedBgm}
                    onChange={e => setSelectedBgm(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
                  >
                    <option value="phonk_drive">Phonk Drive (Viral Energy)</option>
                    <option value="deep_tension">Deep Tension (Suspense)</option>
                    <option value="lofi_chill">Lo-Fi Chill (Warm / Story)</option>
                    <option value="epic_discovery">Epic Discovery (Docu)</option>
                    <option value="upbeat_viral">Upbeat Viral (Pop/Tech)</option>
                  </select>
                </div>

                {/* B-Roll Theme */}
                <div>
                  <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                    🎞️ Stock B-Roll Vault
                  </label>
                  <select
                    value={selectedBroll}
                    onChange={e => setSelectedBroll(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
                  >
                    <option value="minecraft_parkour">Minecraft Parkour (Gameplay)</option>
                    <option value="subway_surfers">Subway Runner (Gameplay)</option>
                    <option value="satisfying_asmr">Satisfying ASMR (Soap/Kinetic)</option>
                    <option value="dark_cyberpunk">Dark Cyberpunk & Rain</option>
                    <option value="space_nebula">Space & Cosmic Vortex</option>
                    <option value="neural_brain">Neural Brain & AI Matrix</option>
                    <option value="luxury_wealth">Luxury Wealth & Money</option>
                    <option value="dark_ocean">Dark Abyssal Ocean</option>
                  </select>
                </div>
              </div>

              {/* Auto-SFX Indicator */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: 'rgba(34, 197, 94, 0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                <Volume2 size={14} color="#22c55e" />
                <span style={{ fontSize: '11px', color: '#22c55e', fontWeight: 600 }}>
                  Intelligent Auto-SFX Active: Sub-bass hook drop + transition whooshes + power word dings automatically staged.
                </span>
              </div>

              {/* Optional Custom Topics Input */}
              <div>
                <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Custom Topics (Optional — 1 topic per line, or leave empty for AI selection)
                </label>
                <textarea
                  rows={3}
                  value={customTopics}
                  onChange={e => setCustomTopics(e.target.value)}
                  placeholder="e.g. How billionaires avoid taxes&#10;Why statues in Egypt have broken noses&#10;The deepest sound in the ocean"
                  style={{
                    width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-secondary)', color: 'var(--text-primary)',
                    border: '1px solid var(--border)', fontSize: 'var(--text-xs)', resize: 'vertical'
                  }}
                />
              </div>

              {/* Launch Auto-Pilot Button */}
              <button
                disabled={isRenderingBatch}
                onClick={handleStartBatch}
                className="btn-primary"
                style={{
                  marginTop: 'var(--space-2)',
                  padding: '12px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)',
                  fontWeight: 700, fontSize: 'var(--text-sm)'
                }}
              >
                {isRenderingBatch ? (
                  <>
                    <RefreshCw size={16} className="spin" />
                    <span>Auto-Pilot Rendering Batch ({batchProgress}%)...</span>
                  </>
                ) : (
                  <>
                    <Rocket size={16} />
                    <span>⚡ Launch 1-Click Auto-Pilot ({batchCount} Shorts)</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right: Live Queue & Generated Results Feed */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            
            {/* Live Progress Card (When running) */}
            {isRenderingBatch && (
              <div className="card" style={{ padding: 'var(--space-4)', border: '1px solid var(--accent)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                  <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ⚡ Active Batch Engine
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                    {batchExtra?.current_index ? `Processing Video ${batchExtra.current_index}/${batchExtra.total}` : 'Initializing...'}
                  </span>
                </div>

                <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-3)' }}>
                  {batchStage}
                </div>

                {/* Progress bar */}
                <div style={{ width: '100%', height: '8px', background: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${batchProgress}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent), #ec4899)', transition: 'width 0.4s ease' }} />
                </div>
              </div>
            )}

            {/* Results Grid / Feed */}
            <div className="card" style={{ padding: 'var(--space-4)', flex: 1, minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
                <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <Sparkles size={16} color="var(--accent)" />
                  Rendered Shorts & Metadata Queue
                </h3>
                {batchResults.length > 0 && (
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--green)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Check size={14} /> Ready in ~/Downloads
                  </span>
                )}
              </div>

              {batchResults.length === 0 && !isRenderingBatch ? (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', gap: 'var(--space-2)' }}>
                  <Rocket size={36} strokeWidth={1.5} color="var(--border)" />
                  <p style={{ fontSize: 'var(--text-sm)', margin: 0 }}>
                    No batch currently generated.
                  </p>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', margin: 0 }}>
                    Select your niche on the left and click <strong>Launch 1-Click Auto-Pilot</strong> to produce ready-to-post Shorts automatically.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', maxHeight: '600px', overflowY: 'auto' }}>
                  {batchResults.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: 'var(--space-3)', borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                        display: 'grid', gridTemplateColumns: '110px 1fr', gap: 'var(--space-3)'
                      }}
                    >
                      {/* Video / Cover Preview */}
                      <div style={{ width: '110px', height: '180px', borderRadius: 'var(--radius-sm)', overflow: 'hidden', background: '#000', position: 'relative' }}>
                        <video
                          src={item.video_url}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          controls
                          preload="metadata"
                        />
                      </div>

                      {/* Content & Metadata Details */}
                      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          {/* Schedule badge */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: '4px' }}>
                            <span style={{ fontSize: '10px', background: 'var(--accent-glow)', color: 'var(--accent)', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                              {item.schedule_day} • {item.schedule_time}
                            </span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                              {Math.round(item.duration)}s duration
                            </span>
                          </div>

                          <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: '0 0 6px 0', color: 'var(--text-primary)', lineHeight: 1.3 }}>
                            {item.title}
                          </h4>

                          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: '0 0 8px 0', lineHeight: 1.3 }}>
                            {item.metadata?.yt_description?.slice(0, 100)}…
                          </p>
                        </div>

                        {/* Quick 1-Click Copy & Download actions */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          <button
                            onClick={() => copyToClipboard(
                              `${item.metadata?.yt_titles?.[0] || item.title}\n\n${item.metadata?.yt_description}\n\n${item.metadata?.yt_tags?.join(' ')}`,
                              `yt_${idx}`
                            )}
                            style={{
                              padding: '5px 10px', borderRadius: '4px', border: '1px solid var(--border)',
                              background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: '11px',
                              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600
                            }}
                          >
                            {copiedKey === `yt_${idx}` ? <Check size={12} color="var(--green)" /> : <Copy size={12} />}
                            <span>Copy YouTube SEO</span>
                          </button>

                          <button
                            onClick={() => copyToClipboard(
                              `${item.metadata?.fb_caption}\n\n${item.metadata?.fb_tags?.join(' ')}`,
                              `fb_${idx}`
                            )}
                            style={{
                              padding: '5px 10px', borderRadius: '4px', border: '1px solid var(--border)',
                              background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: '11px',
                              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600
                            }}
                          >
                            {copiedKey === `fb_${idx}` ? <Check size={12} color="var(--green)" /> : <Share2 size={12} />}
                            <span>Copy FB Caption</span>
                          </button>

                          <a
                            href={item.video_url}
                            download={item.video_filename}
                            style={{
                              padding: '5px 10px', borderRadius: '4px', border: 'none',
                              background: 'var(--accent)', color: '#fff', fontSize: '11px',
                              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600,
                              textDecoration: 'none'
                            }}
                          >
                            <Download size={12} />
                            <span>Download MP4</span>
                          </a>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. LIVE TRENDS & BREAKING NEWS HARVESTER */}
      {/* ========================================================================= */}
      {activeTab === 'trend_harvester' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.3fr)', gap: 'var(--space-4)' }}>
          
          {/* Left: Live Google Trends Feed */}
          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <TrendingUp size={16} color="var(--accent)" />
                  Real-time Google Trends & Viral News
                </h3>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Updated live from global RSS search feeds</span>
              </div>
              <button
                onClick={fetchTrends}
                disabled={isLoadingTrends}
                style={{ padding: '6px 10px', fontSize: '11px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: '#fff', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <RefreshCw size={12} className={isLoadingTrends ? 'spin' : ''} />
                <span>Refresh</span>
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', maxHeight: '500px', overflowY: 'auto' }}>
              {liveTrends.map((t, idx) => (
                <div
                  key={idx}
                  onClick={() => handleTrendToScript(t)}
                  style={{
                    padding: '10px', borderRadius: 'var(--radius-sm)',
                    background: selectedTrend?.title === t.title ? 'var(--bg-secondary)' : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${selectedTrend?.title === t.title ? 'var(--accent)' : 'var(--border)'}`,
                    cursor: 'pointer', transition: 'all var(--transition)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                    <span style={{ fontSize: '10px', background: 'var(--accent-glow)', color: 'var(--accent)', padding: '1px 6px', borderRadius: '3px', fontWeight: 700 }}>
                      🔥 {t.traffic}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t.source}</span>
                  </div>
                  <h4 style={{ fontSize: 'var(--text-xs)', fontWeight: 700, margin: '4px 0 2px 0', color: 'var(--text-primary)' }}>
                    {t.title}
                  </h4>
                  <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.3 }}>
                    {t.summary}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Auto-Generated Trend Script & 1-Click Render */}
          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0 }}>
              Live Viral Script & Infinite Loop Stager
            </h3>

            {isGeneratingTrendScript ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '8px' }}>
                <RefreshCw size={18} className="spin" color="var(--accent)" />
                <span>Crafting high-retention news script with infinite loop ending...</span>
              </div>
            ) : trendScript ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '10px', background: '#ef4444', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontWeight: 800 }}>
                    {trendScript.hook_badge || 'BREAKING'}
                  </span>
                  <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                    {trendScript.title}
                  </h4>
                </div>

                <div style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--accent)', display: 'block', marginBottom: '4px' }}>
                    🎙️ Narration Script (Infinite Loop Ending):
                  </span>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-primary)', lineHeight: 1.5, margin: 0 }}>
                    "{trendScript.script}"
                  </p>
                </div>

                <button
                  onClick={() => {
                    setCustomTopics(selectedTrend?.title || '')
                    setActiveTab('batch_factory')
                  }}
                  className="btn-primary"
                  style={{ padding: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: 'var(--text-xs)', fontWeight: 700 }}
                >
                  <Rocket size={14} />
                  <span>Send to 1-Click Auto-Pilot Factory & Render</span>
                </button>
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>
                Select any breaking trend on the left to auto-generate a viral script.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. 2-PERSON PODCAST & DIALOGUE SHORTS */}
      {/* ========================================================================= */}
      {activeTab === 'podcast_maker' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.4fr)', gap: 'var(--space-4)' }}>
          
          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Users size={16} color="var(--accent)" />
              2-Person Conversational Podcast Shorts
            </h3>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Conversation Topic / Provocative Question
              </label>
              <textarea
                rows={3}
                value={podcastTopic}
                onChange={e => setPodcastTopic(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  🎙️ Host / Interviewer Voice
                </label>
                <select
                  value={podcastHostVoice}
                  onChange={e => setPodcastHostVoice(e.target.value)}
                  style={{ width: '100%', padding: '7px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: '#fff', border: '1px solid var(--border)', fontSize: '11px' }}
                >
                  {voices.map(v => <option key={v.id} value={v.id}>{v.name} ({v.gender})</option>)}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  💡 Guest / Expert Voice
                </label>
                <select
                  value={podcastGuestVoice}
                  onChange={e => setPodcastGuestVoice(e.target.value)}
                  style={{ width: '100%', padding: '7px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: '#fff', border: '1px solid var(--border)', fontSize: '11px' }}
                >
                  {voices.map(v => <option key={v.id} value={v.id}>{v.name} ({v.gender})</option>)}
                </select>
              </div>
            </div>

            <button
              onClick={handleGeneratePodcast}
              disabled={isGeneratingPodcast}
              className="btn-primary"
              style={{ padding: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: 'var(--text-xs)', fontWeight: 700 }}
            >
              {isGeneratingPodcast ? <RefreshCw size={14} className="spin" /> : <Mic size={14} />}
              <span>{isGeneratingPodcast ? 'Synthesizing Dual-Voice Podcast...' : 'Generate 2-Speaker Dialogue & Audio'}</span>
            </button>
          </div>

          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0 }}>
              Alternating Speaker Dialogue & Audio Preview
            </h3>

            {podcastDialogue ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {podcastAudioRes?.master_audio_url && (
                  <div style={{ padding: 'var(--space-2)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <audio src={podcastAudioRes.master_audio_url} controls style={{ width: '100%' }} />
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
                  {podcastDialogue.turns?.map((turn, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 12px', borderRadius: 'var(--radius-sm)',
                        background: turn.speaker === 'host' ? 'rgba(91, 108, 249, 0.08)' : 'rgba(236, 72, 153, 0.08)',
                        borderLeft: `3px solid ${turn.speaker === 'host' ? 'var(--accent)' : '#ec4899'}`
                      }}
                    >
                      <span style={{ fontSize: '10px', fontWeight: 800, color: turn.speaker === 'host' ? 'var(--accent)' : '#ec4899', textTransform: 'uppercase' }}>
                        {turn.speaker === 'host' ? `🎙️ ${podcastDialogue.host_name || 'Host'}` : `💡 ${podcastDialogue.guest_name || 'Guest'}`}
                      </span>
                      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-primary)', margin: '2px 0 0 0', lineHeight: 1.4 }}>
                        {turn.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>
                Click "Generate 2-Speaker Dialogue" to create a dynamic podcast Short.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. TELEGRAM REMOTE CONTROL BOT */}
      {/* ========================================================================= */}
      {activeTab === 'telegram_bot' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.2fr)', gap: 'var(--space-4)' }}>
          
          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Smartphone size={18} color="var(--accent)" />
              <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0 }}>
                Telegram Remote Control Setup
              </h3>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
              Control your channel factory directly from your phone. Create a bot in 30 seconds via Telegram's <strong>@BotFather</strong>.
            </p>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Telegram Bot Token
              </label>
              <input
                type="password"
                value={telegramToken}
                onChange={e => setTelegramToken(e.target.value)}
                placeholder="e.g. 7123456789:AAH..."
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Your Telegram Chat ID (or User ID)
              </label>
              <input
                type="text"
                value={telegramChatId}
                onChange={e => setTelegramChatId(e.target.value)}
                placeholder="e.g. 123456789"
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)', marginTop: '4px' }}>
              <button
                onClick={() => handleTelegramAction('start')}
                className="btn-primary"
                style={{ padding: '10px', fontSize: 'var(--text-xs)', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                <Zap size={14} />
                <span>Start Phone Bot</span>
              </button>

              <button
                onClick={() => handleTelegramAction('test_message')}
                disabled={isSendingTgTest}
                style={{ padding: '10px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: '#fff', borderRadius: 'var(--radius-sm)', fontSize: 'var(--text-xs)', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                <Send size={14} />
                <span>{isSendingTgTest ? 'Sending...' : 'Send Test Msg'}</span>
              </button>
            </div>
          </div>

          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0 }}>
              Phone Commands Cheat Sheet
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {[
                { cmd: '/batch 5 dark_psychology', desc: 'Renders 5 Shorts and sends MP4 files + copyable titles to your phone.' },
                { cmd: '/trend', desc: 'Fetches today\'s #1 Google trend, generates script, and sends ready Short.' },
                { cmd: '/reddit', desc: 'Creates a viral Reddit drama story with Subway Surfers gameplay.' },
                { cmd: '/status', desc: 'Checks server CPU, GPU NVENC status, and disk space.' }
              ].map((c, i) => (
                <div key={i} style={{ padding: '10px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  <code style={{ color: 'var(--accent)', fontWeight: 700, fontSize: '12px' }}>{c.cmd}</code>
                  <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: 'var(--text-secondary)' }}>{c.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. CONTENT CALENDAR TAB */}
      {/* ========================================================================= */}
      {activeTab === 'calendar' && (
        <div className="card" style={{ padding: 'var(--space-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
            <div>
              <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Calendar size={18} color="var(--accent)" />
                Channel Posting Schedule (YouTube Shorts & Facebook Reels)
              </h3>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', margin: 0 }}>
                High-engagement posting slots calibrated for peak algorithm traffic (12:00 PM & 6:30 PM)
              </p>
            </div>
          </div>

          {batchResults.length === 0 ? (
            <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--text-muted)' }}>
              <Calendar size={40} strokeWidth={1.5} color="var(--border)" style={{ marginBottom: 'var(--space-2)' }} />
              <p style={{ fontSize: 'var(--text-sm)' }}>Generate a batch in <strong>1-Click Batch Factory</strong> to populate your schedule.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--space-3)' }}>
              {batchResults.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: 'var(--space-3)', borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                    display: 'flex', flexDirection: 'column', gap: 'var(--space-2)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', background: 'var(--accent-glow)', padding: '2px 8px', borderRadius: '4px' }}>
                      {item.schedule_day}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> {item.schedule_time}
                    </span>
                  </div>

                  <h4 style={{ fontSize: 'var(--text-xs)', fontWeight: 700, margin: 0, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                    {item.title}
                  </h4>

                  <div style={{ width: '100%', height: '140px', borderRadius: 'var(--radius-sm)', overflow: 'hidden', background: '#000' }}>
                    <video src={item.video_url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} controls preload="metadata" />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '4px' }}>
                    <button
                      onClick={() => copyToClipboard(item.metadata?.yt_titles?.[0] + '\n' + item.metadata?.yt_description, `cal_yt_${idx}`)}
                      style={{ padding: '6px', fontSize: '10px', background: 'var(--bg-card)', border: '1px solid var(--border)', color: '#fff', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
                    >
                      {copiedKey === `cal_yt_${idx}` ? 'Copied!' : 'Copy YouTube'}
                    </button>
                    <button
                      onClick={() => copyToClipboard(item.metadata?.fb_caption, `cal_fb_${idx}`)}
                      style={{ padding: '6px', fontSize: '10px', background: 'var(--bg-card)', border: '1px solid var(--border)', color: '#fff', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
                    >
                      {copiedKey === `cal_fb_${idx}` ? 'Copied!' : 'Copy FB Reel'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 6. STOCK B-ROLL & GAMEPLAY VAULT */}
      {/* ========================================================================= */}
      {activeTab === 'broll_vault' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div>
              <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Film size={18} color="var(--accent)" />
                Stock B-Roll & Gameplay Retention Loops (9:16 HD)
              </h3>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', margin: 0 }}>
                High-retention vertical footage ready to inject into any Short
              </p>
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-2)', minWidth: '320px' }}>
              <input
                type="text"
                value={brollSearchQuery}
                onChange={e => setBrollSearchQuery(e.target.value)}
                placeholder="Search stock video (e.g. rain, galaxy, gym)..."
                onKeyDown={e => e.key === 'Enter' && handleSearchBroll()}
                style={{ flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              />
              <button
                onClick={handleSearchBroll}
                disabled={isSearchingBroll}
                style={{ padding: '8px 14px', borderRadius: 'var(--radius-sm)', background: 'var(--accent)', color: '#fff', border: 'none', fontWeight: 600, fontSize: 'var(--text-xs)', cursor: 'pointer' }}
              >
                {isSearchingBroll ? 'Searching…' : 'Search'}
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 'var(--space-3)' }}>
            {brollCategories.map(cat => (
              <div
                key={cat.id}
                className="card"
                style={{ padding: 'var(--space-3)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {cat.name}
                  </span>
                  <span style={{ fontSize: '9px', background: cat.color + '22', color: cat.color, padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                    {cat.niche}
                  </span>
                </div>

                <div style={{ width: '100%', height: '240px', borderRadius: 'var(--radius-sm)', overflow: 'hidden', background: '#000' }}>
                  {cat.video_url ? (
                    <video
                      src={cat.video_url}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      controls
                      loop
                      muted
                      preload="metadata"
                    />
                  ) : (
                    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '11px' }}>
                      Loop generating...
                    </div>
                  )}
                </div>

                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {cat.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 7. REDDIT STORY GENERATOR */}
      {/* ========================================================================= */}
      {activeTab === 'reddit_maker' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.4fr)', gap: 'var(--space-4)' }}>
          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <MessageSquare size={16} color="var(--accent)" />
              Reddit Story Creator
            </h3>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Subreddit Channel
              </label>
              <select
                value={redditSub}
                onChange={e => setRedditSub(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              >
                <option value="r/AskReddit">r/AskReddit (Unbelievable Answers)</option>
                <option value="r/AmItheAsshole">r/AmItheAsshole (Drama & Revenge)</option>
                <option value="r/confession">r/confession (Secret Confessions)</option>
                <option value="r/Showerthoughts">r/Showerthoughts (Mind Blown)</option>
                <option value="r/nosleep">r/nosleep (Scary Encounters)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Story Prompt / Angle (Optional)
              </label>
              <textarea
                rows={4}
                value={redditPrompt}
                onChange={e => setRedditPrompt(e.target.value)}
                placeholder="e.g. My landlord tried to keep my $3,000 deposit, so I took his whole company down..."
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              />
            </div>

            <button
              onClick={handleGenerateReddit}
              disabled={isGeneratingReddit}
              className="btn-primary"
              style={{ padding: '10px', fontSize: 'var(--text-xs)', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              {isGeneratingReddit ? <RefreshCw size={14} className="spin" /> : <Sparkles size={14} />}
              <span>{isGeneratingReddit ? 'Writing Story & Rendering Card...' : 'Generate Reddit Story & Card'}</span>
            </button>
          </div>

          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0 }}>
              Live Reddit UI Card & Narration Script
            </h3>

            {redditStory ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {redditStory.card_url && (
                  <div style={{ width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border)' }}>
                    <img src={redditStory.card_url} alt="Reddit Post Card" style={{ width: '100%', height: 'auto', display: 'block' }} />
                  </div>
                )}

                <div style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                    🎙️ Narration Script ({redditStory.author})
                  </span>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-primary)', lineHeight: 1.5, margin: 0 }}>
                    "{redditStory.script}"
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>
                Click "Generate Reddit Story & Card" to create an authentic story.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 8. 9:16 COVER & THUMBNAIL STUDIO */}
      {/* ========================================================================= */}
      {activeTab === 'thumbnail_studio' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(320px, 1fr)', gap: 'var(--space-4)' }}>
          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <ImageIcon size={16} color="var(--accent)" />
              High-CTR 9:16 Thumbnail Designer
            </h3>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Viral Hook Text
              </label>
              <input
                type="text"
                value={thumbHookText}
                onChange={e => setThumbHookText(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Pill Badge Text (Top Banner)
              </label>
              <input
                type="text"
                value={thumbBadge}
                onChange={e => setThumbBadge(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                Color & 3D Typography Preset
              </label>
              <select
                value={thumbStyle}
                onChange={e => setThumbStyle(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)', fontSize: 'var(--text-xs)' }}
              >
                <option value="viral_yellow">Viral Yellow (#FFE600 & 3D Drop Shadow)</option>
                <option value="mrbeast_impact">MrBeast Impact (Bold White & Blue Badge)</option>
                <option value="neon_cyber">Neon Cyan & Purple Cyber Glow</option>
                <option value="dark_mystery">Dark Mystery & Crimson Red</option>
              </select>
            </div>

            <button
              onClick={handleGenerateThumbnail}
              disabled={isGeneratingThumb}
              className="btn-primary"
              style={{ padding: '10px', fontSize: 'var(--text-xs)', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              {isGeneratingThumb ? <RefreshCw size={14} className="spin" /> : <Sparkles size={14} />}
              <span>{isGeneratingThumb ? 'Generating 3D Cover...' : 'Generate 9:16 Viral Cover'}</span>
            </button>
          </div>

          <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '420px' }}>
            {generatedCoverUrl ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
                <div style={{ width: '220px', height: '390px', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '2px solid var(--accent)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
                  <img src={generatedCoverUrl} alt="Generated Cover" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
                <a
                  href={generatedCoverUrl}
                  download="Short_Cover_916.jpg"
                  style={{
                    padding: '8px 16px', background: 'var(--accent)', color: '#fff',
                    borderRadius: 'var(--radius-sm)', textDecoration: 'none', fontSize: 'var(--text-xs)',
                    fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px'
                  }}
                >
                  <Download size={14} /> Download High-Res Cover
                </a>
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)', textAlign: 'center' }}>
                <ImageIcon size={36} strokeWidth={1.5} color="var(--border)" style={{ marginBottom: '8px' }} />
                <p>Generated 9:16 Cover preview will appear here.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
