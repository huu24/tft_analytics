#!/bin/bash

echo "🔄 Auto-restart crawler script"
echo "⚠️  Bạn cần regenerate API key mỗi 24 giờ"
echo ""

while true; do
    echo "🚀 Starting crawler at $(date)"
    python3 -u tft_crawler_massive.py 2>&1 | tee -a massive_crawl.log
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Crawler completed successfully!"
        break
    fi
    
    echo "❌ Crawler exited with code $EXIT_CODE"
    echo ""
    echo "⏰ Waiting 23 hours before restart..."
    echo "📝 Trong thời gian này, hãy:"
    echo "   1. Vào https://developer.riotgames.com/"
    echo "   2. Click 'Regenerate API Key'"
    echo "   3. Update .env với key mới"
    echo ""
    
    sleep 82800  # 23 hours
done
