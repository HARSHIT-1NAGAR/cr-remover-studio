import React from 'react'
import { Eye, Volume2, Smartphone, Shield, ShieldCheck } from 'lucide-react'

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

  const score = Math.min(99, 30
    + (params.dynamic_time_warp ? 20 : 0)
    + (params.harmonic_notch_eq ? 18 : 0)
    + (params.camera_exif_injection ? 12 : 0)
    + (params.ken_burns_zoom >= 1.04 ? 10 : 0)
    + (params.film_grain >= 1.0 ? 5 : 0)
    + (params.color_grade ? 5 : 0)
    + (params.isolate_vocals ? 15 : 0)
    + (params.mirror_flip ? 5 : 0)
  )

  const scoreColor = score >= 90 ? 'var(--green)' : score >= 70 ? 'var(--amber)' : 'var(--red)'

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
        {/* Visual & Temporal */}
        <SectionLabel icon={Eye}>Visual & Temporal</SectionLabel>

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
          label="Ken Burns Zoom"
          desc="Continuous pan motion to disrupt spatial keyframe histograms"
          min={1.00} max={1.15} step={0.01}
          value={params.ken_burns_zoom}
          onChange={e => update('ken_burns_zoom', parseFloat(e.target.value))}
          format={v => `${Math.round((v - 1) * 100)}%`}
        />
        <SliderRow
          label="Film Grain"
          desc="Micro-pixel dither to break exact pixel hashes"
          min={0} max={5} step={0.5}
          value={params.film_grain}
          onChange={e => update('film_grain', parseFloat(e.target.value))}
          format={v => `${v.toFixed(1)}%`}
        />

        {/* Audio */}
        <SectionLabel icon={Volume2}>Audio & Acoustic</SectionLabel>

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
            label="GPU Encoding (NVENC)"
            desc="NVIDIA hardware encoding — preserves 1080p quality at CQ-17"
            checked={params.use_gpu}
            onChange={e => update('use_gpu', e.target.checked)}
          />
        </div>
      </div>
    </div>
  )
}
