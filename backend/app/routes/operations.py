from datetime import datetime, timezone

import psycopg2
from fastapi import APIRouter, Response

from app.config import settings

router = APIRouter()


def connect():
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )


def load_status():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT data_version, raw_object_count, published_at
                FROM data_versions
                WHERE is_active = TRUE
                ORDER BY published_at DESC
                LIMIT 1
                """
            )
            active = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM processed_silver_objects")
            silver_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM processed_raw_objects")
            published_count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT run_id, started_at, finished_at, status, raw_object_count,
                       new_object_count, data_version
                FROM etl_runs
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
            latest_run = cur.fetchone()
            cur.execute(
                """
                SELECT raw_match_count, participant_count, valid_participant_count,
                       rejected_participant_count, duplicate_participant_count
                FROM data_quality_runs
                ORDER BY checked_at DESC
                LIMIT 1
                """
            )
            quality = cur.fetchone()
        now = datetime.now(timezone.utc)
        published_at = active[2] if active else None
        return {
            "data_version": active[0] if active else None,
            "raw_object_count": active[1] if active else 0,
            "published_at": published_at.isoformat() if published_at else None,
            "snapshot_age_seconds": int((now - published_at).total_seconds()) if published_at else -1,
            "silver_object_count": silver_count,
            "published_object_count": published_count,
            "latest_run": {
                "run_id": str(latest_run[0]),
                "started_at": latest_run[1].isoformat(),
                "finished_at": latest_run[2].isoformat() if latest_run[2] else None,
                "status": latest_run[3],
                "raw_object_count": latest_run[4],
                "new_object_count": latest_run[5],
                "data_version": latest_run[6],
                "duration_seconds": int(((latest_run[2] or now) - latest_run[1]).total_seconds()),
            } if latest_run else None,
            "quality": {
                "raw_match_count": quality[0],
                "participant_count": quality[1],
                "valid_participant_count": quality[2],
                "rejected_participant_count": quality[3],
                "duplicate_participant_count": quality[4],
            } if quality else None,
        }
    finally:
        conn.close()


@router.get("/status")
async def status():
    return load_status()


def metric_line(name, value, labels=None):
    if not labels:
        return f"# TYPE {name} gauge\n{name} {value}"
    label_text = ",".join(f'{key}="{str(val)}"' for key, val in labels.items())
    return f"# TYPE {name} gauge\n{name}{{{label_text}}} {value}"


@router.get("/metrics", include_in_schema=False)
async def metrics():
    current = load_status()
    quality = current["quality"] or {}
    latest_run = current["latest_run"] or {}
    raw_seen = latest_run.get("raw_object_count", current["raw_object_count"])
    silver_count = current["silver_object_count"]
    published_count = current["published_object_count"]
    total_participants = quality.get("participant_count", 0)
    valid_participants = quality.get("valid_participant_count", 0)
    values = {
        "tft_snapshot_age_seconds": current["snapshot_age_seconds"],
        "tft_raw_objects_seen": raw_seen,
        "tft_silver_objects_processed": silver_count,
        "tft_raw_objects_published": published_count,
        "tft_raw_to_silver_backlog": max(raw_seen - silver_count, 0),
        "tft_silver_to_gold_backlog": max(silver_count - published_count, 0),
        "tft_etl_latest_duration_seconds": latest_run.get("duration_seconds", 0),
        "tft_etl_latest_new_objects": latest_run.get("new_object_count", 0),
        "tft_quality_participants_total": total_participants,
        "tft_quality_participants_valid": valid_participants,
        "tft_quality_participants_rejected": quality.get("rejected_participant_count", 0),
        "tft_quality_participants_duplicates": quality.get("duplicate_participant_count", 0),
        "tft_quality_valid_participant_ratio": valid_participants / total_participants if total_participants else 0,
    }
    lines = [metric_line(name, value) for name, value in values.items()]
    lines.append(metric_line("tft_active_snapshot_info", 1, {
        "version": current["data_version"] or "none",
    }))
    lines.append(metric_line("tft_etl_latest_status", 1, {
        "status": latest_run.get("status", "none"),
        "version": latest_run.get("data_version") or "none",
    }))
    body = "\n".join(lines) + "\n"
    return Response(content=body, media_type="text/plain; version=0.0.4")
