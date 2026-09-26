#!/bin/bash
# ==============================================================================
# Native Desktop App Launcher for CR Remover Studio
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Check if backend server is running; if not, launch in background
if ! curl -s http://localhost:8000/api/system >/dev/null 2>&1; then
    echo "Starting backend server..."
    "$SCRIPT_DIR/start.sh" >/dev/null 2>&1 &
    
    # Wait for server to become responsive
    for i in {1..20}; do
        if curl -s http://localhost:8000/api/system >/dev/null 2>&1; then
            break
        fi
        sleep 0.3
    done
fi

# 2. Launch in standalone native window mode (No browser tabs or URL bars)
URL="http://localhost:8000"
APP_TITLE="CR Remover Studio"
USER_DATA="/tmp/cr_remover_desktop_profile"

if command -v google-chrome >/dev/null 2>&1; then
    google-chrome --app="$URL" --window-size=1360,920 --user-data-dir="$USER_DATA" --class="cr-remover-studio" "$@"
elif command -v brave-browser >/dev/null 2>&1; then
    brave-browser --app="$URL" --window-size=1360,920 --user-data-dir="$USER_DATA" --class="cr-remover-studio" "$@"
elif command -v chromium >/dev/null 2>&1; then
    chromium --app="$URL" --window-size=1360,920 --user-data-dir="$USER_DATA" --class="cr-remover-studio" "$@"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"
fi
