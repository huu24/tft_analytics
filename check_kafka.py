import json
from kafka import KafkaConsumer

# Khởi tạo Consumer lắng nghe topic 'tft-raw-matches'
consumer = KafkaConsumer(
    'tft-raw-matches',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest', # Đọc từ message đầu tiên có trong topic
    value_deserializer=lambda x: json.loads(x.decode('utf-8')) # Dịch ngược từ Byte về JSON Dictionary
)

print("🎧 Đang lắng nghe dữ liệu từ Kafka...\n")

# Chỉ đọc ĐÚNG 1 TRẬN ĐẤU để phân tích, sau đó dừng lại
for message in consumer:
    match_data = message.value
    
    print("="*50)
    print(f"🔥 ĐÃ NHẬN ĐƯỢC TRẬN ĐẤU: {match_data['metadata']['match_id']}")
    print("="*50)
    
    # 1. Xem cấu trúc cấp cao nhất
    print("1. Các thành phần chính của file JSON:")
    print(list(match_data.keys())) 
    
    # 2. Xem thông tin chung của trận đấu (metadata & info)
    print("\n2. Thông tin chung của trận đấu:")
    print(f"- Phiên bản TFT: {match_data['info']['game_version']}")
    print(f"- Thời gian chơi: {round(match_data['info']['game_length'] / 60, 2)} phút")
    
    # 3. Khám phá mảng 'participants' (Chứa data của 8 người chơi - Rất quan trọng!)
    participants = match_data['info']['participants']
    print(f"\n3. Có {len(participants)} người chơi trong trận này.")
    
    # Xem thử data của NGƯỜI CHƠI ĐẦU TIÊN (Hạng 1 hoặc người bị loại đầu)
    player_1 = participants[0]
    print(f"\n🔍 Trích xuất người chơi đạt TOP {player_1['placement']}:")
    
    # Lấy danh sách các Lõi Công Nghệ (Augments)
    print(f"- Các lõi đã chọn: {player_1.get('augments', [])}")
    
    # Lấy danh sách Tướng (Units)
    print("- Đội hình (Tướng & Sao):")
    for unit in player_1['units']:
        print(f"  + {unit['character_id']} ({unit['tier']} sao)")
        
    break # Lấy 1 message là đủ hiểu, thoát vòng lặp
