#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_FILE="$SCRIPT_DIR/external_main.py"
PYTHON_BIN="${PYTHON_BIN:-}"
VENV_PATH="${VENV_PATH:-}"
RESTART_DELAY="${RESTART_DELAY:-5}"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/external_main_watchdog.log}"

child_pid=""
stop_requested=0
user_supplied_python=0
user_supplied_venv=0

if [[ -n "$PYTHON_BIN" ]]; then
    user_supplied_python=1
fi

if [[ -n "$VENV_PATH" ]]; then
    user_supplied_venv=1
fi

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

resolve_python() {
    local candidate=""
    local -a venv_candidates=()

    if (( user_supplied_venv == 1 )); then
        venv_candidates+=("$VENV_PATH")
    fi
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        venv_candidates+=("$VIRTUAL_ENV")
    fi

    venv_candidates+=(
        "$SCRIPT_DIR/.venv"
        "$SCRIPT_DIR/venv"
        "$SCRIPT_DIR/../.venv"
        "$SCRIPT_DIR/../venv"
    )

    for candidate in "${venv_candidates[@]}"; do
        [[ -z "$candidate" ]] && continue
        if [[ -x "$candidate/bin/python" ]]; then
            VENV_PATH="$candidate"
            PYTHON_BIN="$candidate/bin/python"
            return 0
        fi
    done

    if (( user_supplied_venv == 1 )); then
        echo "Error: VENV_PATH '$VENV_PATH' does not contain bin/python." >&2
        return 1
    fi

    if (( user_supplied_python == 1 )); then
        if [[ -x "$PYTHON_BIN" ]]; then
            return 0
        fi
        if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
            PYTHON_BIN="$(command -v "$PYTHON_BIN")"
            return 0
        fi
        echo "Error: Python executable '$PYTHON_BIN' was not found." >&2
        return 1
    fi

    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3)"
        return 0
    fi

    if command -v python >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python)"
        return 0
    fi

    echo "Error: No Python interpreter found. Install Python or set VENV_PATH/PYTHON_BIN." >&2
    return 1
}

if ! resolve_python; then
    exit 1
fi

if [[ ! -f "$APP_FILE" ]]; then
    echo "Error: '$APP_FILE' not found." >&2
    exit 1
fi

if [[ -n "$VENV_PATH" ]]; then
    export VIRTUAL_ENV="$VENV_PATH"
    export PATH="$VENV_PATH/bin:$PATH"
    log "Using virtual environment: $VENV_PATH"
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
