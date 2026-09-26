# CR Remover Studio — Engineering & Coding Standards (AGENTS.md)

This document establishes the mandatory engineering principles, architecture guidelines, and coding best practices for all Python backend and React frontend development in this workspace.

---

## 1. Core Architecture Principles

1. **Decoupled Client-Server Boundary**:
   - Backend exposes a clean, type-safe REST & WebSocket API.
   - Frontend is a standalone React (Vite) application that can be built into static assets served by FastAPI.
2. **Fail-Safe & Graceful Fallbacks**:
   - Hardware detection must be automatic (NVIDIA NVENC GPU acceleration with seamless CPU `libx264` fallback).
   - Video processing errors must return structured error messages, not unhandled 500 exceptions.
3. **Resource & Memory Management**:
   - Never load entire multi-gigabyte video files into RAM. Use streaming I/O and disk-based temp staging.
   - Auto-clean temporary working files (extracted audio stems, intermediate frame buffers) in `finally:` blocks.
   - Revoke browser Blob / Object URLs (`URL.revokeObjectURL`) to prevent client-side memory leaks.

---

## 2. Python Backend Best Practices (FastAPI + FFmpeg + PyTorch)

### A. Type Safety & Validation
- Use Python 3.12 type annotations everywhere (`typing.Optional`, `typing.List`, `typing.Dict`).
- Use **Pydantic v2** models for all request schemas, preset parameters, and response structures.
- Enforce strict parameter validation (e.g. zoom between $1.0$ and $1.3$, pitch between $-100$ and $+100$ cents, speed between $0.8$ and $1.5$).

### B. Subprocess & FFmpeg Execution
- **Never use `shell=True`** with unsanitized inputs. Always pass arguments as explicit lists: `["ffmpeg", "-y", "-i", input_path, ...]`.
- Use `asyncio.create_subprocess_exec` for non-blocking execution inside FastAPI endpoints.
- Parse FFmpeg progress lines (`time=...`, `frame=...`) in real-time to compute progress percentages ($0\% \to 100\%$) and stream to clients via WebSockets.
- Gracefully handle codec errors and missing filters.

### C. AI Audio & Concurrency
- Lazy-load heavy AI models (Demucs / PyTorch) only when requested.
- Run heavy CPU/GPU rendering in background workers (`asyncio.to_thread` or BackgroundTasks) so the API server never blocks.
- Cache processed models in a dedicated cache directory.

### D. File System Organization
- Store uploads and outputs in structured directories:
  - `storage/uploads/`
  - `storage/processed/`
  - `storage/temp/`
- Generate unique UUIDs for all jobs to avoid file overwriting or race conditions.

---

## 3. React Frontend Best Practices (Vite + Modern React 18+)

### A. Component Architecture & Design
- **Single Responsibility Principle**: Keep components modular, isolated, and focused (e.g. `UploadZone`, `PresetCard`, `VideoComparePlayer`, `ProgressBar`).
- Use **Functional Components** with standard React hooks (`useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`).
- Avoid prop drilling; use clean state structures or React Context for global job state.

### B. UI/UX & Styling Guidelines
- **Modern Dark-Mode Aesthetic**: Premium cyber/studio theme (`#090a0f` background, `#121520` cards, glowing `#6366f1` / `#ec4899` gradients).
- **Vanilla CSS / CSS Modules / Variables**: Define a unified design token system in `index.css` (spacing, colors, border-radii, glassmorphic blurs).
- **Micro-Interactions**: Hover states, smooth scale transitions, loading skeletons, glowing drag-over dropzones.
- **Accessibility & Feedback**: Visual indicators for all states (Uploading, Processing, Rendering, Complete, Error).

### C. Media & Performance
- Use HTML5 `<video>` with hardware acceleration (`playsInline`, preload metadata).
- Video Comparison Slider: Synchronize playback timestamps between original and transformed video streams.
- Clean up WebSockets on component unmount to prevent ghost connections and memory leaks.

---

## 4. Testing & Verification Checklist

Before completing any feature:
1. **Backend**: Verify endpoints return valid JSON and appropriate HTTP status codes (200, 400, 404, 500).
2. **Pipeline**: Test sample video render with both GPU (if NVENC present) and CPU fallback.
3. **Frontend**: Verify responsive layout, drag-and-drop file upload, real-time WebSocket progress updates, and video download trigger.
4. **Clean Code**: Zero lint errors, no dead code or leftover console logs.
