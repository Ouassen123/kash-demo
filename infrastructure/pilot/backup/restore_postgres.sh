#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./restore_postgres.sh school-a ./backups/school-a/file.dump
#   ./restore_postgres.sh school-b ./backups/school-b/file.dump

SCHOOL_ID=${1:-}
BACKUP_FILE=${2:-}

if [[ -z "$SCHOOL_ID" || -z "$BACKUP_FILE" ]]; then
  echo "Usage: $0 <school-a|school-b> <backup-file>"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

if [[ "$SCHOOL_ID" == "school-a" ]]; then
  CONTAINER="kash-school-a-postgres"
  DB_NAME=${SCHOOL_A_DB_NAME:-kash_school_a}
  DB_USER=${SCHOOL_A_DB_USER:-kash_school_a_user}
elif [[ "$SCHOOL_ID" == "school-b" ]]; then
  CONTAINER="kash-school-b-postgres"
  DB_NAME=${SCHOOL_B_DB_NAME:-kash_school_b}
  DB_USER=${SCHOOL_B_DB_USER:-kash_school_b_user}
else
  echo "Invalid school id: $SCHOOL_ID"
  exit 1
fi

echo "Restoring backup for ${SCHOOL_ID} from ${BACKUP_FILE}"
cat "$BACKUP_FILE" | docker exec -i "$CONTAINER" pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists

echo "Restore completed"
