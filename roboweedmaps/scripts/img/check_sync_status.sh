#!/bin/bash

# Script to monitor rsync progress in real-time

echo "===== RoboWeedMaps Image Sync Progress ====="

# Log file path
LOG_FILE="/data/roboweedmaps/logs/image_sync_$(date +%Y%m%d).log"

# Check if rsync is running
if pgrep -f "rsync.*roboweedmaps/images" > /dev/null; then
    echo "STATUS: Rsync is currently running"
    
    # Show basic process info
    RSYNC_PID=$(pgrep -f "rsync.*roboweedmaps/images")
    echo "Process ID: $RSYNC_PID"
    echo "Running for: $(ps -o etime= -p $RSYNC_PID)"
    
    echo -e "\nFollowing log file in real-time. Press Ctrl+C to exit."
    echo "----------------------------------------"
    # Follow the log in real-time
    tail -f "$LOG_FILE"
else
    echo "STATUS: Rsync is not currently running"
    
    if [ -f "$LOG_FILE" ]; then
        echo -e "\nLast 20 lines from today's log file:"
        echo "----------------------------------------"
        tail -n 20 "$LOG_FILE"
    else
        echo "No log file found for today."
    fi
fi
