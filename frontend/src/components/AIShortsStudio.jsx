import React, { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  Mic,
  Play,
  Pause,
  Film,
  Type,
  Music,
  Sliders,
  Upload,
  Download,
  CheckCircle2,
  RefreshCw,
  Layers,
  Wand2,
  Volume2,
  Video,
  ArrowRight,
  ShieldCheck,
  Zap,
  Clock,
  Eye,
  Trash2,
  Palette,
  SlidersHorizontal,
  FileAudio,
  Check
} from 'lucide-react'

// Iconic Creator Subtitle Presets
const CREATOR_SUBTITLE_PRESETS = [
  {
    id: 'hormozi_yellow',
    creator: 'Alex Hormozi',
    name: 'Hormozi Viral Signature',
    font: 'Montserrat',
    activeColor: '#FFE600',
    inactiveColor: '#FFFFFF',
    outlineColor: '#000000',
    outlineWidth: 5,
    backgroundBox: true,
    wordsPerLine: 2,
    textCase: 'uppercase',
    animation: 'pop',
    fontSize: 54,
    badge: 'POPULAR',
    desc: 'Bold canary yellow pop, heavy black stroke, 2-word flash'
  },
  {
    id: 'beast_green',
    creator: 'MrBeast',
    name: 'MrBeast Punchy Green',
    font: 'Montserrat',
    activeColor: '#22C55E',
    inactiveColor: '#FFFFFF',
    outlineColor: '#000000',
    outlineWidth: 6,
    backgroundBox: true,
    wordsPerLine: 3,
    textCase: 'uppercase',
    animation: 'pop',
    fontSize: 52,
    badge: 'HIGH IMPACT',
    desc: 'Electric neon green active, heavy outline with dark backing'
  },
  {
    id: 'ali_abdaal',
    creator: 'Ali Abdaal',
    name: 'Ali Abdaal Minimalist',
    font: 'Montserrat',
    activeColor: '#FBBF24',
    inactiveColor: '#F1F5F9',
    outlineColor: '#000000',
    outlineWidth: 2,
    backgroundBox: true,
    wordsPerLine: 3,
    textCase: 'capitalize',
    animation: 'pop',
    fontSize: 48,
    badge: 'AESTHETIC',
    desc: 'Warm amber gold, soft charcoal pill box, clean Title Case'
  },
  {
    id: 'iman_gadzhi',
    creator: 'Iman Gadzhi',
    name: 'Iman Gadzhi Editorial',
    font: 'Bebas Neue',
    activeColor: '#EF4444',
    inactiveColor: '#FFFFFF',
    outlineColor: '#000000',
    outlineWidth: 4,
    backgroundBox: false,
    wordsPerLine: 2,
    textCase: 'uppercase',
    animation: 'pop',
    fontSize: 60,
    badge: 'LUXURY',
    desc: 'Crimson red highlight, editorial tall font, high contrast'
  },
  {
    id: 'cyber_neon',
    creator: 'Cyber / Tech',
    name: 'Cyberpunk Neon Matrix',
    font: 'Montserrat',
    activeColor: '#00F0FF',
    inactiveColor: '#F472B6',
    outlineColor: '#000000',
    outlineWidth: 4,
    backgroundBox: true,
    wordsPerLine: 2,
    textCase: 'uppercase',
    animation: 'pop',
    fontSize: 54,
    badge: 'FUTURISTIC',
    desc: 'Electric cyan active, glowing magenta inactive'
  },
  {
    id: 'custom',
    creator: 'Custom Studio',
    name: 'Custom Creator Designer',
    font: 'Montserrat',
    activeColor: '#FFE600',
    inactiveColor: '#FFFFFF',
    outlineColor: '#000000',
    outlineWidth: 5,
    backgroundBox: true,
    wordsPerLine: 2,
    textCase: 'uppercase',
    animation: 'pop',
    fontSize: 54,
    badge: 'STUDIO',
    desc: 'Full control over fonts, colors, boxes, strokes & timing'
  }
]

// Quick Topic Starters
const TOPIC_SUGGESTIONS = [
  '3 Insane Mysteries About The Deep Ocean',
  'Why Coffee Keeps You Awake (The Chemical Truth)',
  'How To Build $10k/Month With AI Tools In 2026',
  'The Real Reason People Fail In Their 20s',
  'What Happens When A Black Hole Collides With Earth'
]

export default function AIShortsStudio({ systemInfo, onOpenKeyModal }) {
  // Master Step: 1 (Script & Voice) | 2 (Storyboard) | 3 (Style & BGM) | 4 (Render)
  const [currentStep, setCurrentStep] = useState(1)

  // Step 1: Script & Voice State
  const [topic, setTopic] = useState('')
  const [tone, setTone] = useState('dramatic')
  const [targetDuration, setTargetDuration] = useState(30)
  const [isGeneratingScript, setIsGeneratingScript] = useState(false)
  const [script, setScript] = useState(
    "Most people have no idea about the deepest secret in our universe. In fact, over eighty percent of everything out there is completely invisible to our eyes. Scientists call this dark matter, and without it, our entire galaxy would instantly fly apart. Subscribe now for the mind-blowing truth."
  )
  const [voices, setVoices] = useState([])
  const [selectedVoice, setSelectedVoice] = useState('en-US-ChristopherNeural')
  const [voiceSpeed, setVoiceSpeed] = useState(1.05)
  const [voicePitch, setVoicePitch] = useState(0)
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false)
  const [customVoiceFile, setCustomVoiceFile] = useState(null)
  const [voiceAudioUrl, setVoiceAudioUrl] = useState(null)
  const [voiceAudioPath, setVoiceAudioPath] = useState(null)
  const [wordTimings, setWordTimings] = useState([])
  const [audioDuration, setAudioDuration] = useState(0)

  // Step 2: Storyboard & Scenes State
  const [scenes, setScenes] = useState([])
  const [isParsingScenes, setIsParsingScenes] = useState(false)

  // Step 3: Professional Creator Subtitle Studio
  const [selectedPresetId, setSelectedPresetId] = useState('hormozi_yellow')
  const [subtitleFont, setSubtitleFont] = useState('Montserrat')
  const [subtitleFontSize, setSubtitleFontSize] = useState(54)
  const [subtitleActiveColor, setSubtitleActiveColor] = useState('#FFE600')
  const [subtitleInactiveColor, setSubtitleInactiveColor] = useState('#FFFFFF')
  const [subtitleOutlineColor, setSubtitleOutlineColor] = useState('#000000')
  const [subtitleOutlineWidth, setSubtitleOutlineWidth] = useState(5)
  const [subtitleBackgroundBox, setSubtitleBackgroundBox] = useState(true)
  const [subtitleWordsPerLine, setSubtitleWordsPerLine] = useState(2)
  const [subtitleTextCase, setSubtitleTextCase] = useState('uppercase')
  const [subtitleAnimation, setSubtitleAnimation] = useState('pop')
  const [subtitlePositionY, setSubtitlePositionY] = useState(420)

  // BGM & Extras State
  const [bgmTrack, setBgmTrack] = useState('phonk_drive')
  const [bgmVolume, setBgmVolume] = useState(0.18)
  const [duckingIntensity, setDuckingIntensity] = useState(0.80)
  const [progressBar, setProgressBar] = useState(true)
  const [progressBarColor, setProgressBarColor] = useState('#06b6d4')
  const [antiCopyrightShield, setAntiCopyrightShield] = useState(true)

  // Audio Previews
  const [playingBgm, setPlayingBgm] = useState(null)
  const [isPlayingVoice, setIsPlayingVoice] = useState(false)
  const voiceAudioRef = useRef(null)
  const bgmAudioRef = useRef(null)

  // Step 4: Render & Export State
  const [isRendering, setIsRendering] = useState(false)
  const [renderProgress, setRenderProgress] = useState(0)
  const [renderStage, setRenderStage] = useState('')
  const [renderedVideoUrl, setRenderedVideoUrl] = useState(null)
  const [renderJobId, setRenderJobId] = useState(null)

  // Live Canvas Preview Playhead
  const [previewPlaying, setPreviewPlaying] = useState(false)
  const [previewTime, setPreviewTime] = useState(0)
  const previewTimerRef = useRef(null)

  // Load Voices on mount
  useEffect(() => {
    fetch('/api/ai-shorts/voices')
      .then((res) => res.json())
      .then((data) => {
        setVoices(data)
        if (data && data.length > 0) {
          setSelectedVoice(data[0].id)
        }
      })
      .catch((err) => console.error('Failed to load voices:', err))
  }, [])

  // Apply Subtitle Preset
  const handleSelectSubtitlePreset = (preset) => {
    setSelectedPresetId(preset.id)
    if (preset.id !== 'custom') {
      setSubtitleFont(preset.font)
      setSubtitleActiveColor(preset.activeColor)
      setSubtitleInactiveColor(preset.inactiveColor)
      setSubtitleOutlineColor(preset.outlineColor)
      setSubtitleOutlineWidth(preset.outlineWidth)
      setSubtitleBackgroundBox(preset.backgroundBox)
      setSubtitleWordsPerLine(preset.wordsPerLine)
      setSubtitleTextCase(preset.textCase)
      setSubtitleAnimation(preset.animation)
      setSubtitleFontSize(preset.fontSize)
    }
  }

  // Auto-generate Script using AI (Gemini)
  const handleGenerateScriptAI = async (customTopic) => {
    const t = customTopic || topic
    if (!t.trim()) {
      alert('Please enter a topic or concept prompt!')
      return
    }
    const savedKeys = localStorage.getItem('cr_gemini_api_keys') || localStorage.getItem('cr_gemini_api_key') || ''
    setIsGeneratingScript(true)
    try {
      const res = await fetch('/api/ai-shorts/generate-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: t.trim(),
          tone,
          target_duration: targetDuration,
          gemini_api_key: savedKeys
        })
      })
      if (!res.ok) throw new Error('Failed to generate script')
      const data = await res.json()
      if (data.script) {
        setScript(data.script)
      }
    } catch (err) {
      alert('Error generating script: ' + err.message)
    } finally {
      setIsGeneratingScript(false)
    }
  }

  // Generate TTS Voice & Break Down Script into Scenes
  const handleGenerateVoiceAndScenes = async () => {
    if (!script.trim()) {
      alert('Please provide a narration script!')
      return
    }

    const savedKeys = localStorage.getItem('cr_gemini_api_keys') || localStorage.getItem('cr_gemini_api_key') || ''
    setIsGeneratingTTS(true)
    setIsParsingScenes(true)

    try {
      // 1. Generate Voice & Word Timings
      const ttsRes = await fetch('/api/ai-shorts/generate-tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: script.trim(),
          voice_name: selectedVoice,
          speed_factor: voiceSpeed,
          pitch_cents: voicePitch
        })
      })

      if (!ttsRes.ok) throw new Error('TTS Voice Generation Failed')
      const ttsData = await ttsRes.json()

      setVoiceAudioUrl(ttsData.audio_url)
      setVoiceAudioPath(ttsData.audio_file)
      setWordTimings(ttsData.word_timings || [])
      setAudioDuration(ttsData.duration || 30)

      // 2. Parse Scenes
      const parseRes = await fetch('/api/ai-shorts/parse-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_text: script.trim(),
          gemini_api_key: savedKeys
        })
      })

      if (!parseRes.ok) throw new Error('Scene Breakdown Failed')
      const parseData = await parseRes.json()

      // Distribute total audio duration across scenes
      const rawScenes = parseData.scenes || []
      const totalWords = rawScenes.reduce((acc, s) => acc + (s.narration_text.split(' ').length || 1), 0)
      const adjustedScenes = rawScenes.map((sc) => {
        const wordsInSc = sc.narration_text.split(' ').length || 1
        const dur = (wordsInSc / (totalWords || 1)) * (ttsData.duration || 30)
        return {
          ...sc,
          duration_seconds: Math.max(1.8, Math.round(dur * 10) / 10)
        }
      })

      setScenes(adjustedScenes)
      setCurrentStep(2) // Move to Storyboard
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setIsGeneratingTTS(false)
      setIsParsingScenes(false)
    }
  }

  // Handle Custom Voice Upload
  const handleCustomVoiceUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/ai-shorts/upload-voice', {
        method: 'POST',
        body: formData
      })
      if (!res.ok) throw new Error('Failed to upload custom voice')
      const data = await res.json()
      setCustomVoiceFile(file)
      setVoiceAudioUrl(data.audio_url)
      setVoiceAudioPath(data.file_path)
      setAudioDuration(data.duration || 30)
    } catch (err) {
      alert('Error uploading voice: ' + err.message)
    }
  }

  // Handle Video Clip Upload for a specific Scene
  const handleSceneVideoUpload = async (sceneIdx, file) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })
      if (!res.ok) throw new Error('Upload failed')
      const data = await res.json()

      const updated = [...scenes]
      updated[sceneIdx] = {
        ...updated[sceneIdx],
        video_source_path: `/home/harshit/Desktop/cr-remover/backend/storage/uploads/${data.job_id}_${data.filename}`,
        video_preview_url: data.video_url
      }
      setScenes(updated)
    } catch (err) {
      alert('Error uploading scene clip: ' + err.message)
    }
  }

  // Toggle BGM Preview Playback
  const toggleBgmPlay = (trackId) => {
    if (playingBgm === trackId) {
      bgmAudioRef.current?.pause()
      setPlayingBgm(null)
    } else {
      if (trackId === 'none') {
        bgmAudioRef.current?.pause()
        setPlayingBgm(null)
        setBgmTrack('none')
        return
      }
      setBgmTrack(trackId)
      setPlayingBgm(trackId)
      if (bgmAudioRef.current) {
        bgmAudioRef.current.src = `/api/media/assets/${trackId}.wav`
        bgmAudioRef.current.play().catch((e) => console.log(e))
      }
    }
  }

  // Toggle Voice Audio Playback
  const toggleVoicePlay = () => {
    if (isPlayingVoice) {
      voiceAudioRef.current?.pause()
      setIsPlayingVoice(false)
    } else {
      if (voiceAudioUrl && voiceAudioRef.current) {
        voiceAudioRef.current.src = voiceAudioUrl
        voiceAudioRef.current.play().then(() => setIsPlayingVoice(true)).catch((e) => console.log(e))
      }
    }
  }

  // Start 9:16 Master Render
  const handleStartRender = async () => {
    if (!voiceAudioPath || scenes.length === 0) {
      alert('Please generate voice and storyboard scenes first!')
      return
    }

    const jobId = `short_${Date.now().toString().slice(-6)}`
    setRenderJobId(jobId)
    setIsRendering(true)
    setRenderProgress(5)
    setRenderStage('Compiling Master 9:16 Short & Creator Subtitles...')
    setRenderedVideoUrl(null)

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/progress/${jobId}`
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.progress !== undefined) setRenderProgress(data.progress)
        if (data.current_stage) setRenderStage(data.current_stage)

        if (data.status === 'completed' || data.progress === 100) {
          setIsRendering(false)
          setRenderedVideoUrl(`/api/media/processed/ai_short_${jobId}.mp4`)
          ws.close()
        } else if (data.status === 'failed') {
          setIsRendering(false)
          alert('Rendering failed: ' + (data.current_stage || 'Unknown error'))
          ws.close()
        }
      } catch (e) {
        console.error(e)
      }
    }

    try {
      const payload = {
        project_id: jobId,
        title: topic.trim() ? topic.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 30) : 'Viral_AI_Short',
        scenes: scenes,
        voice_audio_path: voiceAudioPath,
        word_timings: wordTimings,
        subtitle_style: selectedPresetId,
        subtitle_font_family: subtitleFont,
        subtitle_font_size: subtitleFontSize,
        subtitle_text_case: subtitleTextCase,
        subtitle_active_color: subtitleActiveColor,
        subtitle_inactive_color: subtitleInactiveColor,
        subtitle_outline_color: subtitleOutlineColor,
        subtitle_outline_width: subtitleOutlineWidth,
        subtitle_background_box: subtitleBackgroundBox,
        subtitle_words_per_line: subtitleWordsPerLine,
        subtitle_position_y: subtitlePositionY,
        subtitle_animation: subtitleAnimation,
        progress_bar: progressBar,
        progress_bar_color: progressBarColor,
        bgm_track: bgmTrack,
        bgm_volume: bgmVolume,
        ducking_intensity: duckingIntensity,
        anti_copyright_shield: antiCopyrightShield,
        use_gpu: systemInfo?.nvenc_accelerated ?? true
      }

      const res = await fetch('/api/ai-shorts/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) throw new Error('Failed to start render')
    } catch (err) {
      setIsRendering(false)
      alert('Render initiation error: ' + err.message)
    }
  }

  // Format text according to selected case
  const formatWordCase = (word) => {
    if (!word) return ''
    if (subtitleTextCase === 'uppercase') return word.toUpperCase()
    if (subtitleTextCase === 'capitalize') return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    return word
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Hidden Audio Players */}
      <audio ref={voiceAudioRef} onEnded={() => setIsPlayingVoice(false)} />
      <audio ref={bgmAudioRef} loop />

      {/* Step Navigation Pill Bar */}
      <div
        className="card"
        style={{
          padding: '12px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-xs)',
              background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-indigo))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Wand2 size={16} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
              AI Shorts Studio Workflow
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Step {currentStep} of 4: {currentStep === 1 ? 'Script & Voiceover' : currentStep === 2 ? 'Scene Storyboard' : currentStep === 3 ? 'Creator Subtitles & Sound' : 'Master 9:16 Render'}
            </div>
          </div>
        </div>

        {/* Step Buttons */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {[
            { num: 1, label: '1. Script & Voice', icon: Mic },
            { num: 2, label: '2. Storyboard', icon: Film },
            { num: 3, label: '3. Subtitles & Sound', icon: Type },
            { num: 4, label: '4. Master Export', icon: Zap }
          ].map((step) => {
            const Icon = step.icon
            const isActive = currentStep === step.num
            const isPast = currentStep > step.num
            return (
              <button
                key={step.num}
                onClick={() => setCurrentStep(step.num)}
                style={{
                  background: isActive
                    ? 'linear-gradient(135deg, var(--accent-cyan), var(--accent-indigo))'
                    : isPast
                    ? 'rgba(6, 182, 212, 0.12)'
                    : 'rgba(255, 255, 255, 0.03)',
                  border: isActive ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                  color: isActive ? 'white' : isPast ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  padding: '7px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.2s ease',
                  boxShadow: isActive ? '0 0 15px rgba(6, 182, 212, 0.35)' : 'none'
                }}
              >
                {isPast ? <Check size={13} color="var(--accent-cyan)" /> : <Icon size={13} />}
                <span>{step.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* STEP 1: SCRIPT & NEURAL VOICEOVER GENERATOR */}
      {/* ========================================================================= */}
      {currentStep === 1 && (
        <div className="main-grid">
          {/* Left: Script Studio */}
          <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="var(--accent-cyan)" />
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Narration Script & AI Prompt</h3>
              </div>
              <span className="mono-metric" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {script.split(' ').filter(Boolean).length} words • ~{Math.round(script.split(' ').filter(Boolean).length / 2.5)}s duration
              </span>
            </div>

            {/* AI Topic Prompt Helper */}
            <div
              style={{
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label style={{ fontSize: '0.76rem', fontWeight: 800, color: 'var(--accent-cyan)', letterSpacing: '0.5px' }}>
                  ✨ GENERATE VIRAL SCRIPT FROM TOPIC
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={onOpenKeyModal}
                    style={{
                      background: 'rgba(6, 182, 212, 0.12)',
                      border: '1px solid rgba(6, 182, 212, 0.3)',
                      color: 'var(--accent-cyan)',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-xs)',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    🔑 Key Pool
                  </button>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    style={{ width: 'auto', padding: '4px 8px', fontSize: '0.74rem', borderRadius: 'var(--radius-xs)' }}
                  >
                    <option value="dramatic">Dramatic & Mystery</option>
                    <option value="storytelling">Storytelling & Facts</option>
                    <option value="motivational">Motivational</option>
                    <option value="educational">Educational</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Enter topic e.g. 3 Insane Facts About Black Holes..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                />
                <button
                  onClick={() => handleGenerateScriptAI()}
                  disabled={isGeneratingScript}
                  className="btn-primary"
                  style={{ padding: '0 20px', whiteSpace: 'nowrap' }}
                >
                  {isGeneratingScript ? <RefreshCw size={15} className="spin" /> : <Wand2 size={15} />}
                  <span>Generate</span>
                </button>
              </div>

              {/* Quick Topic Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                {TOPIC_SUGGESTIONS.map((t, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setTopic(t)
                      handleGenerateScriptAI(t)
                    }}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-xs)',
                      padding: '4px 8px',
                      fontSize: '0.7rem',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                  >
                    + {t}
                  </button>
                ))}
              </div>
            </div>

            {/* Narration Script Textarea */}
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, marginBottom: '6px', color: 'var(--text-secondary)' }}>
                Full Narration Script (Hook ➔ Escalate ➔ Reveal ➔ Loop)
              </label>
              <textarea
                rows={7}
                value={script}
                onChange={(e) => setScript(e.target.value)}
                placeholder="Paste or write your narration script here..."
                style={{ lineHeight: '1.6' }}
              />
            </div>

            <button
              onClick={handleGenerateVoiceAndScenes}
              disabled={isGeneratingTTS || isParsingScenes}
              className="btn-primary"
              style={{ width: '100%', padding: '14px' }}
            >
              {isGeneratingTTS ? (
                <>
                  <RefreshCw size={18} className="spin" />
                  <span>Synthesizing Neural Speech & Slicing Scenes...</span>
                </>
              ) : (
                <>
                  <span>Generate Voice & Proceed to Storyboard</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>

          {/* Right: Neural Voice Studio */}
          <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mic size={18} color="var(--accent-indigo)" />
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Neural Voice & Tone Engine</h3>
            </div>

            {/* Voice List */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-secondary)' }}>
                Select Hyper-Realistic Neural Voice (100% Free & Offline)
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '230px', overflowY: 'auto' }}>
                {voices.map((v) => {
                  const isSelected = selectedVoice === v.id
                  return (
                    <div
                      key={v.id}
                      onClick={() => setSelectedVoice(v.id)}
                      style={{
                        padding: '9px 12px',
                        borderRadius: 'var(--radius-sm)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.18)' : 'rgba(255, 255, 255, 0.02)',
                        border: isSelected ? '1px solid var(--accent-indigo)' : '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 800, fontSize: '0.85rem', color: isSelected ? '#c4b5fd' : 'white' }}>
                          {v.name}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {v.description}
                        </div>
                      </div>
                      <span
                        className="mono-metric"
                        style={{
                          fontSize: '0.68rem',
                          background: 'rgba(255, 255, 255, 0.05)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          color: 'var(--text-secondary)'
                        }}
                      >
                        {v.locale}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Voice Speed & Pitch Sliders */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '2px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Voice Speed</span>
                  <span className="mono-metric" style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>{voiceSpeed}x</span>
                </div>
                <input
                  type="range"
                  min="0.8"
                  max="1.3"
                  step="0.05"
                  value={voiceSpeed}
                  onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '2px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Pitch Shift</span>
                  <span className="mono-metric" style={{ color: 'var(--accent-indigo)', fontWeight: 700 }}>{voicePitch} cents</span>
                </div>
                <input
                  type="range"
                  min="-50"
                  max="50"
                  step="5"
                  value={voicePitch}
                  onChange={(e) => setVoicePitch(parseInt(e.target.value))}
                />
              </div>
            </div>

            {/* Custom Voice Upload Alternative */}
            <div
              style={{
                border: '1px dashed var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                textAlign: 'center',
                background: 'rgba(0, 0, 0, 0.3)'
              }}
            >
              <div style={{ fontSize: '0.82rem', fontWeight: 800, marginBottom: '2px' }}>
                📁 Have your own recorded voiceover?
              </div>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: '0 0 8px 0' }}>
                Upload any MP3/WAV audio track to sync and cut scenes automatically
              </p>
              <label
                className="btn-secondary"
                style={{ padding: '6px 14px', fontSize: '0.76rem', cursor: 'pointer' }}
              >
                <FileAudio size={13} />
                <span>{customVoiceFile ? customVoiceFile.name : 'Upload Audio Track'}</span>
                <input type="file" accept="audio/*" onChange={handleCustomVoiceUpload} style={{ display: 'none' }} />
              </label>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: INTERACTIVE STORYBOARD & SCENE MATCHER */}
      {/* ========================================================================= */}
      {currentStep === 2 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Film size={20} color="var(--accent-cyan)" />
                <span>Scene Storyboard & B-Roll Matcher ({scenes.length} Scenes)</span>
              </h3>
              <p style={{ margin: '3px 0 0 0', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                Each narration line is synchronized to its own visual clip and camera motion.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              {voiceAudioUrl && (
                <button
                  onClick={toggleVoicePlay}
                  className="btn-secondary"
                  style={{ padding: '8px 14px', fontSize: '0.82rem' }}
                >
                  {isPlayingVoice ? <Pause size={14} /> : <Play size={14} />}
                  <span>{isPlayingVoice ? 'Pause Voice' : 'Preview Full Voiceover'}</span>
                </button>
              )}

              <button
                onClick={() => setCurrentStep(3)}
                className="btn-primary"
                style={{ padding: '8px 18px', fontSize: '0.84rem' }}
              >
                <span>Next: Creator Subtitles & BGM</span>
                <ArrowRight size={15} />
              </button>
            </div>
          </div>

          {/* Grid of Scene Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {scenes.map((scene, idx) => (
              <div
                key={scene.id || idx}
                className="card"
                style={{
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '14px'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span
                      style={{
                        background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-indigo))',
                        color: 'white',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        fontSize: '0.7rem',
                        fontWeight: 900
                      }}
                    >
                      SCENE #{idx + 1}
                    </span>
                    <span className="mono-metric" style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={11} />
                      {scene.duration_seconds}s
                    </span>
                  </div>

                  <p
                    style={{
                      fontSize: '0.88rem',
                      lineHeight: '1.5',
                      color: 'var(--text-primary)',
                      margin: '0 0 10px 0',
                      background: 'rgba(0, 0, 0, 0.4)',
                      padding: '10px',
                      borderRadius: 'var(--radius-sm)',
                      borderLeft: '3px solid var(--accent-cyan)'
                    }}
                  >
                    "{scene.narration_text}"
                  </p>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {scene.visual_keywords?.map((kw, kIdx) => (
                      <span
                        key={kIdx}
                        style={{
                          background: 'rgba(255, 255, 255, 0.04)',
                          border: '1px solid var(--border-subtle)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '0.68rem',
                          color: 'var(--text-secondary)'
                        }}
                      >
                        #{kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                        Camera Zoom
                      </label>
                      <select
                        value={scene.camera_effect}
                        onChange={(e) => {
                          const upd = [...scenes]
                          upd[idx].camera_effect = e.target.value
                          setScenes(upd)
                        }}
                        style={{ padding: '5px 8px', fontSize: '0.76rem' }}
                      >
                        <option value="slow_zoom_in">Slow Zoom In</option>
                        <option value="punch_zoom">Punch-In Close-up</option>
                        <option value="slow_zoom_out">Slow Zoom Out</option>
                        <option value="pan_left">Pan Left</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                        SFX Trigger
                      </label>
                      <select
                        value={scene.sfx_trigger}
                        onChange={(e) => {
                          const upd = [...scenes]
                          upd[idx].sfx_trigger = e.target.value
                          setScenes(upd)
                        }}
                        style={{ padding: '5px 8px', fontSize: '0.76rem' }}
                      >
                        <option value="whoosh">Whoosh</option>
                        <option value="bass_drop">Sub-Bass Drop</option>
                        <option value="ding">Chime Ding</option>
                        <option value="glitch">Glitch FX</option>
                        <option value="none">None</option>
                      </select>
                    </div>
                  </div>

                  <div
                    style={{
                      background: 'rgba(0, 0, 0, 0.4)',
                      border: scene.video_source_path ? '1px solid var(--accent-emerald)' : '1px dashed var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 10px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Video size={13} color={scene.video_source_path ? 'var(--accent-emerald)' : 'var(--text-muted)'} />
                      <span style={{ color: scene.video_source_path ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                        {scene.video_source_path ? 'Custom Video Set' : 'Auto Motion Gradient'}
                      </span>
                    </div>

                    <label
                      style={{
                        background: 'rgba(255, 255, 255, 0.08)',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      <span>{scene.video_source_path ? 'Change' : 'Upload Clip'}</span>
                      <input
                        type="file"
                        accept="video/*"
                        onChange={(e) => e.target.files[0] && handleSceneVideoUpload(idx, e.target.files[0])}
                        style={{ display: 'none' }}
                      />
                    </label>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 3: PRO CREATOR SUBTITLES STUDIO & BGM MIXER */}
      {/* ========================================================================= */}
      {currentStep === 3 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.25fr 0.75fr', gap: '24px' }}>
          {/* Left: Custom Creator Subtitle Designer */}
          <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Type size={18} color="var(--accent-cyan)" />
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Top Creator Subtitle Presets</h3>
              </div>
              <span className="brand-tag">PRO CREATOR SUITE</span>
            </div>

            {/* Presets Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              {CREATOR_SUBTITLE_PRESETS.map((preset) => {
                const isSelected = selectedPresetId === preset.id
                return (
                  <div
                    key={preset.id}
                    onClick={() => handleSelectSubtitlePreset(preset)}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-md)',
                      background: isSelected ? 'rgba(6, 182, 212, 0.16)' : 'rgba(255, 255, 255, 0.02)',
                      border: isSelected ? '2px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      boxShadow: isSelected ? '0 0 20px rgba(6, 182, 212, 0.25)' : 'none'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                        <span style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', fontWeight: 800 }}>
                          {preset.creator}
                        </span>
                        <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '1px 4px', borderRadius: '3px' }}>
                          {preset.badge}
                        </span>
                      </div>
                      <div style={{ fontWeight: 800, fontSize: '0.82rem', color: 'white', marginBottom: '4px' }}>
                        {preset.name}
                      </div>
                    </div>

                    <div
                      style={{
                        background: '#000000',
                        padding: '6px',
                        borderRadius: '4px',
                        textAlign: 'center',
                        color: preset.activeColor,
                        fontWeight: 900,
                        fontSize: '0.78rem',
                        letterSpacing: '0.5px'
                      }}
                    >
                      VIRAL POP
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Customization Sliders & Controls */}
            <div
              style={{
                background: 'rgba(0, 0, 0, 0.45)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Palette size={14} color="var(--accent-cyan)" />
                <span style={{ fontSize: '0.8rem', fontWeight: 800, color: 'white', letterSpacing: '0.5px' }}>
                  FINE-TUNE CREATOR PARAMETERS
                </span>
              </div>

              {/* Row 1: Font & Words Per Line */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Font Family
                  </label>
                  <select
                    value={subtitleFont}
                    onChange={(e) => {
                      setSubtitleFont(e.target.value)
                      setSelectedPresetId('custom')
                    }}
                    style={{ padding: '7px 10px', fontSize: '0.78rem' }}
                  >
                    <option value="Montserrat">Montserrat ExtraBold (Modern Viral)</option>
                    <option value="Bebas Neue">Bebas Neue (Tall Editorial)</option>
                    <option value="Liberation Sans">Liberation Sans Bold (Clean Pro)</option>
                    <option value="Impact">Impact (Classic Beast)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Flash Speed / Words Per Line
                  </label>
                  <select
                    value={subtitleWordsPerLine}
                    onChange={(e) => {
                      setSubtitleWordsPerLine(parseInt(e.target.value))
                      setSelectedPresetId('custom')
                    }}
                    style={{ padding: '7px 10px', fontSize: '0.78rem' }}
                  >
                    <option value={1}>1 Word (Ultra-Fast Flash / Hormozi)</option>
                    <option value={2}>2 Words (Dynamic Sweet Spot)</option>
                    <option value={3}>3 Words (MrBeast Standard)</option>
                    <option value={4}>4 Words (Documentary Style)</option>
                  </select>
                </div>
              </div>

              {/* Row 2: Colors */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Active Word Highlight Color
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="color"
                      value={subtitleActiveColor}
                      onChange={(e) => {
                        setSubtitleActiveColor(e.target.value)
                        setSelectedPresetId('custom')
                      }}
                      style={{ width: '32px', height: '32px', border: 'none', borderRadius: '4px', cursor: 'pointer', background: 'transparent' }}
                    />
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {['#FFE600', '#22C55E', '#00F0FF', '#EF4444', '#FF007A', '#F59E0B'].map((hex) => (
                        <div
                          key={hex}
                          onClick={() => {
                            setSubtitleActiveColor(hex)
                            setSelectedPresetId('custom')
                          }}
                          style={{
                            width: '18px',
                            height: '18px',
                            borderRadius: '3px',
                            background: hex,
                            cursor: 'pointer',
                            border: subtitleActiveColor === hex ? '2px solid white' : '1px solid rgba(255,255,255,0.2)'
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                    Inactive Words Color
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="color"
                      value={subtitleInactiveColor}
                      onChange={(e) => {
                        setSubtitleInactiveColor(e.target.value)
                        setSelectedPresetId('custom')
                      }}
                      style={{ width: '32px', height: '32px', border: 'none', borderRadius: '4px', cursor: 'pointer', background: 'transparent' }}
                    />
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {['#FFFFFF', '#F1F5F9', '#94A3B8', '#F472B6'].map((hex) => (
                        <div
                          key={hex}
                          onClick={() => {
                            setSubtitleInactiveColor(hex)
                            setSelectedPresetId('custom')
                          }}
                          style={{
                            width: '18px',
                            height: '18px',
                            borderRadius: '3px',
                            background: hex,
                            cursor: 'pointer',
                            border: subtitleInactiveColor === hex ? '2px solid var(--accent-cyan)' : '1px solid rgba(255,255,255,0.2)'
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Row 3: Casing & Pill Box & Size */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                    Letter Casing
                  </label>
                  <select
                    value={subtitleTextCase}
                    onChange={(e) => {
                      setSubtitleTextCase(e.target.value)
                      setSelectedPresetId('custom')
                    }}
                    style={{ padding: '5px', fontSize: '0.74rem' }}
                  >
                    <option value="uppercase">ALL CAPS</option>
                    <option value="capitalize">Title Case</option>
                    <option value="original">Original</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                    Dark Pill Box
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', height: '28px' }}>
                    <input
                      type="checkbox"
                      checked={subtitleBackgroundBox}
                      onChange={(e) => {
                        setSubtitleBackgroundBox(e.target.checked)
                        setSelectedPresetId('custom')
                      }}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <span style={{ fontSize: '0.74rem' }}>{subtitleBackgroundBox ? 'Enabled' : 'None'}</span>
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '2px' }}>
                    Font Size ({subtitleFontSize}px)
                  </label>
                  <input
                    type="range"
                    min="36"
                    max="72"
                    step="2"
                    value={subtitleFontSize}
                    onChange={(e) => {
                      setSubtitleFontSize(parseInt(e.target.value))
                      setSelectedPresetId('custom')
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Royalty-Free BGM & Auto-Ducking */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <Music size={16} color="var(--accent-indigo)" />
                <h4 style={{ margin: 0, fontSize: '0.95rem' }}>Royalty-Free BGM & Auto-Ducking</h4>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '12px' }}>
                {[
                  { id: 'phonk_drive', name: 'Phonk Drive', genre: 'High Energy' },
                  { id: 'lofi_chill', name: 'Lo-Fi Chill', genre: 'Relaxed' },
                  { id: 'deep_tension', name: 'Deep Tension', genre: 'Suspense' },
                  { id: 'epic_discovery', name: 'Epic Discovery', genre: 'Atmospheric' },
                  { id: 'upbeat_viral', name: 'Upbeat Viral', genre: 'Tech Pop' },
                  { id: 'none', name: 'Mute BGM', genre: 'No Music' }
                ].map((track) => {
                  const isSelected = bgmTrack === track.id
                  const isPlaying = playingBgm === track.id
                  return (
                    <div
                      key={track.id}
                      onClick={() => toggleBgmPlay(track.id)}
                      style={{
                        padding: '8px 10px',
                        borderRadius: 'var(--radius-sm)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.22)' : 'rgba(255, 255, 255, 0.02)',
                        border: isSelected ? '1px solid var(--accent-indigo)' : '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '0.76rem', fontWeight: 800 }}>{track.name}</div>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>{track.genre}</div>
                      </div>
                      {track.id !== 'none' && (
                        <div style={{ color: isPlaying ? 'var(--accent-pink)' : 'var(--accent-indigo)' }}>
                          {isPlaying ? <Pause size={12} /> : <Play size={12} />}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Ducking Slider */}
              <div style={{ background: 'rgba(0,0,0,0.35)', padding: '10px 14px', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', marginBottom: '2px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>🎙️ Voice Auto-Ducking (Lowers BGM volume when voice speaks)</span>
                  <span className="mono-metric" style={{ color: 'var(--accent-cyan)', fontWeight: 800 }}>{Math.round(duckingIntensity * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0.4"
                  max="0.95"
                  step="0.05"
                  value={duckingIntensity}
                  onChange={(e) => setDuckingIntensity(parseFloat(e.target.value))}
                />
              </div>
            </div>
          </div>

          {/* Right: Phone Mockup Live Simulator */}
          <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '20px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Eye size={16} color="var(--accent-emerald)" />
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Live 9:16 Creator Preview</h3>
              </div>

              {/* Realistic Titanium Phone Frame */}
              <div
                style={{
                  width: '220px',
                  height: '390px',
                  margin: '0 auto',
                  background: 'linear-gradient(180deg, #141724, #080a10)',
                  borderRadius: '28px',
                  border: '4px solid #2e3448',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 20px 45px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.06)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  padding: '14px'
                }}
              >
                {/* Top Notch & Progress Bar */}
                {progressBar && (
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      height: '4px',
                      width: '45%',
                      background: progressBarColor,
                      boxShadow: `0 0 10px ${progressBarColor}`
                    }}
                  />
                )}

                <div style={{ fontSize: '0.62rem', color: '#64748b', textAlign: 'left', marginTop: '2px', letterSpacing: '0.5px' }}>
                  9:16 SHORTS
                </div>

                {/* Subtitle Mock on Video */}
                <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                  <div
                    style={{
                      display: 'inline-block',
                      background: subtitleBackgroundBox ? 'rgba(0, 0, 0, 0.8)' : 'transparent',
                      padding: subtitleBackgroundBox ? '6px 12px' : '0',
                      borderRadius: '8px',
                      fontFamily: subtitleFont,
                      fontWeight: 900,
                      fontSize: `${Math.round(subtitleFontSize * 0.38)}px`,
                      letterSpacing: subtitleFont === 'Bebas Neue' ? '1px' : '0.5px',
                      lineHeight: '1.2'
                    }}
                  >
                    <span
                      style={{
                        color: subtitleActiveColor,
                        display: 'inline-block',
                        transform: subtitleAnimation === 'pop' ? 'scale(1.15)' : 'none',
                        transition: 'transform 0.1s ease',
                        textShadow: subtitleOutlineWidth > 0 ? `0 0 ${subtitleOutlineWidth}px ${subtitleOutlineColor}` : 'none'
                      }}
                    >
                      {formatWordCase('VIRAL')}
                    </span>{' '}
                    <span
                      style={{
                        color: subtitleInactiveColor,
                        textShadow: subtitleOutlineWidth > 0 ? `0 0 ${subtitleOutlineWidth}px ${subtitleOutlineColor}` : 'none'
                      }}
                    >
                      {formatWordCase('SECRET')}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Anti-Copyright & Render Trigger */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)'
                }}
              >
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={15} />
                  <span>Apple iPhone EXIF & Anti-Copyright Shield</span>
                </div>
                <input
                  type="checkbox"
                  checked={antiCopyrightShield}
                  onChange={(e) => setAntiCopyrightShield(e.target.checked)}
                />
              </div>

              <button
                onClick={handleStartRender}
                className="btn-primary"
                style={{ width: '100%', padding: '14px', fontSize: '0.95rem' }}
              >
                <Zap size={18} />
                <span>Render Master 9:16 Short (GPU NVENC)</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* RENDERING PROGRESS MODAL */}
      {/* ========================================================================= */}
      {isRendering && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.88)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999
          }}
        >
          <div
            className="card"
            style={{
              width: '460px',
              padding: '32px',
              textAlign: 'center',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              boxShadow: '0 25px 60px rgba(0, 0, 0, 0.9)'
            }}
          >
            <div style={{ marginBottom: '18px' }}>
              <Zap size={38} color="var(--accent-cyan)" className="pulse-glow" />
            </div>
            <h3 style={{ fontSize: '1.3rem', fontWeight: 900, margin: '0 0 8px 0' }}>
              Rendering Master 9:16 Short
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', margin: '0 0 20px 0' }}>
              {renderStage || 'Compiling multi-scene stitches, BGM ducking & creator subtitles...'}
            </p>

            {/* Progress Bar */}
            <div
              style={{
                width: '100%',
                height: '8px',
                background: 'rgba(255, 255, 255, 0.08)',
                borderRadius: 'var(--radius-full)',
                overflow: 'hidden',
                marginBottom: '10px'
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${renderProgress}%`,
                  background: 'linear-gradient(90deg, var(--accent-cyan), var(--accent-indigo))',
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
            <div className="mono-metric" style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
              {renderProgress}%
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* COMPLETED RENDERED SHORT PLAYER */}
      {/* ========================================================================= */}
      {renderedVideoUrl && (
        <div
          className="card"
          style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(6, 182, 212, 0.08))',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            padding: '28px',
            textAlign: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '16px' }}>
            <CheckCircle2 size={24} color="var(--accent-emerald)" />
            <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 900 }}>Master 9:16 Short Export Ready!</h2>
          </div>

          <div style={{ maxWidth: '330px', margin: '0 auto 20px auto', borderRadius: '18px', overflow: 'hidden', boxShadow: '0 16px 40px rgba(0,0,0,0.7)' }}>
            <video
              src={renderedVideoUrl}
              controls
              autoPlay
              playsInline
              style={{ width: '100%', display: 'block' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '14px' }}>
            <a
              href={renderedVideoUrl}
              download={`ai_short_${renderJobId || 'clean'}.mp4`}
              className="btn-primary"
              style={{ padding: '12px 28px', textDecoration: 'none', background: 'linear-gradient(135deg, var(--accent-emerald), var(--accent-cyan))' }}
            >
              <Download size={18} />
              <span>Download Master Short MP4</span>
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
