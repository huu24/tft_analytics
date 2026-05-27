from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChampionSummary(BaseModel):
    champion_id: str
    display_name: Optional[str] = None
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float
    top4_rate: float
    pick_rate: float
    last_updated: Optional[datetime] = None


class ChampionDetail(ChampionSummary):
    pass


class ChampionItemCombo(BaseModel):
    item_name: str
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float


class ChampionTraitCombo(BaseModel):
    trait_name: str
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float


class ChampionListResponse(BaseModel):
    items: List[ChampionSummary]
    total: int
