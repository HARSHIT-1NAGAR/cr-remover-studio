import React, { useState } from 'react'
import { CheckCircle2, Download, RefreshCw } from 'lucide-react'

export default function VideoComparePlayer({ jobResult, originalVideo, onReset }) {
  const [tab, setTab] = useState('transformed')

  const fmt = (bytes) => {
    if (!bytes) return '—'
    const k = 1024, s = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / k ** i).toFixed(1)} ${s[i]}`
  }

  const handleDownload = () => {
    window.location.href = `/api/download/${jobResult.job_id}`
  }

  return (
    <div className="card" style={{ borderColor: 'rgba(34, 197, 94, 0.25)' }}>
      {/* Header */}
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-icon" style={{ background: 'var(--green-muted)', borderColor: 'rgba(34,197,94,.2)' }}>
            <CheckCircle2 size={14} color="var(--green)" />
          </div>
          Transformation Complete
          <span className="badge badge-green" style={{ marginLeft: '4px' }}>Ready</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-ghost" onClick={onReset}>
            <RefreshCw size={13} /> New Video
          </button>
          <button
            onClick={handleDownload}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '7px',
              padding: '7px 16px', border: 'none', borderRadius: 'var(--radius-sm)',
              background: 'var(--green)', color: '#fff', fontSize: '0.84rem',
              fontWeight: 600, cursor: 'pointer', transition: 'all var(--transition)'
            }}
          >
            <Download size={14} /> Download
          </button>
        </div>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {/* Tab Row */}
        <div className="tab-row" style={{ marginBottom: 0 }}>
          <button className={`tab-btn ${tab === 'transformed' ? 'active' : ''}`} onClick={() => setTab('transformed')}>
            Transformed
          </button>
          <button className={`tab-btn ${tab === 'original' ? 'active' : ''}`} onClick={() => setTab('original')}>
            Original
          </button>
        </div>

        {/* Video */}
        <div className="video-preview">
          {tab === 'transformed' && (
            <video src={jobResult.output_url} controls autoPlay style={{ width: '100%', maxHeight: '380px', objectFit: 'contain' }} />
          )}
          {tab === 'original' && originalVideo?.video_url && (
            <video src={originalVideo.video_url} controls style={{ width: '100%', maxHeight: '380px', objectFit: 'contain' }} />
          )}
        </div>

        {/* Meta */}
        <div className="file-meta-bar">
          <div className="meta-chip">📄 {jobResult.output_filename}</div>
          {jobResult.processed_size_bytes && (
            <div className="meta-chip">📦 {fmt(jobResult.processed_size_bytes)}</div>
          )}
          <div className="meta-chip" style={{ color: 'var(--green)' }}>✓ Fingerprints Disrupted</div>
          <div className="meta-chip" style={{ color: 'var(--green)' }}>✓ Clean EXIF</div>
        </div>
      </div>
    </div>
  )
}
