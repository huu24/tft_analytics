#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ ! -f .env ]; then
  echo "ERROR: .env file not found."
  echo "Review .env and configure credentials/keys before re-running."
  exit 1
fi

if ! command -v docker &> /dev/null; then
  echo "ERROR: docker is not installed."
  exit 1
fi

if ! docker compose version &> /dev/null; then
  echo "ERROR: docker compose is not installed."
  exit 1
fi

echo "Starting infrastructure (Elasticsearch, Redis, Postgres, MinIO)..."
docker compose up -d elasticsearch redis postgres minio minio-init

echo "Waiting for Elasticsearch to be ready..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "Elasticsearch is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "ERROR: Elasticsearch did not start within 60 seconds."
    exit 1
  fi
  sleep 2
done

echo "Initializing Elasticsearch indices..."
docker compose run --rm -v "$PROJECT_DIR/etl:/app/etl" backend python etl/scripts/init_es.py --host elasticsearch

echo "Initializing Airflow and ETL metadata..."
docker compose run --rm airflow-init

echo "Starting all services..."
docker compose up -d --build

echo "Waiting for Airflow to initialize..."
sleep 15
docker compose exec airflow-webserver airflow dags unpause tft_analytics_etl 2>/dev/null || true

echo ""
echo "=== TFT Analytics is running ==="
echo "Frontend:    http://localhost:80"
echo "Backend API: http://localhost:8000"
echo "Airflow:     http://localhost:8080 (admin/admin)"
echo "MinIO:       http://localhost:9001 (admin/password123)"
echo ""
echo "Useful commands:"
echo "  make logs    - Tail all service logs"
echo "  make health  - Check health of all services"
echo "  make down    - Stop all services"
