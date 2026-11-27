#!/usr/bin/env bash
# Daily PostgreSQL Backup Script for LeadHarvest India
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

docker exec leadharvest_postgres pg_dump -U "${POSTGRES_USER:-leadharvest}" "${POSTGRES_DB:-leadharvest}" | gzip > "$BACKUP_DIR/leadharvest_${TIMESTAMP}.sql.gz"

# Retain last 14 days of backups
find "$BACKUP_DIR" -name "leadharvest_*.sql.gz" -mtime +14 -delete
echo "Backup saved: $BACKUP_DIR/leadharvest_${TIMESTAMP}.sql.gz"
