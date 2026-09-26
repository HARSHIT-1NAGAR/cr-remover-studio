import React from 'react'
import { Loader2, AlertCircle, X } from 'lucide-react'

export default function ProgressModal({ progress, stage, isFailed, errorMessage, onCancel }) {
  return (
    <div className="modal-backdrop">
      <div className="modal-box" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-5)' }}>
        {/* Icon */}
        <div style={{
          width: '56px', height: '56px', borderRadius: '50%',
          background: isFailed ? 'var(--red-muted)' : 'var(--accent-muted)',
          border: `1px solid ${isFailed ? 'rgba(239,68,68,.2)' : 'var(--accent-border)'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {isFailed
            ? <AlertCircle size={26} color="var(--red)" />
            : <Loader2 size={26} color="var(--accent)" className="spin" />
          }
        </div>

        {/* Text */}
        <div>
          <h3 style={{ fontSize: '1.05rem', marginBottom: '4px' }}>
            {isFailed ? 'Transformation Failed' : 'Processing Video…'}
          </h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            {isFailed
              ? (errorMessage || 'An unexpected error occurred.')
              : (stage || 'Applying anti-fingerprint pipeline…')
            }
          </p>
        </div>

        {/* Progress bar */}
        {!isFailed && (
          <div style={{ width: '100%' }}>
            <div className="progress-track">
              <div className="progress-fill animated" style={{ width: `${progress}%` }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
              <span>{stage || 'Rendering…'}</span>
              <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{progress}%</span>
            </div>
          </div>
        )}

        {/* GPU note */}
        {!isFailed && (
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
            NVENC GPU acceleration active
          </div>
        )}

        {/* Error dismiss */}
        {isFailed && (
          <button className="btn-ghost" onClick={onCancel}>
            <X size={14} /> Close & Retry
          </button>
        )}
      </div>
    </div>
  )
}
