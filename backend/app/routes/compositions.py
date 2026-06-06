from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.es_client import get_es_client
from app.services import analytics
from app.models.compositions import CompDetail, CompListResponse

router = APIRouter()


@router.get("", response_model=CompListResponse)
async def list_compositions(
    min_games: int = Query(10, ge=1, le=10000, description="Minimum games filter"),
    sort_by: str = Query("win_rate", description="Sort field"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    es=Depends(get_es_client),
):
    items, total = await analytics.get_compositions(es, min_games, sort_by, limit, offset)
    return CompListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{comp_signature}", response_model=CompDetail)
async def get_composition(
    comp_signature: str,
    es=Depends(get_es_client),
):
    data = await analytics.get_comp_detail(es, comp_signature)
    if not data:
        raise HTTPException(status_code=404, detail="Composition not found")
    return data
