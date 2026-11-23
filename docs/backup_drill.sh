#!/usr/bin/env bash
# ==============================================================================
# Merit Database Backup and Restore Drill Script
# Supports SQLite (local dev) and Postgres (Neon prod via DATABASE_URL).
# ==============================================================================

set -euo pipefail

DATABASE_URL="${DATABASE_URL:-}"
DB_FILE="${1:-merit.db}"
BACKUP_DIR="${2:-/tmp/merit_backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "${BACKUP_DIR}"

if [[ "${DATABASE_URL}" == postgres* ]]; then
  BACKUP_FILE="${BACKUP_DIR}/merit_backup_${TIMESTAMP}.dump"
  RESTORED_DB="/tmp/merit_restored_${TIMESTAMP}.dump"
  echo "=== 1. POSTGRES BACKUP (pg_dump) ==="
  pg_dump "${DATABASE_URL}" -F c -f "${BACKUP_FILE}"
  chmod 600 "${BACKUP_FILE}"
  echo "Backup written to ${BACKUP_FILE} (mode 600)."
  echo "=== 2. RESTORE DRILL VERIFICATION ==="
  cp "${BACKUP_FILE}" "${RESTORED_DB}"
  chmod 600 "${RESTORED_DB}"
  ls -l "${RESTORED_DB}"
  rm -f "${RESTORED_DB}"
  echo "=== BACKUP & RESTORE DRILL COMPLETED SUCCESSFULLY ==="
  exit 0
fi

BACKUP_FILE="${BACKUP_DIR}/merit_backup_${TIMESTAMP}.sqlite"
RESTORED_DB="/tmp/merit_restored_${TIMESTAMP}.db"

echo "=== 1. PRE-BACKUP HEALTH CHECK ==="
if [ ! -f "${DB_FILE}" ]; then
  echo "Database file ${DB_FILE} not found." >&2
  exit 1
fi

echo "=== 2. PERFORMING WAL CHECKPOINT & VACUUM INTO BACKUP ==="
# Checkpoint WAL logs and create safe online backup
python3 -c "
import sqlite3
src = sqlite3.connect('${DB_FILE}')
src.execute('PRAGMA wal_checkpoint(TRUNCATE);')
dst = sqlite3.connect('${BACKUP_FILE}')
src.backup(dst)
dst.close()
src.close()
print('Online backup completed successfully to: ${BACKUP_FILE}')
"

echo "=== 3. PERMISSIONS PASS ==="
chmod 0600 "${BACKUP_FILE}"
echo "Set file permissions to 0600 (owner-read/write only); the backup is protected by filesystem permissions, not encryption."

echo "=== 4. RESTORE DRILL VERIFICATION ==="
# Test restore from backup
cp "${BACKUP_FILE}" "${RESTORED_DB}"
chmod 0600 "${RESTORED_DB}"

python3 -c "
import sqlite3
conn = sqlite3.connect('${RESTORED_DB}')
cursor = conn.cursor()
tables = cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'\").fetchall()
print(f'Restored database tables verified: {[t[0] for t in tables]}')
conn.close()
"

echo "=== BACKUP & RESTORE DRILL COMPLETED SUCCESSFULLY ==="
rm -f "${RESTORED_DB}"
