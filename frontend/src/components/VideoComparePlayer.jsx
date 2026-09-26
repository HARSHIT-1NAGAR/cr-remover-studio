import React, { useState } from 'react'
import { CheckCircle2, Download, RefreshCw, FolderOpen, Check } from 'lucide-react'

export default function VideoComparePlayer({ jobResult, originalVideo, onReset }) {
  const [tab, setTab] = useState('transformed')
  const [isExporting, setIsExporting] = useState(false)
  const [exportedInfo, setExportedInfo] = useState(null)

  const fmt = (bytes) => {
    if (!bytes) return '—'
    const k = 1024, s = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / k ** i).toFixed(1)} ${s[i]}`
  }

  const handleDownload = () => {
    window.location.href = `/api/download/${jobResult.job_id}`
  }

  const handleExportToDesktop = async () => {
    setIsExporting(true)
    try {
      const res = await fetch('/api/exports/export-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobResult.job_id,
          title: originalVideo?.filename || jobResult.output_filename || 'Cleaned_Video',
          preset: 'youtube_bypass',
          category: 'full_videos',
          aspect: '16x9'
        })
      })
      if (res.ok) {
        const data = await res.json()
        setExportedInfo(data)
      } else {
        alert('Failed to export to Desktop')
      }
    } catch (err) {
      console.error(err)
      alert('Error exporting: ' + err.message)
    } finally {
      setIsExporting(false)
    }
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
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button className="btn-ghost" onClick={onReset}>
            <RefreshCw size={13} /> New Video
          </button>
          <button
            onClick={handleExportToDesktop}
            disabled={isExporting}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '7px',
              padding: '7px 14px', border: '1px solid rgba(56, 189, 248, 0.4)', borderRadius: 'var(--radius-sm)',
              background: exportedInfo ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.12)',
              color: exportedInfo ? '#34d399' : '#7dd3fc', fontSize: '0.84rem',
              fontWeight: 600, cursor: 'pointer', transition: 'all var(--transition)'
            }}
            title="Save into ~/Desktop/CR_Remover_Exports/02_Full_Edited_Videos/"
          >
            {exportedInfo ? <Check size={14} /> : <FolderOpen size={14} />}
            {exportedInfo ? 'Saved to Desktop' : isExporting ? 'Exporting...' : 'Save to Desktop'}
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
          {exportedInfo && (
            <div className="meta-chip" style={{ color: '#38bdf8', background: 'rgba(56, 189, 248, 0.12)', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
              📁 Desktop: {exportedInfo.filename} ({exportedInfo.category})
            </div>
          )}
          <div className="meta-chip" style={{ color: 'var(--green)' }}>✓ Fingerprints Disrupted</div>
          <div className="meta-chip" style={{ color: 'var(--green)' }}>✓ Clean EXIF</div>
        </div>
      </div>
    </div>
  )
}
