from fastapi import APIRouter, Depends
from app.services.es_client import get_es_client

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check(es = Depends(get_es_client)):
    try:
        await es.ping()
        return {"status": "ready", "elasticsearch": "connected"}
    except Exception:
        return {"status": "not_ready", "elasticsearch": "disconnected"}
