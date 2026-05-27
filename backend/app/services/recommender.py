import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ml_available = False
_recommend_fn = None


def _init_ml():
    global _ml_available, _recommend_fn
    if _recommend_fn is not None:
        return

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    ml_path = project_root / "ml"
    if ml_path.exists() and str(ml_path.parent) not in sys.path:
        sys.path.insert(0, str(ml_path.parent))

    try:
        from ml.predict import recommend, _load_model
        _load_model()
        _recommend_fn = recommend
        _ml_available = True
        logger.info("ML model loaded successfully")
    except Exception as e:
        logger.warning(f"ML model not available: {e}")
        _ml_available = False


def is_model_loaded() -> bool:
    _init_ml()
    return _ml_available


def predict(
    champion_ids: list[str],
    item_names: Optional[list[str]] = None,
    top_k: int = 5,
) -> list[dict]:
    _init_ml()
    if not _ml_available or _recommend_fn is None:
        return []
    return _recommend_fn(champion_ids, item_names, top_k)
