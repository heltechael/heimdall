#!/bin/bash

# Print status of all RoboWeedMaps sync services and timers

echo "===== RoboWeedMaps Sync Status ====="
echo ""
echo "-- Image Sync Timer --"
systemctl status roboweedmaps-image-sync.timer
echo ""
echo "-- Image Sync Service --"
systemctl status roboweedmaps-image-sync.service
echo ""
echo "-- Database Sync Timer --"
systemctl status roboweedmaps-db-sync.timer
echo ""
echo "-- Database Sync Service --"
systemctl status roboweedmaps-db-sync.service
echo ""
echo "-- Recent Image Sync Logs --"
tail -n 10 /data/roboweedmaps/logs/image_sync_$(date +%Y%m%d).log 2>/dev/null || echo "No image sync logs for today"
echo ""
echo "-- Recent Database Sync Logs --"
tail -n 10 /data/roboweedmaps/logs/db_sync_$(date +%Y%m%d).log 2>/dev/null || echo "No database sync logs for today"
echo ""
echo "-- Database Sync State --"
cat /data/roboweedmaps/state/db_sync_state.json 2>/dev/null || echo "No database sync state file found"
