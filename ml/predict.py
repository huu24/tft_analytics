import sys
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.config.tft_static_data import CHAMPION_NAMES, ITEM_NAMES
from ml.model import TFTRecommender

CHECKPOINT_PATH = Path(__file__).resolve().parent / "checkpoints" / "best_model.pt"

_model = None
_champion_vocab = None
_item_vocab = None
_idx_to_champion = None


def _load_model(checkpoint_path=None):
    global _model, _champion_vocab, _item_vocab, _idx_to_champion
    if _model is not None:
        return

    path = Path(checkpoint_path) if checkpoint_path else CHECKPOINT_PATH
    if not path.exists():
        # Fallback: create untrained model with default vocab
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _champion_vocab = {c: i for i, c in enumerate(CHAMPION_NAMES.keys())}
        _item_vocab = {item: i for i, item in enumerate(ITEM_NAMES.keys())}
        _idx_to_champion = {v: k for k, v in _champion_vocab.items()}
        _model = TFTRecommender(len(_champion_vocab), len(_item_vocab)).to(device)
        _model.eval()
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(path, map_location=device, weights_only=False)

    _champion_vocab = ckpt["champion_vocab"]
    _item_vocab = ckpt["item_vocab"]
    _idx_to_champion = {v: k for k, v in _champion_vocab.items()}

    _model = TFTRecommender(ckpt["num_champions"], ckpt["num_items"]).to(device)
    _model.load_state_dict(ckpt["model_state_dict"])
    _model.eval()


def recommend(champion_ids, item_names=None, top_k=5):
    _load_model()
    device = next(_model.parameters()).device

    champ_indices = [_champion_vocab[c] for c in champion_ids if c in _champion_vocab]
    if not champ_indices:
        return []

    item_indices = []
    if item_names:
        item_indices = [_item_vocab[i] for i in item_names if i in _item_vocab]
    if not item_indices:
        item_indices = [0]

    champ_tensor = torch.tensor(champ_indices, dtype=torch.long, device=device)
    item_tensor = torch.tensor(item_indices, dtype=torch.long, device=device)
    champ_offsets = torch.zeros(1, dtype=torch.long, device=device)
    item_offsets = torch.zeros(1, dtype=torch.long, device=device)

    with torch.no_grad():
        logits = _model(champ_tensor, item_tensor, champ_offsets, item_offsets)
        probs = F.softmax(logits, dim=1)[0]

    owned = set(champ_indices)
    scores = []
    for idx in range(len(_idx_to_champion)):
        if idx in owned:
            continue
        cid = _idx_to_champion[idx]
        scores.append((cid, probs[idx].item()))

    scores.sort(key=lambda x: x[1], reverse=True)
    results = []
    for cid, conf in scores[:top_k]:
        results.append({
            "champion_id": cid,
            "display_name": CHAMPION_NAMES.get(cid, cid),
            "confidence": round(conf, 4),
        })
    return results


if __name__ == "__main__":
    sample_champs = ["TFT17_Blitzcrank", "TFT17_Nunu", "TFT17_Riven"]
    sample_items = ["TFT_Item_RedBuff", "TFT_Item_Crownguard"]
    recs = recommend(sample_champs, sample_items, top_k=5)
    for r in recs:
        print(f"  {r['display_name']:20s} ({r['champion_id']:30s}) confidence={r['confidence']:.4f}")
