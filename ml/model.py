import torch
import torch.nn as nn


class TFTRecommender(nn.Module):
    def __init__(self, num_champions, num_items, embed_dim=64, hidden_dim=128):
        super().__init__()
        self.num_champions = num_champions
        self.num_items = num_items

        self.champion_embed = nn.EmbeddingBag(num_champions, embed_dim, mode="sum")
        self.item_embed = nn.EmbeddingBag(num_items, embed_dim, mode="sum")

        self.mlp = nn.Sequential(
            nn.Linear(embed_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_champions),
        )

    def forward(self, champion_ids, item_ids, champ_offsets, item_offsets):
        champ_repr = self.champion_embed(champion_ids, champ_offsets)
        item_repr = self.item_embed(item_ids, item_offsets)
        x = torch.cat([champ_repr, item_repr], dim=1)
        logits = self.mlp(x)
        return logits
