.PHONY: up down logs health init-es init-metadata etl setup down-v

up:
	docker compose up -d --build

down:
	docker compose down

down-v:
	docker compose down -v

logs:
	docker compose logs -f --tail=100

health:
	@echo "=== Elasticsearch ==="
	@curl -sf http://localhost:9200/_cluster/health?pretty || echo "DOWN"
	@echo "\n=== Backend API ==="
	@curl -sf http://localhost:8000/health/health || echo "DOWN"
	@echo "\n=== Frontend ==="
	@curl -sf -o /dev/null -w "HTTP %{http_code}" http://localhost:80 || echo "DOWN"
	@echo "\n=== Airflow ==="
	@curl -sf http://localhost:8080/health || echo "DOWN"
	@echo ""

init-es:
	docker compose run --rm -v $(CURDIR)/etl:/app/etl backend python etl/scripts/init_es.py --host elasticsearch

init-metadata:
	docker compose run --rm airflow-init

etl:
	docker compose exec airflow-webserver airflow dags trigger tft_analytics_etl

setup:
	@echo "=== First-time setup ==="
	@echo "1. Checking .env file..."
	@test -f .env || (echo "ERROR: .env file not found. Copy from .env.example and configure." && exit 1)
	@echo "2. Starting infrastructure services..."
	docker compose up -d --build elasticsearch redis postgres minio minio-init
	@echo "3. Waiting for Elasticsearch..."
	@sleep 10
	@echo "4. Initializing Elasticsearch indices..."
	docker compose run --rm -v $(CURDIR)/etl:/app/etl backend python etl/scripts/init_es.py --host elasticsearch
	@echo "5. Starting remaining services..."
	docker compose run --rm airflow-init
	docker compose up -d --build
	@echo "6. Waiting for Airflow..."
	@sleep 15
	@echo "7. Unpausing ETL DAG..."
	docker compose exec airflow-webserver airflow dags unpause tft_analytics_etl || true
	@echo "\n=== Setup complete ==="
	@echo "Frontend:  http://localhost:80"
	@echo "Backend:   http://localhost:8000"
	@echo "Airflow:   http://localhost:8080"
	@echo "MinIO:     http://localhost:9001"
