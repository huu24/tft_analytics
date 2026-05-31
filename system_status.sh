#!/bin/bash

echo "🔍 TFT Analytics System Status"
echo "=============================="
echo ""

echo "📦 Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep tft | sed 's/^/   /'
echo ""

echo "📊 Elasticsearch Data:"
echo "   Player stats: $(curl -s http://localhost:9200/player_stats/_count 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo 'N/A')"
echo "   Champion stats: $(curl -s http://localhost:9200/champion_stats/_count 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo 'N/A')"
echo "   Item stats: $(curl -s http://localhost:9200/item_stats/_count 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo 'N/A')"
echo ""

echo "🕷️  Crawler Progress:"
python3 -c "
from minio import Minio
client = Minio('localhost:9000', access_key='admin', secret_key='password123', secure=False)
objects = list(client.list_objects('lakehouse-bucket', prefix='tft-raw/', recursive=True))
print(f'   Matches crawled: {len(objects)}')
" 2>/dev/null || echo "   MinIO connection failed"
echo ""

echo "🔗 API Endpoints:"
echo "   Root: $(curl -s http://localhost:8000/ 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('message', 'N/A'))" 2>/dev/null || echo 'N/A')"
echo "   Health: $(curl -s http://localhost:8000/health/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'N/A'))" 2>/dev/null || echo 'N/A')"
echo ""

echo "🌐 Frontend:"
echo "   URL: http://localhost:5173"
echo "   Status: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:5173 2>/dev/null || echo 'N/A')"
echo ""

echo "📝 Commands:"
echo "   ./check_crawler.sh        # Check crawler progress"
echo "   tail -f massive_crawl.log # Real-time crawler logs"
echo "   ./system_status.sh        # Run this check again"
