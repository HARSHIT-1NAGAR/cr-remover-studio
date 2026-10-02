import React from 'react'
import { Eye, Volume2, Smartphone, Shield, ShieldCheck, Sparkles, Monitor } from 'lucide-react'

function Toggle({ label, desc, checked, onChange }) {
  return (
    <div className="toggle-row">
      <div className="toggle-label">
        <span className="toggle-label-text">{label}</span>
        {desc && <span className="toggle-label-desc">{desc}</span>}
      </div>
      <label className="toggle-switch">
        <input type="checkbox" checked={checked} onChange={onChange} />
        <span className="toggle-slider" />
      </label>
    </div>
  )
}

function SliderRow({ label, desc, min, max, step, value, onChange, format }) {
  return (
    <div style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>{label}</div>
          {desc && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>{desc}</div>}
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: '0.78rem', fontWeight: 600,
          color: 'var(--accent)', background: 'var(--accent-muted)', border: '1px solid var(--accent-border)',
          padding: '2px 8px', borderRadius: 'var(--radius-full)', whiteSpace: 'nowrap', marginLeft: '12px'
        }}>
          {format ? format(value) : value}
        </span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={onChange} />
    </div>
  )
}

function SectionLabel({ icon: Icon, children }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '7px',
      fontSize: '0.72rem', fontWeight: 600, letterSpacing: '0.06em',
      textTransform: 'uppercase', color: 'var(--text-muted)',
      marginTop: 'var(--space-5)', marginBottom: 'var(--space-2)',
      paddingBottom: 'var(--space-2)', borderBottom: '1px solid var(--border)'
    }}>
      <Icon size={13} />
      {children}
    </div>
  )
}

export default function TransformSettings({ params, setParams }) {
  const update = (key, val) => setParams(prev => ({ ...prev, [key]: val, preset: 'custom' }))

  const score = Math.min(99, 35
    + (params.dynamic_time_warp ? 22 : 0)
    + (params.harmonic_notch_eq ? 20 : 0)
    + (params.camera_exif_injection ? 15 : 0)
    + (params.ken_burns_zoom >= 1.04 ? 12 : 0)
    + (params.color_grade ? 6 : 0)
    + (params.isolate_vocals ? 15 : 0)
    + (params.mirror_flip ? 5 : 0)
  )

  const scoreColor = score >= 90 ? 'var(--green)' : score >= 70 ? 'var(--amber)' : 'var(--red)'
  const currentRes = params.render_resolution || 'original'

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-icon"><Shield size={14} /></div>
          Anti-Copyright Shield
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '4px 10px', borderRadius: 'var(--radius-full)',
          background: score >= 90 ? 'var(--green-muted)' : 'var(--amber-muted)',
          border: `1px solid ${score >= 90 ? 'rgba(34,197,94,.2)' : 'rgba(245,158,11,.2)'}`,
          fontSize: '0.76rem', fontWeight: 600, color: scoreColor
        }}>
          <ShieldCheck size={12} />
          {score}% Protected
        </div>
      </div>

      <div className="card-body">
        {/* Output Resolution & Quality */}
        <SectionLabel icon={Monitor}>Master Render Resolution & Clarity</SectionLabel>

        <div style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Target Output Resolution</div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Upscale to cinema 4K UHD or preserve 100% native source resolution
              </div>
            </div>
            <span style={{
              fontSize: '0.74rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px',
              background: currentRes === '4k' ? 'rgba(236,72,153,0.15)' : 'rgba(99,102,241,0.15)',
              color: currentRes === '4k' ? '#ec4899' : '#818cf8',
              border: `1px solid ${currentRes === '4k' ? 'rgba(236,72,153,0.3)' : 'rgba(99,102,241,0.3)'}`
            }}>
              {currentRes === '4k' ? '👑 4K UHD (50Mbps)' : currentRes === '2k' ? '🌟 2K QHD (30Mbps)' : currentRes === '1080p' ? '📺 1080p FHD' : '💎 Original (Source Match)'}
            </span>
          </div>

          {/* Resolution Options Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginTop: '8px' }}>
            {[
              { id: 'original', label: '💎 Original (Source Match)', desc: '100% lossless native pixels, zero downscale' },
              { id: '4k', label: '👑 4K Ultra HD (Master)', desc: '3840×2160 / 2160×3840 (50 Mbps Cinema)' },
              { id: '2k', label: '🌟 2K QHD (Studio)', desc: '2560×1440 / 1440×2560 (30 Mbps Pro)' },
              { id: '1080p', label: '📺 1080p Full HD', desc: '1920×1080 / 1080×1920 standard' }
            ].map(r => (
              <button
                key={r.id}
                type="button"
                onClick={() => update('render_resolution', r.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  gap: '3px',
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: currentRes === r.id ? '1px solid #818cf8' : '1px solid var(--border)',
                  background: currentRes === r.id ? 'rgba(99, 102, 241, 0.14)' : 'var(--card-bg)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: currentRes === r.id ? '#a5b4fc' : 'var(--text-primary)' }}>
                  {r.label}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {r.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        <Toggle
          label="Clarity & Detail Boost (Unsharp)"
          desc="Adaptive spatial sharpening to restore razor-sharp edges and high-frequency textures"
          checked={params.clarity_boost ?? false}
          onChange={e => update('clarity_boost', e.target.checked)}
        />

        {/* Visual & Temporal */}
        <SectionLabel icon={Eye}>Visual & Temporal Protections</SectionLabel>

        <Toggle
          label="Dynamic Time-Warping"
          desc="Sine-wave speed variation to break Content ID temporal matching"
          checked={params.dynamic_time_warp ?? true}
          onChange={e => update('dynamic_time_warp', e.target.checked)}
        />
        <Toggle
          label="Mirror Flip"
          desc="Flip video horizontally — keep off if video has text or logos"
          checked={params.mirror_flip ?? false}
          onChange={e => update('mirror_flip', e.target.checked)}
        />
        <Toggle
          label="Color Grading"
          desc="Enhances RGB curves and saturation without degradation"
          checked={params.color_grade}
          onChange={e => update('color_grade', e.target.checked)}
        />
        <Toggle
          label="Watermark Blur (Delogo)"
          desc="Blurs corner handles and TikTok watermarks"
          checked={params.watermark_blur ?? false}
          onChange={e => update('watermark_blur', e.target.checked)}
        />
        <Toggle
          label="9:16 Vertical Shorts Canvas"
          desc="Converts 16:9 landscape to vertical with blurred background"
          checked={params.shorts_vertical_916}
          onChange={e => update('shorts_vertical_916', e.target.checked)}
        />

        <SliderRow
          label="Ken Burns Dynamic Pan & Zoom"
          desc="Smooth continuous pan motion to disrupt spatial keyframe hashes"
          min={1.00} max={1.15} step={0.01}
          value={params.ken_burns_zoom}
          onChange={e => update('ken_burns_zoom', parseFloat(e.target.value))}
          format={v => `${Math.round((v - 1) * 100)}%`}
        />
        <SliderRow
          label="Film Grain (Noise)"
          desc="Set to 0% for pure crystal-clean video; higher values add micro-texture"
          min={0} max={5} step={0.5}
          value={params.film_grain ?? 0}
          onChange={e => update('film_grain', parseFloat(e.target.value))}
          format={v => v === 0 ? '0.0% (Clean / No Grain)' : `${v.toFixed(1)}%`}
        />

        {/* Audio */}
        <SectionLabel icon={Volume2}>Audio & Acoustic Desync</SectionLabel>

        <Toggle
          label="4-Band Harmonic Notch EQ"
          desc="Attenuates 420 Hz, 1250 Hz, 3450 Hz, 6200 Hz to shatter acoustic fingerprints"
          checked={params.harmonic_notch_eq ?? true}
          onChange={e => update('harmonic_notch_eq', e.target.checked)}
        />
        <Toggle
          label="AI Speech Isolation (Demucs)"
          desc="Removes 100% of copyrighted background music via stem separation"
          checked={params.isolate_vocals}
          onChange={e => update('isolate_vocals', e.target.checked)}
        />

        <SliderRow
          label="Pitch Shift"
          desc="Micro-shifts pitch to disrupt Chromaprint fingerprinting"
          min={-60} max={60} step={5}
          value={params.pitch_cents}
          onChange={e => update('pitch_cents', parseInt(e.target.value))}
          format={v => `${v > 0 ? '+' : ''}${v}¢`}
        />
        <SliderRow
          label="Speed Multiplier"
          desc="Adjusts playback speed with automatic pitch correction"
          min={0.95} max={1.10} step={0.01}
          value={params.speed_factor}
          onChange={e => update('speed_factor', parseFloat(e.target.value))}
          format={v => `${v.toFixed(2)}×`}
        />

        {/* Device & Encoding */}
        <SectionLabel icon={Smartphone}>Device Signatures & Encoding</SectionLabel>

        <Toggle
          label="iPhone 15 Pro Max EXIF Injection"
          desc="Injects authentic iOS 17.5 camera metadata to appear as genuine phone footage"
          checked={params.camera_exif_injection ?? true}
          onChange={e => update('camera_exif_injection', e.target.checked)}
        />
        <Toggle
          label="Strip Metadata"
          desc="Removes all embedded identifiable file metadata"
          checked={params.strip_metadata}
          onChange={e => update('strip_metadata', e.target.checked)}
        />
        <div className="toggle-row" style={{ borderBottom: 'none' }}>
          <Toggle
            label="GPU Encoding (NVIDIA NVENC)"
            desc="High-bitrate cinema rendering with zero CPU bottleneck (up to 50 Mbps 4K)"
            checked={params.use_gpu}
            onChange={e => update('use_gpu', e.target.checked)}
          />
        </div>
      </div>
    </div>
  )
}
