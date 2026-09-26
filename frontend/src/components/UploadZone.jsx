import React, { useState, useRef } from 'react'
import { UploadCloud, Film, CheckCircle2, Clock, Link2, Loader2, RefreshCw, X } from 'lucide-react'

export default function UploadZone({
  onVideoUploaded,
  onUrlDownload,
  uploadedVideo,
  isUploading,
  uploadProgress,
  isFetchingUrl,
  onResetVideo
}) {
  const [activeTab, setActiveTab] = useState('upload')
  const [videoUrl, setVideoUrl] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) validateAndUpload(e.dataTransfer.files[0])
  }

  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files?.[0]) validateAndUpload(e.target.files[0])
  }

  const validateAndUpload = (file) => {
    if (!file.type.startsWith('video/')) {
      alert('Please upload a valid video file (.mp4, .mov, .mkv, .avi)')
      return
    }
    onVideoUploaded(file)
  }

  const handleUrlSubmit = (e) => {
    e.preventDefault()
    if (!videoUrl.trim()) return
    onUrlDownload(videoUrl.trim())
  }

  const fmt = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024, s = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / k ** i).toFixed(1)} ${s[i]}`
  }

  const fmtDur = (s) => {
    if (!s) return '0:00'
    return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-icon"><Film size={14} /></div>
          Source Video
        </div>
        {uploadedVideo && (
          <button className="btn-ghost" onClick={onResetVideo} style={{ fontSize: '0.76rem', gap: '5px' }}>
            <RefreshCw size={12} /> Change
          </button>
        )}
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {/* Uploaded Video Preview */}
        {uploadedVideo ? (
          <div>
            <div className="video-preview">
              <video
                src={uploadedVideo.video_url}
                controls
                style={{ width: '100%', maxHeight: '220px', objectFit: 'contain' }}
              />
            </div>
            <div className="file-meta-bar" style={{ marginTop: '10px' }}>
              <div className="meta-chip">
                <CheckCircle2 size={11} color="var(--green)" />
                <span style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {uploadedVideo.filename}
                </span>
              </div>
              <div className="meta-chip">📦 {fmt(uploadedVideo.size_bytes)}</div>
              <div className="meta-chip">
                <Clock size={11} />
                {fmtDur(uploadedVideo.duration_seconds)}
              </div>
              {uploadedVideo.resolution && (
                <div className="meta-chip">📐 {uploadedVideo.resolution}</div>
              )}
              <div className="meta-chip">🎞️ {Math.round(uploadedVideo.fps || 30)} fps</div>
            </div>
          </div>
        ) : (
          <>
            {/* Tabs */}
            <div className="tab-row" style={{ marginBottom: 0 }}>
              <button
                className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
                onClick={() => setActiveTab('upload')}
              >
                Local File
              </button>
              <button
                className={`tab-btn ${activeTab === 'url' ? 'active' : ''}`}
                onClick={() => setActiveTab('url')}
              >
                URL / YouTube
              </button>
            </div>

            {/* Upload Tab */}
            {activeTab === 'upload' ? (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  style={{ display: 'none' }}
                  onChange={handleChange}
                />
                <div
                  className={`dropzone-container ${dragActive ? 'drag-active' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  style={{ padding: 'var(--space-8) var(--space-6)' }}
                >
                  <div className="upload-icon-pulse">
                    {isUploading
                      ? <Loader2 size={20} className="spin" />
                      : <UploadCloud size={20} />
                    }
                  </div>
                  <div>
                    <div className="dropzone-title" style={{ fontSize: '0.88rem' }}>
                      {isUploading ? 'Uploading…' : 'Drop video here or click to browse'}
                    </div>
                    <div className="dropzone-sub" style={{ marginTop: '4px' }}>
                      MP4, MOV, MKV, WebM — any size
                    </div>
                  </div>
                  {isUploading && (
                    <div className="progress-track" style={{ width: '80%' }}>
                      <div className="progress-fill animated" style={{ width: `${uploadProgress}%` }} />
                    </div>
                  )}
                </div>
              </>
            ) : (
              /* URL Tab */
              <form onSubmit={handleUrlSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ position: 'relative' }}>
                  <Link2
                    size={15}
                    style={{
                      position: 'absolute', left: '12px', top: '50%',
                      transform: 'translateY(-50%)', color: 'var(--text-muted)',
                      pointerEvents: 'none'
                    }}
                  />
                  <input
                    type="url"
                    placeholder="Paste YouTube, TikTok, or Instagram URL…"
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    style={{ paddingLeft: '36px' }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!videoUrl.trim() || isFetchingUrl}
                  className="btn-primary"
                  style={{ width: '100%' }}
                >
                  {isFetchingUrl ? (
                    <><Loader2 size={15} className="spin" /> Fetching…</>
                  ) : (
                    <>Fetch & Load Video</>
                  )}
                </button>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 0 }}>
                  Downloads up to 1080p — works with YouTube, TikTok, Instagram, Twitter/X
                </p>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  )
}
