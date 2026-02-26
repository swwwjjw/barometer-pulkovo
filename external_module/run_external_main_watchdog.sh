#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_FILE="$SCRIPT_DIR/external_main.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RESTART_DELAY="${RESTART_DELAY:-5}"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/external_main_watchdog.log}"

child_pid=""
stop_requested=0

log() {
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" | tee -a "$LOG_FILE"
}

shutdown() {
    stop_requested=1
    log "Stop signal received. Shutting down watchdog..."

    if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
        kill "$child_pid" 2>/dev/null || true
        wait "$child_pid" 2>/dev/null || true
    fi
}

trap shutdown SIGINT SIGTERM

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Error: Python executable '$PYTHON_BIN' was not found." >&2
    exit 1
fi

if [[ ! -f "$APP_FILE" ]]; then
    echo "Error: '$APP_FILE' not found." >&2
    exit 1
fi

log "Watchdog started for external_main.py (python: $PYTHON_BIN, restart delay: ${RESTART_DELAY}s)"

while (( stop_requested == 0 )); do
    (
        cd "$SCRIPT_DIR" || exit 1
        "$PYTHON_BIN" "$APP_FILE"
    ) &
    child_pid=$!

    wait "$child_pid"
    exit_code=$?
    child_pid=""

    if (( stop_requested == 1 )); then
        break
    fi

    log "external_main.py exited with code ${exit_code}. Restarting in ${RESTART_DELAY}s..."
    sleep "$RESTART_DELAY"
done

log "Watchdog stopped."
