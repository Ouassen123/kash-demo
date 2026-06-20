#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./backup_postgres.sh school-a
#   ./backup_postgres.sh school-b

SCHOOL_ID=${1:-}
if [[ -z "$SCHOOL_ID" ]]; then
  echo "Usage: $0 <school-a|school-b>"
  exit 1
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./backups/${SCHOOL_ID}"
mkdir -p "$BACKUP_DIR"

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

BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"
echo "Creating backup for ${SCHOOL_ID} -> ${BACKUP_FILE}"

docker exec "$CONTAINER" pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_FILE"

echo "Backup completed: $BACKUP_FILE"
