import re

from fastapi import APIRouter, Depends

from app.services import analytics
from app.services.es_client import get_es_client

router = APIRouter()


def display_name(identifier: str) -> str:
    value = re.sub(r"^TFT\d+_", "", identifier)
    value = re.sub(r"^TFT_", "", value)
    value = re.sub(r"^Item_", "", value)
    value = value.replace("_", " ")
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", value).strip()


@router.get("")
async def get_catalog(es=Depends(get_es_client)):
    champions, _ = await analytics.get_all_champions(es, limit=200, min_games=0)
    items, _ = await analytics.get_all_items(es, limit=500, min_games=0)
    return {
        "champions": [
            {"id": row["champion_id"], "display_name": display_name(row["champion_id"])}
            for row in champions
        ],
        "items": [
            {"id": row["item_name"], "display_name": display_name(row["item_name"])}
            for row in items
        ],
    }
