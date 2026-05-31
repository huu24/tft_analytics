#!/bin/bash

echo "🔍 TFT Massive Crawler Status"
echo "=============================="
echo ""

echo "1️⃣  Crawler Process:"
if ps aux | grep tft_crawler_massive | grep -v grep > /dev/null; then
    echo "   ✅ Running"
    ps aux | grep tft_crawler_massive | grep -v grep | awk '{print "   PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}'
else
    echo "   ❌ Not running"
fi
echo ""

echo "2️⃣  MinIO Storage:"
python3 -c "
from minio import Minio
client = Minio('localhost:9000', access_key='admin', secret_key='password123', secure=False)
objects = list(client.list_objects('lakehouse-bucket', prefix='tft-raw/', recursive=True))
total_size = sum(obj.size for obj in objects)
print(f'   ☁️  Matches: {len(objects)}')
print(f'   📊 Size: {total_size / 1024 / 1024:.1f} MB')
" 2>&1
echo ""

echo "3️⃣  Progress File:"
if [ -f massive_crawl_progress.json ]; then
    python3 -c "
import json
with open('massive_crawl_progress.json') as f:
    data = json.load(f)
print(f'   👥 Players processed: {len(data.get(\"processed_players\", []))}')
print(f'   🎮 Matches processed: {len(data.get(\"processed_matches\", []))}')
" 2>&1
else
    echo "   ⚠️  No progress file yet (saves every 10 players)"
fi
echo ""

echo "4️⃣  Recent Activity (last 10 uploads):"
tail -50 massive_crawl.log | grep "Uploaded" | tail -10 | sed 's/^/   /'
echo ""

echo "5️⃣  Current Player:"
grep -E "^\[[0-9]+/[0-9]+\]" massive_crawl.log | tail -1 | sed 's/^/   /'
echo ""

echo "📝 Commands:"
echo "   tail -f massive_crawl.log          # Real-time logs"
echo "   ./check_crawler.sh                 # Run this check again"
echo "   killall python3                    # Stop crawler"
