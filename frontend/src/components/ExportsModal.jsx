import React, { useState, useEffect } from 'react'
import {
  FolderOpen, Sparkles, Video, MessageSquare, Mic, Image as ImageIcon,
  Music, FileText, Layers, Download, RefreshCw, X, ExternalLink, HardDrive, CheckCircle
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
      case 'Sparkles': return <Sparkles size={16} color="#818cf8" />
      case 'Video': return <Video size={16} color="#38bdf8" />
      case 'MessageSquare': return <MessageSquare size={16} color="#fb923c" />
      case 'Mic': return <Mic size={16} color="#ec4899" />
      case 'Image': return <ImageIcon size={16} color="#facc15" />
      case 'Music': return <Music size={16} color="#a855f7" />
      case 'FileText': return <FileText size={16} color="#34d399" />
      case 'Layers': return <Layers size={16} color="#f43f5e" />
      default: return <FolderOpen size={16} color="#94a3b8" />
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
        backgroundColor: 'rgba(5, 7, 15, 0.85)',
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
          background: '#0d111d',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '920px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 30px rgba(99, 102, 241, 0.15)',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.08) 0%, transparent 100%)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'rgba(99, 102, 241, 0.15)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <FolderOpen size={20} color="#818cf8" />
            </div>
            <div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                Desktop Exports Vault
                <span
                  style={{
                    fontSize: '0.72rem',
                    padding: '2px 8px',
                    borderRadius: '9999px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#34d399',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    fontWeight: 600
                  }}
                >
                  Categorized & Named
                </span>
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
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
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#cbd5e1',
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
                background: 'rgba(255, 255, 255, 0.05)',
                border: 'none',
                color: '#94a3b8',
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
            background: 'rgba(0, 0, 0, 0.3)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: '#cbd5e1' }}>
            <HardDrive size={14} color="#818cf8" />
            <span style={{ color: '#94a3b8' }}>Desktop Location:</span>
            <code
              onClick={handleCopyPath}
              title="Click to copy path"
              style={{
                background: 'rgba(99, 102, 241, 0.1)',
                padding: '3px 8px',
                borderRadius: '6px',
                color: '#c7d2fe',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                cursor: 'pointer',
                fontSize: '0.78rem'
              }}
            >
              {summary?.root_path || '~/Desktop/CR_Remover_Exports'}
            </code>
            {copiedPath && <span style={{ color: '#34d399', fontSize: '0.75rem' }}>✓ Copied</span>}
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
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
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
                  background: selectedFolder === 'all' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: selectedFolder === 'all' ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.06)',
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
                  <FolderOpen size={16} color="#818cf8" />
                  <div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f1f5f9' }}>All Recent</div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
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
                      background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                      border: isSelected ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.06)',
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
                        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f1f5f9' }}>{folder.label}</div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
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
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {selectedFolder === 'all' ? 'All Recent Exports' : `Files in ${selectedFolder}`}
              </div>
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                {displayFiles.length} item{displayFiles.length === 1 ? '' : 's'}
              </span>
            </div>

            {displayFiles.length === 0 ? (
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px dashed rgba(255, 255, 255, 0.08)',
                  borderRadius: '10px',
                  padding: '30px',
                  textAlign: 'center',
                  color: '#64748b'
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
                  background: 'rgba(0, 0, 0, 0.2)',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  borderRadius: '10px',
                  overflow: 'hidden'
                }}
              >
                {displayFiles.map((f, idx) => (
                  <div
                    key={f.filename + idx}
                    style={{
                      padding: '10px 16px',
                      borderBottom: idx === displayFiles.length - 1 ? 'none' : '1px solid rgba(255, 255, 255, 0.04)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '12px',
                      background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                      <div
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '6px',
                          background: 'rgba(255, 255, 255, 0.04)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0
                        }}
                      >
                        {f.extension === '.mp4' || f.extension === '.webm' ? (
                          <Video size={14} color="#38bdf8" />
                        ) : f.extension === '.jpg' || f.extension === '.png' ? (
                          <ImageIcon size={14} color="#facc15" />
                        ) : f.extension === '.mp3' || f.extension === '.wav' ? (
                          <Music size={14} color="#a855f7" />
                        ) : (
                          <FileText size={14} color="#34d399" />
                        )}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div
                          title={f.filename}
                          style={{
                            fontSize: '0.82rem',
                            fontWeight: 600,
                            color: '#e2e8f0',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}
                        >
                          {f.filename}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', display: 'flex', gap: '10px', marginTop: '2px' }}>
                          <span style={{ color: '#818cf8' }}>{f.category}</span>
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
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        color: '#94a3b8',
                        textDecoration: 'none',
                        fontSize: '0.75rem',
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
