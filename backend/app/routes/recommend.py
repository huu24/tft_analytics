from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services import recommender

router = APIRouter()


class RecommendRequest(BaseModel):
    champion_ids: list[str]
    item_names: Optional[list[str]] = None


class RecommendItem(BaseModel):
    champion_id: str
    display_name: str
    confidence: float


class RecommendResponse(BaseModel):
    recommendations: list[RecommendItem]
    model_version: str


@router.post("", response_model=RecommendResponse)
async def get_recommendations(req: RecommendRequest):
    if not req.champion_ids:
        raise HTTPException(status_code=400, detail="champion_ids is required")

    if not recommender.is_model_loaded():
        raise HTTPException(status_code=503, detail="ML model not loaded")

    results = recommender.predict(req.champion_ids, req.item_names)
    return RecommendResponse(recommendations=results, model_version="v1")
