#!/usr/bin/env bash
set -e

# AO-03 Automated Backup Script
# Creates a timestamped dump of MongoDB ao03 database (if available)
# and archives data/scenarios into backup/

BACKUP_DIR="backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TARGET_DIR="${BACKUP_DIR}/${TIMESTAMP}"

echo "=========================================="
echo " Starting AO-03 Data & Telemetry Backup"
echo " Target: ${TARGET_DIR}"
echo "=========================================="

mkdir -p "${TARGET_DIR}"

# 1. MongoDB dump if mongodump exists and Mongo is reachable
if command -v mongodump &> /dev/null; then
    echo "Attempting MongoDB database 'ao03' export..."
    mongodump --db=ao03 --out="${TARGET_DIR}/mongo_dump" --quiet || echo "Notice: MongoDB mongodump skipped (not running or auth required)."
else
    echo "Notice: mongodump utility not found; skipping binary MongoDB dump."
fi

# 2. Archive data/scenarios JSONL & metadata
if [ -d "data/scenarios" ]; then
    echo "Archiving data/scenarios directory..."
    tar -czf "${TARGET_DIR}/scenarios_archive.tar.gz" -C data scenarios
    echo "Scenarios archive saved to ${TARGET_DIR}/scenarios_archive.tar.gz"
fi

# 3. Archive audit logs
if [ -d "logs" ]; then
    echo "Archiving logs..."
    tar -czf "${TARGET_DIR}/logs_archive.tar.gz" -C logs . 2>/dev/null || true
fi

echo "=========================================="
echo " Backup finished successfully!"
echo " Location: ${TARGET_DIR}"
echo "=========================================="
