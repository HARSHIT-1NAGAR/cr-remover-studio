import React, { useState, useEffect, useRef } from 'react'
import Header from './components/Header'
import UploadZone from './components/UploadZone'
import PresetSelector from './components/PresetSelector'
import TransformSettings from './components/TransformSettings'
import VideoComparePlayer from './components/VideoComparePlayer'
import ProgressModal from './components/ProgressModal'
import AutoViralStudio from './components/AutoViralStudio'
import AIShortsStudio from './components/AIShortsStudio'
import AutoPilotStudio from './components/AutoPilotStudio'
import GeminiKeyModal from './components/GeminiKeyModal'
import { Sparkles } from 'lucide-react'

export default function App() {
  const [activeMode, setActiveMode] = useState('autopilot')
  const [systemInfo, setSystemInfo] = useState(null)
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false)
  const [poolKeyCount, setPoolKeyCount] = useState(0)


  const [presets, setPresets] = useState(null)
  const [selectedPreset, setSelectedPreset] = useState('youtube_bypass')

  const [params, setParams] = useState({
    preset: 'youtube_bypass',
    mirror_flip: false,
    ken_burns_zoom: 1.07,
    color_grade: true,
    film_grain: 2.0,
    tilt_3d: false,
    shorts_vertical_916: false,
    dynamic_time_warp: true,
    watermark_blur: false,
    watermark_position: 'bottom_right',
    pitch_cents: -30,
    speed_factor: 1.03,
    harmonic_notch_eq: true,
    isolate_vocals: false,
    add_ambience: true,
    ambience_volume: 0.015,
    strip_metadata: true,
    camera_exif_injection: true,
    use_gpu: true,
  })

  const [uploadedVideo, setUploadedVideo] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isFetchingUrl, setIsFetchingUrl] = useState(false)

  const [activeJobId, setActiveJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStage, setCurrentStage] = useState('')
  const [errorMessage, setErrorMessage] = useState(null)

  const wsRef = useRef(null)

  useEffect(() => {
    fetch('/api/system')
      .then(r => r.json())
      .then(setSystemInfo)
      .catch(console.error)

    fetch('/api/presets')
      .then(r => r.json())
      .then(data => {
        setPresets(data)
        if (data?.youtube_bypass) {
          setParams(p => ({ ...p, ...data.youtube_bypass.params, preset: 'youtube_bypass' }))
        }
      })
      .catch(console.error)

    fetch('/api/gemini/pool-status')
      .then(r => r.json())
      .then(data => {
        if (data && typeof data.active_keys === 'number') {
          setPoolKeyCount(data.total_keys || data.active_keys)
        }
      })
      .catch(console.error)
  }, [])

  const handleSelectPreset = (key) => {
    setSelectedPreset(key)
    if (presets?.[key]) setParams({ ...params, ...presets[key].params, preset: key })
  }

  const handleVideoUploaded = async (file) => {
    setIsUploading(true)
    setUploadProgress(20)
    setJobStatus(null)
    const fd = new FormData()
    fd.append('file', file)
    try {
      setUploadProgress(50)
      const res = await fetch('/api/upload', { method: 'POST', body: fd })
      if (!res.ok) throw new Error('Upload failed')
      const data = await res.json()
      setUploadProgress(100)
      setUploadedVideo(data)
      setActiveJobId(data.job_id)
    } catch (err) {
      alert('Upload error: ' + err.message)
    } finally {
      setIsUploading(false)
    }
  }

  const handleUrlDownload = async (url) => {
    setIsFetchingUrl(true)
    setJobStatus(null)
    try {
      const res = await fetch('/api/download-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Download failed') }
      const data = await res.json()
      setUploadedVideo(data)
      setActiveJobId(data.job_id)
    } catch (err) {
      alert('URL error: ' + err.message)
    } finally {
      setIsFetchingUrl(false)
    }
  }

  const handleStartTransform = async () => {
    if (!activeJobId || !uploadedVideo) return
    setIsProcessing(true)
    setProgress(0)
    setCurrentStage('Initializing pipeline…')
    setErrorMessage(null)

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    wsRef.current?.close()
    const ws = new WebSocket(`${proto}//${window.location.host}/ws/progress/${activeJobId}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        setProgress(msg.progress || 0)
        setCurrentStage(msg.current_stage || 'Processing…')
        if (msg.status === 'completed') {
          fetch(`/api/jobs/${activeJobId}`).then(r => r.json()).then(job => {
            setJobStatus(job)
            setIsProcessing(false)
          })
          ws.close()
        } else if (msg.status === 'failed') {
          setErrorMessage(msg.current_stage || 'Rendering error')
          setIsProcessing(false)
          ws.close()
        }
      } catch {}
    }

    try {
      const res = await fetch(`/api/transform/${activeJobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })
      if (!res.ok) throw new Error('Failed to start transformation')
    } catch (err) {
      setErrorMessage(err.message)
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setUploadedVideo(null)
    setActiveJobId(null)
    setJobStatus(null)
    setProgress(0)
    setCurrentStage('')
    setErrorMessage(null)
  }

  return (
    <div className="app-container">
      <Header
        systemInfo={systemInfo}
        activeMode={activeMode}
        onModeChange={setActiveMode}
        onOpenKeyModal={() => setIsKeyModalOpen(true)}
        keyCount={poolKeyCount}
      />

      {activeMode === 'autopilot' ? (
        <AutoPilotStudio systemInfo={systemInfo} onOpenKeyModal={() => setIsKeyModalOpen(true)} />
      ) : activeMode === 'ai_shorts' ? (
        <AIShortsStudio systemInfo={systemInfo} onOpenKeyModal={() => setIsKeyModalOpen(true)} />
      ) : activeMode === 'auto_viral' ? (
        <AutoViralStudio onOpenKeyModal={() => setIsKeyModalOpen(true)} />
      ) : jobStatus?.status === 'completed' ? (
        <VideoComparePlayer jobResult={jobStatus} originalVideo={uploadedVideo} onReset={handleReset} />
      ) : (
        <div className="main-grid">
          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <UploadZone
              onVideoUploaded={handleVideoUploaded}
              onUrlDownload={handleUrlDownload}
              uploadedVideo={uploadedVideo}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
              isFetchingUrl={isFetchingUrl}
              onResetVideo={handleReset}
            />
            <PresetSelector
              selectedPreset={selectedPreset}
              onSelectPreset={handleSelectPreset}
              presets={presets}
            />
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <TransformSettings params={params} setParams={setParams} />
            <button
              className="btn-primary"
              disabled={!uploadedVideo || isProcessing || isUploading}
              onClick={handleStartTransform}
            >
              <Sparkles size={16} />
              {!uploadedVideo ? 'Upload a video to get started' : 'Transform Video — Anti-Copyright Shield'}
            </button>
          </div>
        </div>
      )}

      {/* Gemini Multi-Key Pool Manager Modal */}
      <GeminiKeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        onKeysUpdated={(pool) => {
          if (pool && typeof pool.active_keys === 'number') {
            setPoolKeyCount(pool.total_keys || pool.active_keys)
          }
        }}
      />

      {/* Processing Modal — Studio mode */}
      {isProcessing && activeMode === 'studio' && (
        <ProgressModal
          progress={progress}
          stage={currentStage}
          isFailed={!!errorMessage}
          errorMessage={errorMessage}
          onCancel={() => { setIsProcessing(false); setErrorMessage(null) }}
        />
      )}
    </div>
  )
}
