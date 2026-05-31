#!/bin/bash

echo "🔑 Update API Key"
echo "================="
echo ""

# 1. Stop crawler
echo "1️⃣  Stopping crawler..."
killall python3 2>/dev/null
sleep 2
echo "   ✅ Crawler stopped"
echo ""

# 2. Show current key
CURRENT_KEY=$(grep API_KEY .env | cut -d'=' -f2)
echo "2️⃣  Current API Key:"
echo "   ${CURRENT_KEY:0:20}..."
echo ""

# 3. Ask for new key
echo "3️⃣  Enter new API Key (paste and press Enter):"
read -r NEW_KEY

if [ -z "$NEW_KEY" ]; then
    echo "   ❌ No key provided. Aborting."
    exit 1
fi

# 4. Update .env
sed -i "s|^API_KEY=.*|API_KEY=$NEW_KEY|" .env
echo "   ✅ API key updated in .env"
echo ""

# 5. Test new key
echo "4️⃣  Testing new API key..."
TEST_RESULT=$(curl -s -H "X-Riot-Token: $NEW_KEY" "https://vn2.api.riotgames.com/tft/league/v1/challenger" | python3 -c "import sys, json; data=json.load(sys.stdin); print('OK' if 'entries' in data else 'FAIL')" 2>&1)

if [ "$TEST_RESULT" = "OK" ]; then
    echo "   ✅ API key is valid!"
else
    echo "   ❌ API key test failed. Please check the key."
    exit 1
fi
echo ""

# 6. Restart crawler
echo "5️⃣  Restarting crawler..."
nohup python3 -u tft_crawler_massive.py > massive_crawl.log 2>&1 &
CRAWLER_PID=$!
sleep 3

if ps -p $CRAWLER_PID > /dev/null; then
    echo "   ✅ Crawler restarted (PID: $CRAWLER_PID)"
    echo ""
    echo "📊 Checking progress..."
    ./check_crawler.sh
else
    echo "   ❌ Crawler failed to start. Check massive_crawl.log"
fi
