from pydantic import BaseModel
from typing import List, Optional


class BuildRecommendation(BaseModel):
    champion_id: str
    recommended_items: List[str]
    avg_placement: float
    win_rate: float
    total_games: int


class BuildResponse(BaseModel):
    recommendations: List[BuildRecommendation]


class MetaOverview(BaseModel):
    total_players: int
    total_matches_analyzed: int
    top_champions: List[dict]
    top_compositions: List[dict]
    top_items: List[dict]
