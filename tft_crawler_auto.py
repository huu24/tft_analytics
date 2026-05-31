import requests
import json
import time
import os
import io
from minio import Minio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RateLimiter:
    def __init__(self):
        self.requests = []
        self.per_second_limit = 20
        self.per_two_minute_limit = 100

    def pause_champ(self):
        current_time = time.time()

        # Remove timestamps older than 2 minutes
        self.requests = [
            req_time for req_time in self.requests if current_time - req_time < 120
        ]

        # Ensure the list is sorted in ascending order of timestamps
        self.requests.sort()

        while self.requests and len(self.requests) >= self.per_two_minute_limit:
            # Calculate sleep time to wait until just after the oldest request in the 2-minute window expires
            oldest_request = self.requests[0]
            sleep_time = (
                max(120 - (current_time - oldest_request), 0) + 0.1
            )  # Ensure sleep_time is non-negative
            print(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
            current_time = time.time()
            self.requests = [
                req_time for req_time in self.requests if current_time - req_time < 120
            ]

        if self.requests and len(self.requests) >= self.per_second_limit:
            # Calculate sleep time to wait until just after the 20th last request is older than 1 second
            twentieth_last_request = self.requests[-self.per_second_limit]
            sleep_time = (
                max(1 - (current_time - twentieth_last_request), 0) + 0.1
            )  # Ensure sleep_time is non-negative
            print(f"Approaching per-second limit. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)

        # Record the new request time after any necessary sleep
        self.requests.append(time.time())


def save_state_to_file(data, filename):
    """Saves data to a file."""
    try:
        with open(filename, "w") as f:
            json.dump(list(data), f, indent=4)
        print(f"Data saved to {filename}.")
    except Exception as e:
        print(f"Failed to save state to {filename}: {e}")


def load_state_from_file(filename):
    """Loads data from a file, returning a list of dictionaries. If the file doesn't exist or is corrupt, returns an empty list."""
    try:
        with open(filename, "r") as f:
            try:
                data = json.load(f)  # Attempt to load existing data
                if not isinstance(data, list):
                    print("Warning: Data is not a list, resetting file with an empty list.")
                    return []
                return data
            except json.JSONDecodeError:
                print("Warning: Corrupt JSON data in file, resetting to an empty list.")
                return []
    except FileNotFoundError:
        print(f"No file {filename} found, returning an empty list.")
        return []


def get_challenger(api_key, rate_limiter):
    api_url = "https://vn2.api.riotgames.com/tft/league/v1/challenger"
    headers = {"X-Riot-Token": api_key}
    params = {"queue": "RANKED_TFT"}

    try:
        rate_limiter.pause_champ()
        response = requests.get(api_url, headers=headers, params=params)

        if response.status_code == 200:
            print("✅ get_challenger: 200 OK")
            data = response.json()
            return [entry["puuid"] for entry in data.get("entries", []) if "puuid" in entry]
        else:
            print(f"❌ Get challenger failed: HTTP {response.status_code}, using plebs fallback")
            return [
                "CNUsnK5k3_ccSGu_4ItDGg8fvf4n2AK1rzraXFiexHwtxAHvx4AtO9OfNb6yrnAxOxBtlMfPjjFrIQ",
                "QIEDs9rvEcGCUbB0YQj5rtuZrEW2_4lKVDX5aHHwzW380N7W6YLkihZdFSFePxDYvqbuh5CzJBJ25Q"
            ]
    except Exception as e:
        print(f"❌ Exception occurred while getting challenger data: {e}")
        return []


def get_riot_id_by_puuid(puuid, api_key, rate_limiter):
    """Lấy Riot ID dạng Name#Tag"""
    try:
        rate_limiter.pause_champ()
        api_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
        headers = {"X-Riot-Token": api_key}
        
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('gameName')}#{data.get('tagLine')}"
        else:
            print(f"Không lấy được Riot ID cho {puuid[:10]}...: HTTP {response.status_code}")
            return "Unknown#VN2"
    except Exception as e:
        print(f"Lỗi khi lấy Riot ID: {e}")
        return "Unknown#VN2"


def process_challenger_summoners(api_key, rate_limiter):
    challenger_puuids = get_challenger(api_key, rate_limiter)
    puuids_state = load_state_from_file("puuids.json")
    
    has_changes = False
    
    for puuid in challenger_puuids:
        if puuid and not any(d["puuid"] == puuid for d in puuids_state):
            riot_id = get_riot_id_by_puuid(puuid, api_key, rate_limiter)
            print(f"➕ Thêm người chơi mới: {riot_id}")
            puuids_state.append(
                {
                    "puuid": puuid,
                    "name": riot_id,
                    "has_been_seen": False,
                    "match_ids": [],
                }
            )
            has_changes = True

    if has_changes:
        save_state_to_file(puuids_state, "puuids.json")
        print("💾 Đã cập nhật danh sách puuids.json thành công!")
    return puuids_state


def get_match_ids(puuid, api_key, rate_limiter):
    try:
        rate_limiter.pause_champ()
        api_url = f"https://sea.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
        params = {"count": 100}
        headers = {"X-Riot-Token": api_key}

        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get match IDs for {puuid[:10]}: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception occurred while getting match IDs: {e}")
        return []


def get_match_data(match_id, api_key, rate_limiter):
    try:
        rate_limiter.pause_champ()
        api_url = f"https://sea.api.riotgames.com/tft/match/v1/matches/{match_id}"
        headers = {"X-Riot-Token": api_key}

        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            print(f"   [OK] Đã tải trận: {match_id}")
            return response.json()
        else:
            print(f"Failed to get match data for {match_id}: HTTP {response.status_code}")
            return {}
    except Exception as e:
        print(f"Exception occurred while getting match data for {match_id}: {e}")
        return {}


def upload_to_minio(minio_client, bucket_name, match_id, match_detail):
    """Đẩy trực tiếp file JSON của trận đấu lên MinIO Data Lake"""
    try:
        match_bytes = json.dumps(match_detail).encode('utf-8')
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=f"tft-raw/{match_id}.json",
            data=io.BytesIO(match_bytes),
            length=len(match_bytes),
            content_type="application/json"
        )
        print(f"   ☁️ [MinIO] Đã upload trận {match_id} lên bucket {bucket_name}")
    except Exception as e:
        print(f"❌ Lỗi khi upload trận {match_id} lên MinIO: {e}")


def process_match_data(api_key, rate_limiter, puuids, minio_client, bucket_name):
    match_data = load_state_from_file("match_data.json")

    # Tạo một set chứa tất cả các Match ID đã từng tải thành công để chống trùng toàn cục
    global_processed_matches = set()
    for match in match_data:
        if "metadata" in match and "match_id" in match["metadata"]:
            global_processed_matches.add(match["metadata"]["match_id"])

    # Kiểm tra các match ID đã có trên MinIO (nếu có thể)
    try:
        objects = minio_client.list_objects(bucket_name, prefix="tft-raw/", recursive=True)
        for obj in objects:
            m_id = obj.object_name.replace("tft-raw/", "").replace(".json", "")
            global_processed_matches.add(m_id)
    except Exception as e:
        print(f"Lưu ý: Không thể list file trên MinIO để kiểm tra trùng: {e}")

    for puuid_entry in puuids:
        if not puuid_entry.get("has_been_seen", False):
            puuid = puuid_entry["puuid"]
            player_name = puuid_entry.get("name", puuid[:10])

            print(f"🔍 Đang quét lịch sử của người chơi: {player_name}")
            match_ids = get_match_ids(puuid, api_key, rate_limiter)

            has_new_data = False

            for match_id in match_ids:
                if (
                    match_id not in puuid_entry["match_ids"]
                    and match_id not in global_processed_matches
                ):
                    match_detail = get_match_data(match_id, api_key, rate_limiter)

                    if match_detail and "metadata" in match_detail:
                        match_data.append(match_detail)
                        global_processed_matches.add(match_id)
                        has_new_data = True
                        
                        # TỰ ĐỘNG: Upload file JSON lên MinIO Data Lake
                        upload_to_minio(minio_client, bucket_name, match_id, match_detail)

                    puuid_entry["match_ids"].append(match_id)

            # Đánh dấu đã quét xong người chơi này
            puuid_entry["has_been_seen"] = True

            # Lưu checkpoint định kỳ
            if has_new_data:
                save_state_to_file(match_data, "match_data.json")
            save_state_to_file(puuids, "puuids.json")
            print(f"💾 Đã lưu checkpoint cho người chơi: {player_name}")

    save_state_to_file(puuids, "puuids.json")
    save_state_to_file(match_data, "match_data.json")


def load_api_key():
    # Thử lấy từ biến môi trường (Docker style) trước, sau đó fallback ra file txt
    api_key = os.getenv("API_KEY")
    if api_key and api_key != "RGAPI-4868ef9b-3b1a-4013-b3c2-42f7f804e260":
        return api_key.strip()
    
    try:
        with open("api_key.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "RGAPI-4868ef9b-3b1a-4013-b3c2-42f7f804e260"


def get_minio_client():
    endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    # Loại bỏ http:// hoặc https:// để thư viện Minio kết nối chuẩn
    endpoint_clean = endpoint.replace("http://", "").replace("https://", "")
    access_key = os.getenv("MINIO_ACCESS_KEY", "admin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "password123")
    
    print(f"☁️ Đang kết nối tới MinIO tại: {endpoint_clean}")
    return Minio(
        endpoint_clean,
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )


def main():
    api_key = load_api_key()
    if not api_key or api_key == "RGAPI-YOUR-KEY-HERE":
        print("⚠️ API Key chưa được cấu hình. Vui lòng cập nhật API_KEY trong .env hoặc api_key.txt!")
        return

    rate_limiter = RateLimiter()
    minio_client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET", "lakehouse-bucket")

    # Đảm bảo bucket tồn tại
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"📁 Tạo thành công bucket: {bucket_name}")
    except Exception as e:
        print(f"Lỗi kết nối hoặc tạo bucket MinIO: {e}")

    print("🚀 Bắt đầu chu trình tự động quét Challenger...")
    puuids = process_challenger_summoners(api_key, rate_limiter)
    
    print("🚀 Bắt đầu tải và đồng bộ match details lên MinIO...")
    process_match_data(api_key, rate_limiter, puuids, minio_client, bucket_name)
    print("✅ Chu trình crawl và đồng bộ hoàn thành.")


if __name__ == "__main__":
    # Vòng lặp chạy tự động vô hạn (mỗi 10 phút quét lại 1 lần)
    while True:
        try:
            main()
        except Exception as e:
            print(f"❌ Lỗi trong luồng chính: {e}")
        
        sleep_minutes = 10
        print(f"⏳ Đang chờ {sleep_minutes} phút trước khi bắt đầu chu kỳ quét tiếp theo...")
        time.sleep(sleep_minutes * 60)
