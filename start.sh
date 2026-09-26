#!/bin/bash
# ==============================================================================
# CR REMOVER STUDIO — Automated Video Transformation & Remixing App
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================="
echo "⚡ Starting CR Remover Studio (100% Free & Offline)"
echo "🖥️ Hardware: NVIDIA GTX 1650 (NVENC) + Ryzen 5600H"
echo "🌐 Local URL: http://localhost:8000"
echo "================================================================="

# Activate Python virtual environment
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run the FastAPI server which serves the API and the built React UI
python3 backend/run.py
