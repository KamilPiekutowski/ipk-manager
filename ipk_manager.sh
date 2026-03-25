#!/bin/bash
TARGET_DIR="$1"

# 1. Kill the old one (keep your existing logic, it's good)
PID=$(lsof -t -i:8001)
if [ -n "$PID" ]; then
    kill -9 $PID
    sleep 1
fi
fuser -k 8001/tcp 2>/dev/null

# 2. Use setsid to run in a completely new session
# This ensures it survives even if Gunicorn kills the script
setsid python3 -m http.server 8001 --directory "$TARGET_DIR" --bind 0.0.0.0 > /dev/null 2>&1 &

