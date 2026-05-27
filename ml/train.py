import json
import glob
import os
import sys
import logging
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.config.tft_static_data import CHAMPION_NAMES, ITEM_NAMES
from ml.model import TFTRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHAMPION_VOCAB = {cid: idx for idx, cid in enumerate(sorted(CHAMPION_NAMES.keys()))}
ITEM_VOCAB = {iid: idx for idx, iid in enumerate(sorted(ITEM_NAMES.keys()))}
NUM_CHAMPIONS = len(CHAMPION_VOCAB)
NUM_ITEMS = len(ITEM_VOCAB)


def load_matches(data_dir=None):
    if data_dir is None:
        data_dir = Path(__file__).resolve().parent.parent
    patterns = [str(Path(data_dir) / "sample_*.json"), str(Path(data_dir) / "matches_*.json")]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    if not files:
        minio_files = _try_load_minio()
        if minio_files:
            return minio_files
        logger.warning("No match JSON files found in %s", data_dir)
        return []
    matches = []
    for f in files:
        with open(f) as fh:
            matches.append(json.load(fh))
    logger.info("Loaded %d matches from %d files", len(matches), len(files))
    return matches


def _try_load_minio():
    try:
        from minio import Minio
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000").replace("http://", "").replace("https://", "")
        client = Minio(
            endpoint,
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False,
        )
        bucket = os.getenv("MINIO_BUCKET", "tft-matches")
        matches = []
        for obj in client.list_objects(bucket, prefix="matches/"):
            resp = client.get_object(bucket, obj.object_name)
            matches.append(json.loads(resp.read()))
        logger.info("Loaded %d matches from MinIO bucket '%s'", len(matches), bucket)
        return matches
    except Exception as e:
        logger.info("MinIO not available: %s", e)
        return []


def extract_samples(matches):
    samples = []
    for match in matches:
        participants = match.get("info", {}).get("participants", [])
        for p in participants:
            placement = p.get("placement", 8)
            units = p.get("units", [])
            champ_indices = []
            item_indices = []
            for u in units:
                cid = u.get("character_id", "")
                if cid in CHAMPION_VOCAB:
                    champ_indices.append(CHAMPION_VOCAB[cid])
                for item_name in u.get("itemNames", []):
                    if item_name in ITEM_VOCAB:
                        item_indices.append(ITEM_VOCAB[item_name])
            if len(champ_indices) < 2:
                continue
            weight = max(0.1, (9 - placement) / 8.0)
            for i in range(len(champ_indices)):
                masked = champ_indices[:i] + champ_indices[i + 1:]
                target = champ_indices[i]
                samples.append((masked, item_indices, target, weight))
    logger.info("Extracted %d training samples", len(samples))
    return samples


class TFTDataset(Dataset):
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        champ_ids, item_ids, target, weight = self.samples[idx]
        return (
            torch.tensor(champ_ids, dtype=torch.long),
            torch.tensor(item_ids, dtype=torch.long) if item_ids else torch.zeros(1, dtype=torch.long),
            torch.tensor(target, dtype=torch.long),
            torch.tensor(weight, dtype=torch.float),
        )


def collate_fn(batch):
    champ_tensors = [b[0] for b in batch]
    item_tensors = [b[1] for b in batch]
    targets = torch.stack([b[2] for b in batch])
    weights = torch.stack([b[3] for b in batch])

    champ_ids = torch.cat(champ_tensors)
    champ_offsets = torch.zeros(len(batch), dtype=torch.long)
    offset = 0
    for i, t in enumerate(champ_tensors):
        if i > 0:
            offset += len(champ_tensors[i - 1])
        champ_offsets[i] = offset

    item_ids = torch.cat(item_tensors)
    item_offsets = torch.zeros(len(batch), dtype=torch.long)
    offset = 0
    for i, t in enumerate(item_tensors):
        if i > 0:
            offset += len(item_tensors[i - 1])
        item_offsets[i] = offset

    return champ_ids, item_ids, champ_offsets, item_offsets, targets, weights


def train(data_dir=None, epochs=20, batch_size=256, lr=0.001):
    matches = load_matches(data_dir)
    if not matches:
        logger.error("No match data available. Place sample_*.json files in project root or configure MinIO.")
        return

    samples = extract_samples(matches)
    if not samples:
        logger.error("No training samples extracted.")
        return

    split = int(len(samples) * 0.8)
    train_data = samples[:split]
    val_data = samples[split:]
    logger.info("Train: %d, Val: %d", len(train_data), len(val_data))

    train_loader = DataLoader(TFTDataset(train_data), batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(TFTDataset(val_data), batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TFTRecommender(NUM_CHAMPIONS, NUM_ITEMS).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(reduction="none")

    ckpt_dir = Path(__file__).resolve().parent / "checkpoints"
    ckpt_dir.mkdir(exist_ok=True)
    best_val_loss = float("inf")

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0
        total_samples = 0
        for champ_ids, item_ids, champ_off, item_off, targets, weights in train_loader:
            champ_ids = champ_ids.to(device)
            item_ids = item_ids.to(device)
            champ_off = champ_off.to(device)
            item_off = item_off.to(device)
            targets = targets.to(device)
            weights = weights.to(device)

            logits = model(champ_ids, item_ids, champ_off, item_off)
            loss = (criterion(logits, targets) * weights).mean()

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(targets)
            total_samples += len(targets)

        train_loss = total_loss / max(total_samples, 1)

        model.eval()
        val_loss = 0
        val_samples = 0
        with torch.no_grad():
            for champ_ids, item_ids, champ_off, item_off, targets, weights in val_loader:
                champ_ids = champ_ids.to(device)
                item_ids = item_ids.to(device)
                champ_off = champ_off.to(device)
                item_off = item_off.to(device)
                targets = targets.to(device)
                weights = weights.to(device)

                logits = model(champ_ids, item_ids, champ_off, item_off)
                loss = (criterion(logits, targets) * weights).mean()
                val_loss += loss.item() * len(targets)
                val_samples += len(targets)

        val_loss = val_loss / max(val_samples, 1)
        logger.info("Epoch %d/%d - train_loss: %.4f - val_loss: %.4f", epoch, epochs, train_loss, val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            ckpt_path = ckpt_dir / "best_model.pt"
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_loss": val_loss,
                "champion_vocab": CHAMPION_VOCAB,
                "item_vocab": ITEM_VOCAB,
                "num_champions": NUM_CHAMPIONS,
                "num_items": NUM_ITEMS,
            }, ckpt_path)
            logger.info("Saved best model (val_loss: %.4f) to %s", val_loss, ckpt_path)

    logger.info("Training complete. Best val_loss: %.4f", best_val_loss)


if __name__ == "__main__":
    train()
