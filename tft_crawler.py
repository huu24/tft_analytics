import requests
import time
import json
from kafka import KafkaProducer

GLOBAL_DELAY = 1.3

# ==========================================
# 1. CẤU HÌNH API & KAFKA
# ==========================================
API_KEY = "RGAPI-601b9abc-ce64-4a46-8ac9-490e96c64c7a" # Điền API Key của bạn vào đây
HEADERS = {"X-Riot-Token": API_KEY}
REGION = "vn2"
ROUTING = "sea"

KAFKA_BROKER = 'localhost:9092' # Địa chỉ Kafka Broker của bạn
KAFKA_TOPIC = 'tft-raw-matches'

# Khởi tạo Kafka Producer
# value_serializer: Tự động parse dictionary của Python thành chuỗi JSON và encode dạng bytes trước khi gửi
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("✅ Đã kết nối thành công tới Kafka!")
except Exception as e:
    print(f"❌ Lỗi kết nối Kafka: {e}")
    exit(1)

# Tập hợp lưu các match_id đã xử lý để tránh crawl trùng lặp
processed_matches = set()

# ==========================================
# 2. CÁC HÀM GỌI API (CÓ XỬ LÝ RATE LIMIT)
# ==========================================
def call_api(url):
    """Hàm gọi API chung, bao gồm xử lý lỗi 429 Too Many Requests"""
    while True:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            print(f"⏳ Hit Rate Limit! Đang ngủ {retry_after} giây...")
            time.sleep(retry_after)
        else:
            print(f"⚠️ Lỗi {response.status_code} khi gọi {url}")
            return None

# ==========================================
# 3. LOGIC CRAWL CHÍNH
# ==========================================
def stream_tft_data():
    print("🚀 Bắt đầu quét TOÀN BỘ bậc Thách Đấu...")
    
    # 1. Lấy danh sách toàn bộ Thách Đấu (~300 người)
    league_url = f"https://{REGION}.api.riotgames.com/tft/league/v1/challenger"
    challengers = call_api(league_url)
    time.sleep(GLOBAL_DELAY) # Nghỉ ngơi
    
    if not challengers: return

    # BỎ GIỚI HẠN [:10] - Lấy toàn bộ danh sách
    all_players = challengers.get('entries', [])
    print(f"👥 Tìm thấy {len(all_players)} người chơi Thách Đấu.")
    
    for index, player in enumerate(all_players):
        puuid = player.get('puuid')
        if not puuid:
            continue
            
        print(f"[{index + 1}/{len(all_players)}] Đang quét dữ liệu của PUUID: {puuid[:8]}...")
        
        # 2. Lấy danh sách Match IDs (Lấy 5 trận gần nhất của mỗi người)
        match_ids_url = f"https://{ROUTING}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?count=5"
        match_ids = call_api(match_ids_url)
        time.sleep(GLOBAL_DELAY) # Nghỉ ngơi
        
        if not match_ids: continue
        
        # 3. Crawl chi tiết từng trận và ném vào Kafka
        for match_id in match_ids:
            if match_id in processed_matches:
                continue # Bỏ qua nếu đã có
                
            match_detail_url = f"https://{ROUTING}.api.riotgames.com/tft/match/v1/matches/{match_id}"
            match_data = call_api(match_detail_url)
            time.sleep(GLOBAL_DELAY) # Nghỉ ngơi để không bao giờ chạm ngưỡng 100 req/2min
            
            if match_data:
                producer.send(KAFKA_TOPIC, value=match_data)
                processed_matches.add(match_id)
                print(f"   📦 Đã đẩy trận {match_id} vào Kafka")
            
    producer.flush() 
    print(f"✅ Hoàn thành một chu kỳ cào dữ liệu lớn! Đã lưu {len(processed_matches)} trận.")


if __name__ == "__main__":
    # Chạy vòng lặp vô hạn, mỗi 15 phút quét lại một lần để tạo luồng Real-time
    while True:
        stream_tft_data()
        print("Đang chờ 20 giây trước khi quét cycle tiếp theo...")
        time.sleep(20)
