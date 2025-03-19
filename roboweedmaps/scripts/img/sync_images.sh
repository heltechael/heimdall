#!/bin/bash

# Image Synchronization Script for RoboWeedMaps
# Created as part of the AU-loke automated sync system

# Configuration
SOURCE_DIR="/mnt/rwm-data/main-data/"
DEST_DIR="/data/roboweedmaps/images/"
LOG_DIR="/data/roboweedmaps/logs"
LOG_FILE="${LOG_DIR}/image_sync_$(date +%Y%m%d).log"
LOCK_FILE="/data/roboweedmaps/state/image_sync.lock"
RSYNC_OPTS="-avz --delete --stats --progress --timeout=3600"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Check if another instance is running
if [ -f "$LOCK_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Another sync process is already running. If this is incorrect, remove $LOCK_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# Create lock file
touch "$LOCK_FILE"

# Function to clean up on exit
cleanup() {
    rm -f "$LOCK_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Lock file removed" >> "$LOG_FILE"
}

# Register cleanup function
trap cleanup EXIT

# Log start
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Starting image synchronization" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Source: $SOURCE_DIR" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Destination: $DEST_DIR" >> "$LOG_FILE"

# Check if source directory exists and is accessible
if [ ! -d "$SOURCE_DIR" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Source directory does not exist. Aborting." | tee -a "$LOG_FILE"
    exit 1
fi

# Check if we can read from the source directory
if [ ! -r "$SOURCE_DIR" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Source directory is not readable. Aborting." | tee -a "$LOG_FILE"
    exit 1
fi

# Try to list files to verify it's working
if ! ls -la "$SOURCE_DIR" &>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Cannot list files in source directory. The network mount may not be accessible. Aborting." | tee -a "$LOG_FILE"
    exit 1
fi

# Run rsync with error handling
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Starting rsync operation" >> "$LOG_FILE"

# Run rsync and capture output and exit status
rsync_output=$(rsync $RSYNC_OPTS "$SOURCE_DIR" "$DEST_DIR" 2>&1 | tee -a "$LOG_FILE")
rsync_status=$?

# Log rsync output
echo "$rsync_output" >> "$LOG_FILE"

# Check rsync status
if [ $rsync_status -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Rsync completed successfully" | tee -a "$LOG_FILE"
    
    # Extract stats
    transferred=$(echo "$rsync_output" | grep "files transferred:" | awk '{print $NF}')
    total_size=$(echo "$rsync_output" | grep "Total transferred file size:" | awk '{print $5,$6}')
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Files transferred: $transferred, Size: $total_size" | tee -a "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Rsync failed with status $rsync_status" | tee -a "$LOG_FILE"
    # You could add mail notification for failures here
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Image synchronization finished" | tee -a "$LOG_FILE"

exit $rsync_status
