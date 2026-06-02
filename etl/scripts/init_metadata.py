import os

import psycopg2


def connect():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "airflow"),
        user=os.environ.get("POSTGRES_USER", "airflow"),
        password=os.environ.get("POSTGRES_PASSWORD", "airflow"),
    )


def init_metadata():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS etl_runs (
                    run_id UUID PRIMARY KEY,
                    started_at TIMESTAMPTZ NOT NULL,
                    finished_at TIMESTAMPTZ,
                    status VARCHAR(32) NOT NULL,
                    raw_object_count INTEGER NOT NULL DEFAULT 0,
                    new_object_count INTEGER NOT NULL DEFAULT 0,
                    data_version VARCHAR(64),
                    error_message TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS processed_raw_objects (
                    object_name TEXT PRIMARY KEY,
                    etag TEXT,
                    size BIGINT NOT NULL,
                    processed_at TIMESTAMPTZ NOT NULL,
                    data_version VARCHAR(64) NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS data_versions (
                    data_version VARCHAR(64) PRIMARY KEY,
                    published_at TIMESTAMPTZ NOT NULL,
                    raw_object_count INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crawler_players (
                    puuid TEXT PRIMARY KEY,
                    region VARCHAR(16),
                    tier VARCHAR(32),
                    last_crawled_at TIMESTAMPTZ,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crawler_matches (
                    match_id TEXT PRIMARY KEY,
                    object_name TEXT NOT NULL,
                    crawled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_metadata()
    print("ETL metadata tables are ready.")
