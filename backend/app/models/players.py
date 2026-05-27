from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PlayerStats(BaseModel):
    puuid: str
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float
    top4_rate: float
    meta_score: float
    flex_score: float
    item_accuracy: float
    last_updated: Optional[datetime] = None


class PlayerChampionStats(BaseModel):
    champion_id: str
    display_name: Optional[str] = None
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float
    top4_rate: float


class PlayerTraitStats(BaseModel):
    trait_name: str
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float


class PlayerItemStats(BaseModel):
    item_name: str
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float


class PlayerSearchResult(BaseModel):
    puuid: str
    total_games: int
    win_rate: float
    avg_placement: float
