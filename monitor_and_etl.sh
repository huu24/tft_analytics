#!/bin/bash

echo "🔍 Monitoring crawler process..."

# Wait for crawler to finish
while ps aux | grep -v grep | grep tft_crawler_auto > /dev/null; do
    echo "$(date '+%H:%M:%S') - Crawler still running..."
    
    # Show progress
    if [ -f match_data.json ]; then
        MATCH_COUNT=$(python3 -c "import json; print(len(json.load(open('match_data.json'))))" 2>/dev/null || echo "0")
        echo "  📊 Matches crawled: $MATCH_COUNT"
    fi
    
    # Check MinIO
    MINIO_COUNT=$(python3 -c "
from minio import Minio
client = Minio('localhost:9000', access_key='admin', secret_key='password123', secure=False)
objects = list(client.list_objects('lakehouse-bucket', prefix='tft-raw/', recursive=True))
print(len(objects))
" 2>/dev/null || echo "0")
    echo "  ☁️  MinIO objects: $MINIO_COUNT"
    
    sleep 30
done

echo ""
echo "✅ Crawler finished!"
echo ""

# Check if we have data
if [ ! -f match_data.json ]; then
    echo "❌ No match_data.json found. Crawler may have failed."
    exit 1
fi

MATCH_COUNT=$(python3 -c "import json; print(len(json.load(open('match_data.json'))))")
echo "📊 Total matches crawled: $MATCH_COUNT"

if [ "$MATCH_COUNT" -eq 0 ]; then
    echo "❌ No matches found. Check crawler.log for errors."
    exit 1
fi

echo ""
echo "🚀 Starting ETL pipeline..."
echo ""

# Start Spark services
echo "1️⃣  Starting Spark master and worker..."
docker-compose up -d spark-master spark-worker 2>&1 | tail -5

sleep 10

# Check if Spark is ready
echo "2️⃣  Checking Spark status..."
if ! curl -s http://localhost:8081/json/ | grep -q "alive"; then
    echo "❌ Spark master not ready. Check docker logs."
    exit 1
fi
echo "✅ Spark is ready"

# Run ETL
echo ""
echo "3️⃣  Running Spark ETL job..."
docker-compose exec -T spark-master spark-submit \
    --master spark://spark-master:7077 \
    --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.13.0,org.apache.hadoop:hadoop-aws:3.3.4 \
    --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
    --conf spark.hadoop.fs.s3a.access.key=admin \
    --conf spark.hadoop.fs.s3a.secret.key=password123 \
    --conf spark.hadoop.fs.s3a.path.style.access=true \
    /app/etl/spark_jobs/tft_etl.py 2>&1 | tee etl.log

echo ""
echo "4️⃣  Verifying Elasticsearch indices..."
sleep 5

for INDEX in player_stats champion_stats item_stats comp_meta champion_item_combo champion_trait_combo; do
    COUNT=$(curl -s http://localhost:9200/$INDEX/_count 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")
    echo "  📊 $INDEX: $COUNT documents"
done

echo ""
echo "✅ ETL complete!"
echo ""
echo "🌐 Access your dashboard:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo ""
