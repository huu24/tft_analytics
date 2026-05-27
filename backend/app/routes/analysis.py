from fastapi import APIRouter, Depends, Query
from typing import List
from app.services.es_client import get_es_client
from app.services import analytics
from app.models.analysis import BuildResponse, MetaOverview

router = APIRouter()


@router.get("/build", response_model=BuildResponse)
async def get_build(
    champ_ids: List[str] = Query([], description="Champion IDs to analyze"),
    item_names: List[str] = Query([], description="Item names to filter"),
    es=Depends(get_es_client),
):
    recommendations = await analytics.get_build_recommendations(es, champ_ids, item_names)
    return BuildResponse(recommendations=recommendations)


@router.get("/meta-overview", response_model=MetaOverview)
async def get_meta_overview(
    es=Depends(get_es_client),
):
    return await analytics.get_meta_overview(es)
