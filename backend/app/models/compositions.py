from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CompTrait(BaseModel):
    name: str
    tier_current: int


class CompSummary(BaseModel):
    comp_signature: str
    traits: List[CompTrait] = []
    core_units: List[str] = []
    total_games: int
    wins: int
    top4_count: int
    avg_placement: float
    win_rate: float
    top4_rate: float
    last_updated: Optional[datetime] = None


class CompDetail(CompSummary):
    pass


class CompListResponse(BaseModel):
    items: List[CompSummary]
    total: int
    limit: int
    offset: int
