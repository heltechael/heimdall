#!/bin/bash

# Database Synchronization Script for RoboWeedMaps
# Created as part of the AU-loke automated sync system

# Configuration
BACKUP_DIR="/mnt/rwm-backup-db"
LOCAL_DIR="/data/roboweedmaps/database"
WORK_DIR="${LOCAL_DIR}/current"
LOG_DIR="/data/roboweedmaps/logs"
STATE_DIR="/data/roboweedmaps/state"
LOG_FILE="${LOG_DIR}/db_sync_$(date +%Y%m%d).log"
LOCK_FILE="${STATE_DIR}/db_sync.lock"
STATE_FILE="${STATE_DIR}/db_sync_state.json"
DB_NAME="RoboWeedMaps"
DB_USER="SA"
DB_PASSWORD="Robotbil123!"
SQL_DATA_DIR="/var/opt/mssql/data"

# Ensure directories exist
mkdir -p "$LOG_DIR" "$WORK_DIR" "$STATE_DIR"

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
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Starting database synchronization" | tee -a "$LOG_FILE"

# Check if source is mounted and accessible
if ! ls -la "$BACKUP_DIR" &>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Backup directory is not accessible. Aborting." | tee -a "$LOG_FILE"
    exit 1
fi

# Initialize the state file if it doesn't exist
if [ ! -f "$STATE_FILE" ]; then
    echo '{"last_full_backup": "", "last_diff_backup": "", "last_sync_time": ""}' > "$STATE_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Initialized state file" | tee -a "$LOG_FILE"
fi

# Read the current state
LAST_FULL_BACKUP=$(grep -o '"last_full_backup":"[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
LAST_DIFF_BACKUP=$(grep -o '"last_diff_backup":"[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Last full backup: $LAST_FULL_BACKUP" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Last diff backup: $LAST_DIFF_BACKUP" | tee -a "$LOG_FILE"

# Find the latest full and diff backups
LATEST_FULL_BACKUP=$(ls -1t "$BACKUP_DIR"/RoboWeedMaps-*-Full.zip 2>/dev/null | head -1)
LATEST_DIFF_BACKUP=$(ls -1t "$BACKUP_DIR"/RoboWeedMaps-*-Diff.zip 2>/dev/null | head -1)

# Extract backup names for easier comparison
LATEST_FULL_NAME=$(basename "$LATEST_FULL_BACKUP")
LATEST_DIFF_NAME=$(basename "$LATEST_DIFF_BACKUP")

echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Latest full backup: $LATEST_FULL_NAME" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Latest diff backup: $LATEST_DIFF_NAME" | tee -a "$LOG_FILE"

# Check if we need to do anything
if [ "$LATEST_FULL_NAME" = "$LAST_FULL_BACKUP" ] && [ "$LATEST_DIFF_NAME" = "$LAST_DIFF_BACKUP" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: No new backups found. Exiting." | tee -a "$LOG_FILE"
    exit 0
fi

# Clear working directory
rm -rf "${WORK_DIR:?}"/*
mkdir -p "$WORK_DIR"

# Process based on what's new
if [ "$LATEST_FULL_NAME" != "$LAST_FULL_BACKUP" ]; then
    # We have a new full backup - use it and the latest diff if available
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: New full backup found - performing full restore" | tee -a "$LOG_FILE"
    
    # Copy and extract the full backup
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Copying full backup" | tee -a "$LOG_FILE"
    cp "$LATEST_FULL_BACKUP" "$WORK_DIR/full_backup.zip"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Extracting full backup" | tee -a "$LOG_FILE"
    cd "$WORK_DIR" || exit 1
    unzip -o full_backup.zip
    FULL_BAK=$(ls -1 *Full.bak | head -1)
    
    if [ -z "$FULL_BAK" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Failed to extract full backup .bak file" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    # Drop the existing database if it exists
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Dropping existing database if it exists" | tee -a "$LOG_FILE"
    /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "IF DB_ID('$DB_NAME') IS NOT NULL BEGIN ALTER DATABASE [$DB_NAME] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [$DB_NAME]; END"
    
    # Restore the full backup with NORECOVERY if we have a diff, or with RECOVERY if we don't
    if [ -n "$LATEST_DIFF_NAME" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Restoring full backup with NORECOVERY to allow differential" | tee -a "$LOG_FILE"
        /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "RESTORE DATABASE $DB_NAME FROM DISK = N'$WORK_DIR/$FULL_BAK' WITH MOVE 'RoboWeedSupport' TO '$SQL_DATA_DIR/$DB_NAME.mdf', MOVE 'RoboWeedSupport_log' TO '$SQL_DATA_DIR/${DB_NAME}_log.ldf', NORECOVERY"
        
        # Now apply the diff backup
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Copying differential backup" | tee -a "$LOG_FILE"
        cp "$LATEST_DIFF_BACKUP" "$WORK_DIR/diff_backup.zip"
        
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Extracting differential backup" | tee -a "$LOG_FILE"
        unzip -o diff_backup.zip
        DIFF_BAK=$(ls -1 *Diff.bak | head -1)
        
        if [ -z "$DIFF_BAK" ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Failed to extract differential backup .bak file" | tee -a "$LOG_FILE"
            # Recover the database anyway with what we have
            /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "RESTORE DATABASE $DB_NAME WITH RECOVERY"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Applying differential backup with RECOVERY" | tee -a "$LOG_FILE"
            /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "RESTORE DATABASE $DB_NAME FROM DISK = N'$WORK_DIR/$DIFF_BAK' WITH RECOVERY"
        fi
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Restoring full backup with RECOVERY (no differential)" | tee -a "$LOG_FILE"
        /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "RESTORE DATABASE $DB_NAME FROM DISK = N'$WORK_DIR/$FULL_BAK' WITH MOVE 'RoboWeedSupport' TO '$SQL_DATA_DIR/$DB_NAME.mdf', MOVE 'RoboWeedSupport_log' TO '$SQL_DATA_DIR/${DB_NAME}_log.ldf', RECOVERY"
    fi
    
    # Update state file with the new backups
    echo "{\"last_full_backup\": \"$LATEST_FULL_NAME\", \"last_diff_backup\": \"$LATEST_DIFF_NAME\", \"last_sync_time\": \"$(date '+%Y-%m-%d %H:%M:%S')\"}" > "$STATE_FILE"
    
elif [ -n "$LATEST_DIFF_NAME" ] && [ "$LATEST_DIFF_NAME" != "$LAST_DIFF_BACKUP" ]; then
    # We have the same full backup but a new diff backup
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Same full backup but new differential backup found" | tee -a "$LOG_FILE"
    
    # We need to restore the full backup with NORECOVERY and then apply the new diff
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Copying full backup" | tee -a "$LOG_FILE"
    cp "$BACKUP_DIR/$LAST_FULL_BACKUP" "$WORK_DIR/full_backup.zip"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Extracting full backup" | tee -a "$LOG_FILE"
    cd "$WORK_DIR" || exit 1
    unzip -o full_backup.zip
    FULL_BAK=$(ls -1 *Full.bak | head -1)
    
    if [ -z "$FULL_BAK" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Failed to extract full backup .bak file" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    # Drop the existing database if it exists
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Dropping existing database if it exists" | tee -a "$LOG_FILE"
    /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "IF DB_ID('$DB_NAME') IS NOT NULL BEGIN ALTER DATABASE [$DB_NAME] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE [$DB_NAME]; END"
    
    # Restore the full backup with NORECOVERY
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Restoring full backup with NORECOVERY" | tee -a "$LOG_FILE"
    /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "RESTORE DATABASE $DB_NAME FROM DISK = N'$WORK_DIR/$FULL_BAK' WITH MOVE 'RoboWeedSupport' TO '$SQL_DATA_DIR/$DB_NAME.mdf', MOVE 'RoboWeedSupport_log' TO '$SQL_DATA_DIR/${DB_NAME}_log.ldf', NORECOVERY"
    
    # Now apply the diff backup
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Copying differential backup" | tee -a "$LOG_FILE"
    cp "$LATEST_DIFF_BACKUP" "$WORK_DIR/diff_backup.zip"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Extracting differential backup" | tee -a "$LOG_FILE"
    unzip -o diff_backup.zip
    DIFF_BAK=$(ls -1 *Diff.bak | head -1)
    
    if [ -z "$DIFF_BAK" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Failed to extract differential backup .bak file" | tee -a "$LOG_FILE"
        # Recover the database anyway with what we have
        /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "RESTORE DATABASE $DB_NAME WITH RECOVERY"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Applying differential backup with RECOVERY" | tee -a "$LOG_FILE"
        /opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -Q "RESTORE DATABASE $DB_NAME FROM DISK = N'$WORK_DIR/$DIFF_BAK' WITH RECOVERY"
    fi
    
    # Update state file with the new diff backup
    echo "{\"last_full_backup\": \"$LAST_FULL_BACKUP\", \"last_diff_backup\": \"$LATEST_DIFF_NAME\", \"last_sync_time\": \"$(date '+%Y-%m-%d %H:%M:%S')\"}" > "$STATE_FILE"
fi

# Verify the database is accessible
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Verifying database" | tee -a "$LOG_FILE"
DB_CHECK=$(/opt/mssql-tools/bin/sqlcmd -S localhost -U "$DB_USER" -P "$DB_PASSWORD" -d "$DB_NAME" -Q "SELECT TOP 1 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES" -h -1)

if [ -z "$DB_CHECK" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Database verification failed" | tee -a "$LOG_FILE"
    exit 1
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Database verified successfully" | tee -a "$LOG_FILE"
fi

# Run verification script if it exists
if [ -f "/data/roboweedmaps/scripts/db/verify_database.py" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Running database verification script" | tee -a "$LOG_FILE"
    python /data/roboweedmaps/scripts/db/verify_database.py >> "$LOG_FILE" 2>&1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') INFO: Database synchronization completed successfully" | tee -a "$LOG_FILE"

exit 0
