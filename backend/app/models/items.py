from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ItemSummary(BaseModel):
    item_name: str
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    most_common_champion: Optional[str] = None
    last_updated: Optional[datetime] = None


class ItemDetail(ItemSummary):
    pass


class ItemChampionCombo(BaseModel):
    champion_id: str
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float


class ItemListResponse(BaseModel):
    items: List[ItemSummary]
    total: int
