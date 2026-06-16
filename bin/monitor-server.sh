#!/bin/bash
# Agent Notify Server Monitor
# Checks if server is running, restarts if needed

PORT=8765
PROJECT_DIR="/home/chenxilin/.local/share/agent-notify"
LOG_FILE="/tmp/agent-notify.log"
PID_FILE="/tmp/agent-notify.pid"

cd "$PROJECT_DIR"

# Check if port is in use
check_port() {
    ss -tlnp | grep -q ":$PORT"
    return $?
}

# Start server
start_server() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting server on port $PORT" >> "$LOG_FILE"
    nohup python3 -m agent_notify.server $PORT >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 3
}

# Main check
if ! check_port; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Server not running, restarting..." >> "$LOG_FILE"

    # Kill any stale process
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null
        rm -f "$PID_FILE"
    fi

    start_server

    if check_port; then
        echo "[$(date '+%Y-m-%d %H:%M:%S')] Server started successfully" >> "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed to start server" >> "$LOG_FILE"
    fi
fi