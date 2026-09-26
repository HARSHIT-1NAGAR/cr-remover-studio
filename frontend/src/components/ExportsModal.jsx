import React, { useState, useEffect } from 'react'
import {
  FolderOpen, Sparkles, Video, MessageSquare, Mic, Image as ImageIcon,
  Music, FileText, Layers, Download, RefreshCw, X, ExternalLink, HardDrive
} from 'lucide-react'

export default function ExportsModal({ isOpen, onClose }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedFolder, setSelectedFolder] = useState('all')
  const [openingFolder, setOpeningFolder] = useState(false)
  const [copiedPath, setCopiedPath] = useState(false)

  const fetchSummary = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/exports/summary')
      if (res.ok) {
        const data = await res.json()
        setSummary(data)
      }
    } catch (err) {
      console.error('Error fetching exports summary:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchSummary()
    }
  }, [isOpen])

  const handleOpenDesktopFolder = async () => {
    setOpeningFolder(true)
    try {
      await fetch('/api/exports/open-desktop-folder', { method: 'POST' })
    } catch (err) {
      console.error('Failed to open folder:', err)
    } finally {
      setTimeout(() => setOpeningFolder(false), 1000)
    }
  }

  const handleCopyPath = () => {
    if (summary?.root_path) {
      navigator.clipboard.writeText(summary.root_path)
      setCopiedPath(true)
      setTimeout(() => setCopiedPath(false), 2000)
    }
  }

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  const getCategoryIcon = (iconName) => {
    switch (iconName) {
      case 'Sparkles': return <Sparkles size={16} color="var(--accent, #6366f1)" />
      case 'Video': return <Video size={16} color="#0284c7" />
      case 'MessageSquare': return <MessageSquare size={16} color="#ea580c" />
      case 'Mic': return <Mic size={16} color="#db2777" />
      case 'Image': return <ImageIcon size={16} color="#ca8a04" />
      case 'Music': return <Music size={16} color="#9333ea" />
      case 'FileText': return <FileText size={16} color="#16a34a" />
      case 'Layers': return <Layers size={16} color="#e11d48" />
      default: return <FolderOpen size={16} color="var(--text-muted)" />
    }
  }

  if (!isOpen) return null

  // Filter files based on selected folder
  let displayFiles = summary?.recent_files || []
  if (selectedFolder !== 'all' && summary?.folders) {
    const found = summary.folders.find((f) => f.id === selectedFolder)
    displayFiles = found ? found.files : []
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 15, 0.75)',
        backdropFilter: 'blur(12px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '920px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-card)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'var(--accent-muted)',
                border: '1px solid var(--accent-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <FolderOpen size={20} color="var(--accent)" />
            </div>
            <div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                Desktop Exports Vault
                <span
                  style={{
                    fontSize: '0.72rem',
                    padding: '2px 8px',
                    borderRadius: '9999px',
                    background: 'var(--green-muted)',
                    color: 'var(--green)',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    fontWeight: 600
                  }}
                >
                  Categorized & Named
                </span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                All exported videos, covers, audio, and SEO tags organized neatly on your Desktop
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={fetchSummary}
              disabled={loading}
              title="Refresh files"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
                padding: '7px 10px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.78rem'
              }}
            >
              <RefreshCw size={13} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '8px'
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Path Bar & Quick Action */}
        <div
          style={{
            padding: '12px 24px',
            background: 'var(--bg-elevated)',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-primary)' }}>
            <HardDrive size={14} color="var(--accent)" />
            <span style={{ color: 'var(--text-muted)' }}>Desktop Location:</span>
            <code
              onClick={handleCopyPath}
              title="Click to copy path"
              style={{
                background: 'var(--bg-surface)',
                padding: '3px 8px',
                borderRadius: '6px',
                color: 'var(--accent)',
                border: '1px solid var(--border)',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: 600
              }}
            >
              {summary?.root_path || '~/Desktop/CR_Remover_Exports'}
            </code>
            {copiedPath && <span style={{ color: 'var(--green)', fontSize: '0.75rem', fontWeight: 600 }}>✓ Copied</span>}
          </div>

          <button
            onClick={handleOpenDesktopFolder}
            style={{
              background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
              border: 'none',
              color: '#fff',
              padding: '7px 16px',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 12px rgba(79, 70, 229, 0.3)'
            }}
          >
            <ExternalLink size={13} />
            <span>{openingFolder ? 'Opening...' : '📂 Open in File Explorer'}</span>
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Categories Grid */}
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
              Vault Categories
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                gap: '10px'
              }}
            >
              {/* All Category Filter */}
              <div
                onClick={() => setSelectedFolder('all')}
                style={{
                  background: selectedFolder === 'all' ? 'var(--accent-muted)' : 'var(--bg-card)',
                  border: selectedFolder === 'all' ? '1px solid var(--accent)' : '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FolderOpen size={16} color="var(--accent)" />
                  <div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>All Recent</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {summary?.total_files || 0} files ({formatBytes(summary?.total_bytes)})
                    </div>
                  </div>
                </div>
              </div>

              {summary?.folders?.map((folder) => {
                const isSelected = selectedFolder === folder.id
                return (
                  <div
                    key={folder.id}
                    onClick={() => setSelectedFolder(folder.id)}
                    style={{
                      background: isSelected ? 'var(--accent-muted)' : 'var(--bg-card)',
                      border: isSelected ? '1px solid var(--accent)' : '1px solid var(--border)',
                      borderRadius: '10px',
                      padding: '12px 14px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {getCategoryIcon(folder.icon)}
                      <div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{folder.label}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {folder.file_count} files {folder.file_count > 0 && `(${formatBytes(folder.total_bytes)})`}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Files List */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {selectedFolder === 'all' ? 'All Recent Exports' : `Files in ${selectedFolder}`}
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {displayFiles.length} item{displayFiles.length === 1 ? '' : 's'}
              </span>
            </div>

            {displayFiles.length === 0 ? (
              <div
                style={{
                  background: 'var(--bg-card)',
                  border: '1px dashed var(--border)',
                  borderRadius: '10px',
                  padding: '30px',
                  textAlign: 'center',
                  color: 'var(--text-muted)'
                }}
              >
                <FolderOpen size={28} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <div style={{ fontSize: '0.85rem' }}>No exported files in this folder yet</div>
                <div style={{ fontSize: '0.75rem', marginTop: '4px' }}>
                  Exported videos and assets will be automatically placed here with crystal-clear filenames.
                </div>
              </div>
            ) : (
              <div
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  overflow: 'hidden'
                }}
              >
                {displayFiles.map((f, idx) => (
                  <div
                    key={f.filename + idx}
                    style={{
                      padding: '10px 16px',
                      borderBottom: idx === displayFiles.length - 1 ? 'none' : '1px solid var(--border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '12px',
                      background: idx % 2 === 0 ? 'transparent' : 'var(--bg-elevated)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                      <div
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '6px',
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0
                        }}
                      >
                        {f.extension === '.mp4' || f.extension === '.webm' ? (
                          <Video size={14} color="#0284c7" />
                        ) : f.extension === '.jpg' || f.extension === '.png' ? (
                          <ImageIcon size={14} color="#ca8a04" />
                        ) : f.extension === '.mp3' || f.extension === '.wav' ? (
                          <Music size={14} color="#9333ea" />
                        ) : (
                          <FileText size={14} color="#16a34a" />
                        )}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div
                          title={f.filename}
                          style={{
                            fontSize: '0.82rem',
                            fontWeight: 600,
                            color: 'var(--text-primary)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}
                        >
                          {f.filename}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', gap: '10px', marginTop: '2px' }}>
                          <span style={{ color: 'var(--accent)', fontWeight: 500 }}>{f.category}</span>
                          <span>•</span>
                          <span>{formatBytes(f.size_bytes)}</span>
                          <span>•</span>
                          <span>{f.modified_formatted}</span>
                        </div>
                      </div>
                    </div>

                    <a
                      href={`/api/media/${f.category}/${encodeURIComponent(f.filename)}`}
                      download={f.filename}
                      title="Download File"
                      style={{
                        padding: '5px 10px',
                        borderRadius: '6px',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border)',
                        color: 'var(--text-secondary)',
                        textDecoration: 'none',
                        fontSize: '0.75rem',
                        fontWeight: 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        flexShrink: 0
                      }}
                    >
                      <Download size={12} />
                      <span>Download</span>
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
