import argparse
import json
from pathlib import Path

from elasticsearch import Elasticsearch

MAPPINGS_DIR = Path(__file__).resolve().parent.parent / "config" / "es_mappings"

INDEX_NAMES = [
    "player_stats",
    "champion_stats",
    "item_stats",
    "comp_meta",
    "champion_item_combo",
    "champion_trait_combo",
]


def load_mapping(index_name: str) -> dict:
    mapping_path = MAPPINGS_DIR / f"{index_name}.json"
    with open(mapping_path, "r") as f:
        return json.load(f)


def init_indices(es: Elasticsearch, drop: bool = False) -> None:
    for index_name in INDEX_NAMES:
        if drop and es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
            print(f"Deleted index: {index_name}")

        if not es.indices.exists(index=index_name):
            mapping = load_mapping(index_name)
            es.indices.create(index=index_name, body=mapping)
            print(f"Created index: {index_name}")
        else:
            print(f"Index already exists: {index_name}")


def main():
    parser = argparse.ArgumentParser(description="Initialize Elasticsearch indices for TFT Analytics")
    parser.add_argument("--host", default="localhost", help="Elasticsearch host (default: localhost)")
    parser.add_argument("--port", type=int, default=9200, help="Elasticsearch port (default: 9200)")
    parser.add_argument("--drop", action="store_true", help="Delete existing indices before creating")
    args = parser.parse_args()

    es = Elasticsearch([f"http://{args.host}:{args.port}"])

    if not es.ping():
        print(f"ERROR: Cannot connect to Elasticsearch at {args.host}:{args.port}")
        exit(1)

    print(f"Connected to Elasticsearch at {args.host}:{args.port}")
    init_indices(es, drop=args.drop)
    print("Done.")


if __name__ == "__main__":
    main()
