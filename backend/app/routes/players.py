from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.services.es_client import get_es_client
from app.services import analytics
from app.models.players import (
    PlayerStats,
    PlayerChampionStats,
    PlayerTraitStats,
    PlayerItemStats,
    PlayerSearchResult,
)

router = APIRouter()


@router.get("/search", response_model=List[PlayerSearchResult])
async def search_players(
    name: str = Query(..., description="Riot ID or partial name to search"),
    es=Depends(get_es_client),
):
    results = await analytics.search_players(es, name)
    return results


@router.get("/{puuid}", response_model=PlayerStats)
async def get_player_profile(
    puuid: str,
    es=Depends(get_es_client),
):
    data = await analytics.get_player_stats(es, puuid)
    if not data:
        raise HTTPException(status_code=404, detail="Player not found")
    return data


@router.get("/{puuid}/champions", response_model=List[PlayerChampionStats])
async def get_player_champions(
    puuid: str,
    es=Depends(get_es_client),
):
    return await analytics.get_player_champions(es, puuid)


@router.get("/{puuid}/traits", response_model=List[PlayerTraitStats])
async def get_player_traits(
    puuid: str,
    es=Depends(get_es_client),
):
    return await analytics.get_player_traits(es, puuid)


@router.get("/{puuid}/items", response_model=List[PlayerItemStats])
async def get_player_items(
    puuid: str,
    es=Depends(get_es_client),
):
    return await analytics.get_player_items(es, puuid)
