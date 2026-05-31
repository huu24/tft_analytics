import requests
import json
import time
import os
import io
from minio import Minio
from dotenv import load_dotenv
from collections import defaultdict
import threading
from queue import Queue

print("🚀 Starting TFT Massive Crawler...")
load_dotenv()
print("✅ Loaded .env file")

REGIONS = {
    'VN2': {'routing': 'sea', 'league_url': 'https://vn2.api.riotgames.com', 'match_url': 'https://sea.api.riotgames.com'},
    'KR': {'routing': 'asia', 'league_url': 'https://kr.api.riotgames.com', 'match_url': 'https://asia.api.riotgames.com'},
    'NA1': {'routing': 'americas', 'league_url': 'https://na1.api.riotgames.com', 'match_url': 'https://americas.api.riotgames.com'},
    'EUW1': {'routing': 'europe', 'league_url': 'https://euw1.api.riotgames.com', 'match_url': 'https://europe.api.riotgames.com'},
}

TIERS = ['challenger', 'grandmaster', 'master']
MATCHES_PER_PLAYER = 100  # Giảm từ 200 xuống 100 để tăng tốc

class RateLimiter:
    def __init__(self):
        self.requests = []
        self.lock = threading.Lock()
        self.per_second_limit = 20  # User has 20 requests/second
        self.per_two_minute_limit = 100  # User has 100 requests/2 minutes

    def wait(self):
        with self.lock:
            current_time = time.time()
            self.requests = [t for t in self.requests if current_time - t < 120]
            self.requests.sort()

            while len(self.requests) >= self.per_two_minute_limit:
                oldest = self.requests[0]
                sleep_time = max(120 - (current_time - oldest), 0) + 0.1
                print(f"⏱️  Rate limit (2min). Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                current_time = time.time()
                self.requests = [t for t in self.requests if current_time - t < 120]

            if len(self.requests) >= self.per_second_limit:
                twentieth_last = self.requests[-self.per_second_limit]
                sleep_time = max(1 - (current_time - twentieth_last), 0) + 0.1
                print(f"⏱️  Rate limit (1s). Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)

            self.requests.append(time.time())

def call_api(url, headers, rate_limiter, max_retries=3):
    for attempt in range(max_retries):
        try:
            rate_limiter.wait()
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                print(f"⚠️  Rate limited by Riot. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            elif response.status_code == 404:
                return None
            else:
                print(f"❌ API error {response.status_code}: {url}")
                return None
        except Exception as e:
            print(f"❌ Request failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None

def get_players_by_tier(region_code, region_config, tier, api_key, rate_limiter):
    url = f"{region_config['league_url']}/tft/league/v1/{tier}"
    headers = {"X-Riot-Token": api_key}
    
    data = call_api(url, headers, rate_limiter)
    if not data:
        print(f"❌ Failed to get {tier} for {region_code}")
        return []
    
    entries = data.get('entries', [])
    print(f"✅ {region_code} {tier}: {len(entries)} players")
    return [e['puuid'] for e in entries if 'puuid' in e]

def get_match_ids(puuid, region_config, api_key, rate_limiter):
    url = f"{region_config['match_url']}/tft/match/v1/matches/by-puuid/{puuid}/ids?count={MATCHES_PER_PLAYER}"
    headers = {"X-Riot-Token": api_key}
    
    data = call_api(url, headers, rate_limiter)
    return data if data else []

def get_match_data(match_id, region_config, api_key, rate_limiter):
    url = f"{region_config['match_url']}/tft/match/v1/matches/{match_id}"
    headers = {"X-Riot-Token": api_key}
    
    return call_api(url, headers, rate_limiter)

def upload_to_minio(minio_client, bucket, match_id, match_data):
    try:
        match_bytes = json.dumps(match_data).encode('utf-8')
        minio_client.put_object(
            bucket_name=bucket,
            object_name=f"tft-raw/{match_id}.json",
            data=io.BytesIO(match_bytes),
            length=len(match_bytes),
            content_type="application/json"
        )
        print(f"  ☁️  Uploaded {match_id}")
        return True
    except Exception as e:
        print(f"  ❌ MinIO upload failed for {match_id}: {e}")
        return False

def save_progress(progress_file, processed_matches, processed_players):
    with open(progress_file, 'w') as f:
        json.dump({
            'processed_matches': list(processed_matches),
            'processed_players': list(processed_players),
            'timestamp': time.time()
        }, f)

def load_progress(progress_file):
    try:
        with open(progress_file, 'r') as f:
            data = json.load(f)
            return set(data.get('processed_matches', [])), set(data.get('processed_players', []))
    except:
        return set(), set()

def main():
    print("🔧 Entering main function...")
    api_key = os.getenv('API_KEY')
    print(f"🔑 API Key loaded: {api_key[:20]}...")
    if not api_key:
        print("❌ API_KEY not found in .env")
        return

    print("🔌 Connecting to MinIO...")
    minio_client = Minio('localhost:9000', access_key='admin', secret_key='password123', secure=False)
    bucket = 'lakehouse-bucket'
    
    print("📦 Checking bucket...")
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)
    print("✅ MinIO ready")

    rate_limiter = RateLimiter()
    progress_file = 'massive_crawl_progress.json'
    processed_matches, processed_players = load_progress(progress_file)
    
    print(f"📊 Resume: {len(processed_matches)} matches, {len(processed_players)} players already processed")

    all_puuids = []
    for region_code, region_config in REGIONS.items():
        print(f"\n🌍 Fetching players from {region_code}...")
        for tier in TIERS:
            puuids = get_players_by_tier(region_code, region_config, tier, api_key, rate_limiter)
            for puuid in puuids:
                all_puuids.append({
                    'puuid': puuid,
                    'region': region_code,
                    'tier': tier
                })
    
    print(f"\n📊 Total players to crawl: {len(all_puuids)}")
    
    stats = {
        'matches_crawled': len(processed_matches),
        'players_processed': len(processed_players),
        'upload_success': 0,
        'upload_failed': 0,
        'start_time': time.time()
    }

    for idx, player_info in enumerate(all_puuids, 1):
        puuid = player_info['puuid']
        region = player_info['region']
        region_config = REGIONS[region]
        
        if puuid in processed_players:
            continue

        print(f"\n[{idx}/{len(all_puuids)}] {region}/{player_info['tier']}: {puuid[:20]}...")
        
        match_ids = get_match_ids(puuid, region_config, api_key, rate_limiter)
        print(f"  📋 Found {len(match_ids)} matches")
        
        new_matches = 0
        for match_id in match_ids:
            if match_id in processed_matches:
                continue
            
            match_data = get_match_data(match_id, region_config, api_key, rate_limiter)
            if not match_data:
                continue
            
            if upload_to_minio(minio_client, bucket, match_id, match_data):
                stats['upload_success'] += 1
                new_matches += 1
                processed_matches.add(match_id)
            else:
                stats['upload_failed'] += 1
        
        processed_players.add(puuid)
        stats['players_processed'] += 1
        stats['matches_crawled'] += new_matches
        
        if idx % 10 == 0:
            save_progress(progress_file, processed_matches, processed_players)
            elapsed = time.time() - stats['start_time']
            rate = stats['matches_crawled'] / elapsed if elapsed > 0 else 0
            print(f"\n📈 Progress: {stats['matches_crawled']} matches, {stats['players_processed']} players")
            print(f"⚡ Rate: {rate:.1f} matches/sec | ✅ {stats['upload_success']} uploaded | ❌ {stats['upload_failed']} failed")

    save_progress(progress_file, processed_matches, processed_players)
    
    elapsed = time.time() - stats['start_time']
    print(f"\n✅ Crawl complete!")
    print(f"📊 Total matches: {stats['matches_crawled']}")
    print(f"👥 Total players: {stats['players_processed']}")
    print(f"⏱️  Time: {elapsed/3600:.1f} hours")
    print(f"☁️  MinIO: {stats['upload_success']} uploaded, {stats['upload_failed']} failed")

if __name__ == "__main__":
    main()
