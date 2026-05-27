from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.services.es_client import get_es_client
from app.services import analytics
from app.models.items import ItemDetail, ItemChampionCombo, ItemListResponse

router = APIRouter()


@router.get("", response_model=ItemListResponse)
async def list_items(
    sort_by: str = Query("total_games", description="Sort field"),
    limit: int = Query(100, ge=1, le=200, description="Number of results"),
    es=Depends(get_es_client),
):
    items, total = await analytics.get_all_items(es, sort_by, limit)
    return ItemListResponse(items=items, total=total)


@router.get("/{item_name}", response_model=ItemDetail)
async def get_item(
    item_name: str,
    es=Depends(get_es_client),
):
    data = await analytics.get_item_detail(es, item_name)
    if not data:
        raise HTTPException(status_code=404, detail="Item not found")
    return data


@router.get("/{item_name}/champions", response_model=List[ItemChampionCombo])
async def get_item_champions(
    item_name: str,
    es=Depends(get_es_client),
):
    return await analytics.get_item_champions(es, item_name)
