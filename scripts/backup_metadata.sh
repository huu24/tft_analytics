#!/usr/bin/env bash
set -euo pipefail

mkdir -p backups
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker exec tft-postgres pg_dump \
  -U "${POSTGRES_USER:-airflow}" \
  -d "${POSTGRES_DB:-airflow}" \
  --table=etl_runs \
  --table=processed_raw_objects \
  --table=processed_silver_objects \
  --table=data_versions \
  --table=data_quality_runs \
  --table=pipeline_state \
  --table=crawler_players \
  --table=crawler_matches \
  > "backups/tft_metadata_${timestamp}.sql"
echo "Metadata backup written to backups/tft_metadata_${timestamp}.sql"
