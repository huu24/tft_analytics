import argparse
import os

from elasticsearch import Elasticsearch


INDEX_NAMES = [
    "player_stats", "champion_stats", "item_stats", "comp_meta",
    "champion_item_combo", "champion_trait_combo", "player_champion_stats",
    "player_trait_stats", "player_item_stats",
]


def main():
    parser = argparse.ArgumentParser(description="Atomically roll serving aliases back to an existing snapshot.")
    parser.add_argument("data_version", help="Snapshot version, for example v20260602134300153925")
    args = parser.parse_args()
    es = Elasticsearch([f"http://{os.environ.get('ES_HOST', 'elasticsearch')}:{os.environ.get('ES_PORT', '9200')}"])
    actions = []
    for logical_name in INDEX_NAMES:
        concrete_name = f"{logical_name}_{args.data_version}"
        if not es.indices.exists(index=concrete_name):
            raise RuntimeError(f"Missing rollback index: {concrete_name}")
        actions.extend([
            {"remove": {"index": "*", "alias": f"tft_{logical_name}"}},
            {"add": {"index": concrete_name, "alias": f"tft_{logical_name}"}},
        ])
    es.indices.update_aliases(body={"actions": actions})
    print(f"Serving aliases rolled back to {args.data_version}")


if __name__ == "__main__":
    main()
