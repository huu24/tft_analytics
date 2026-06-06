from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.services.es_client import get_es_client
from app.services import analytics
from app.models.champions import (
    ChampionDetail,
    ChampionItemCombo,
    ChampionTraitCombo,
    ChampionListResponse,
)

router = APIRouter()


@router.get("", response_model=ChampionListResponse)
async def list_champions(
    sort_by: str = Query("total_games", description="Sort field"),
    limit: int = Query(100, ge=1, le=200, description="Number of results"),
    min_games: int = Query(10, ge=0, description="Minimum sample size"),
    es=Depends(get_es_client),
):
    items, total = await analytics.get_all_champions(es, sort_by, limit, min_games)
    return ChampionListResponse(items=items, total=total)


@router.get("/{champion_id}", response_model=ChampionDetail)
async def get_champion(
    champion_id: str,
    es=Depends(get_es_client),
):
    data = await analytics.get_champion_detail(es, champion_id)
    if not data:
        raise HTTPException(status_code=404, detail="Champion not found")
    return data


@router.get("/{champion_id}/items", response_model=List[ChampionItemCombo])
async def get_champion_items(
    champion_id: str,
    es=Depends(get_es_client),
):
    return await analytics.get_champion_items(es, champion_id)


@router.get("/{champion_id}/traits", response_model=List[ChampionTraitCombo])
async def get_champion_traits(
    champion_id: str,
    es=Depends(get_es_client),
):
    return await analytics.get_champion_traits(es, champion_id)
