from typing import Any, Dict, List, Optional
from elasticsearch import AsyncElasticsearch


async def es_search(
    es: AsyncElasticsearch,
    index: str,
    query: Dict[str, Any],
    size: int = 10,
    from_: int = 0,
    sort: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"query": query, "size": size, "from": from_}
    if sort:
        body["sort"] = sort
    try:
        resp = await es.search(index=index, body=body)
        return resp
    except Exception:
        return {"hits": {"hits": [], "total": {"value": 0}}}


async def es_get_by_id(
    es: AsyncElasticsearch,
    index: str,
    field: str,
    value: str,
) -> Optional[Dict[str, Any]]:
    query = {"term": {field: value}}
    try:
        resp = await es.search(index=index, body={"query": query, "size": 1})
        hits = resp["hits"]["hits"]
        if hits:
            return hits[0]["_source"]
    except Exception:
        pass
    return None


async def es_count(es: AsyncElasticsearch, index: str, query: Optional[Dict] = None) -> int:
    body = {"query": query} if query else {"query": {"match_all": {}}}
    try:
        resp = await es.count(index=index, body=body)
        return resp["count"]
    except Exception:
        return 0


async def get_player_stats(es: AsyncElasticsearch, puuid: str) -> Optional[Dict]:
    return await es_get_by_id(es, "player_stats", "puuid", puuid)


async def get_player_champions(es: AsyncElasticsearch, puuid: str) -> List[Dict]:
    query = {"term": {"puuid.keyword": puuid}}
    resp = await es_search(es, "player_champion_stats", query, size=100)
    results = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        if "character_id" in src and "champion_id" not in src:
            src["champion_id"] = src["character_id"]
        results.append(src)
    return results


async def get_player_traits(es: AsyncElasticsearch, puuid: str) -> List[Dict]:
    query = {"term": {"puuid.keyword": puuid}}
    resp = await es_search(es, "player_trait_stats", query, size=100)
    return [hit["_source"] for hit in resp["hits"]["hits"]]


async def get_player_items(es: AsyncElasticsearch, puuid: str) -> List[Dict]:
    query = {"term": {"puuid.keyword": puuid}}
    resp = await es_search(es, "player_item_stats", query, size=200)
    return [hit["_source"] for hit in resp["hits"]["hits"]]


async def search_players(es: AsyncElasticsearch, name: str, size: int = 20) -> List[Dict]:
    query = {"wildcard": {"puuid": f"*{name}*"}}
    resp = await es_search(es, "player_stats", query, size=size)
    return [hit["_source"] for hit in resp["hits"]["hits"]]


async def get_compositions(
    es: AsyncElasticsearch,
    min_games: int = 10,
    sort_by: str = "win_rate",
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[Dict], int]:
    query = {"range": {"total_games": {"gte": min_games}}}
    sort_field = sort_by if sort_by in ("win_rate", "top4_rate", "avg_placement", "total_games") else "win_rate"
    sort_order = "asc" if sort_field == "avg_placement" else "desc"
    resp = await es_search(
        es, "comp_meta", query, size=limit, from_=offset,
        sort=[{sort_field: {"order": sort_order}}],
    )
    total = resp["hits"]["total"]["value"]
    items = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        if "signature" in src and "comp_signature" not in src:
            src["comp_signature"] = src["signature"]
        items.append(src)
    return items, total


async def get_comp_detail(es: AsyncElasticsearch, comp_signature: str) -> Optional[Dict]:
    res = await es_get_by_id(es, "comp_meta", "signature", comp_signature)
    if res and "signature" in res and "comp_signature" not in res:
        res["comp_signature"] = res["signature"]
    return res


async def get_all_champions(
    es: AsyncElasticsearch,
    sort_by: str = "total_games",
    limit: int = 100,
) -> tuple[List[Dict], int]:
    sort_field = sort_by if sort_by in ("win_rate", "top4_rate", "avg_placement", "total_games", "pick_rate") else "total_games"
    sort_order = "asc" if sort_field == "avg_placement" else "desc"
    resp = await es_search(
        es, "champion_stats", {"match_all": {}}, size=limit,
        sort=[{sort_field: {"order": sort_order}}],
    )
    total = resp["hits"]["total"]["value"]
    items = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        if "character_id" in src and "champion_id" not in src:
            src["champion_id"] = src["character_id"]
        items.append(src)
    return items, total


async def get_champion_detail(es: AsyncElasticsearch, champion_id: str) -> Optional[Dict]:
    res = await es_get_by_id(es, "champion_stats", "character_id", champion_id)
    if res and "character_id" in res and "champion_id" not in res:
        res["champion_id"] = res["character_id"]
    return res


async def get_champion_items(es: AsyncElasticsearch, champion_id: str) -> List[Dict]:
    query = {"term": {"character_id.keyword": champion_id}}
    resp = await es_search(es, "champion_item_combo", query, size=50, sort=[{"total_games": {"order": "desc"}}])
    results = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        n = src["total_games"]
        res = {**src, "win_rate": src["wins"] / n if n else 0}
        if "character_id" in res and "champion_id" not in res:
            res["champion_id"] = res["character_id"]
        results.append(res)
    return results


async def get_champion_traits(es: AsyncElasticsearch, champion_id: str) -> List[Dict]:
    query = {"term": {"character_id.keyword": champion_id}}
    resp = await es_search(es, "champion_trait_combo", query, size=50, sort=[{"total_games": {"order": "desc"}}])
    results = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        n = src["total_games"]
        res = {**src, "win_rate": src["wins"] / n if n else 0}
        if "character_id" in res and "champion_id" not in res:
            res["champion_id"] = res["character_id"]
        results.append(res)
    return results


async def get_all_items(
    es: AsyncElasticsearch,
    sort_by: str = "total_games",
    limit: int = 100,
) -> tuple[List[Dict], int]:
    sort_field = sort_by if sort_by in ("total_games", "avg_placement") else "total_games"
    sort_order = "asc" if sort_field == "avg_placement" else "desc"
    resp = await es_search(
        es, "item_stats", {"match_all": {}}, size=limit,
        sort=[{sort_field: {"order": sort_order}}],
    )
    total = resp["hits"]["total"]["value"]
    items = [hit["_source"] for hit in resp["hits"]["hits"]]
    return items, total


async def get_item_detail(es: AsyncElasticsearch, item_name: str) -> Optional[Dict]:
    return await es_get_by_id(es, "item_stats", "item_name", item_name)


async def get_item_champions(es: AsyncElasticsearch, item_name: str) -> List[Dict]:
    query = {"term": {"item_name.keyword": item_name}}
    resp = await es_search(es, "champion_item_combo", query, size=50, sort=[{"total_games": {"order": "desc"}}])
    results = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        n = src["total_games"]
        res = {**src, "win_rate": src["wins"] / n if n else 0}
        if "character_id" in res and "champion_id" not in res:
            res["champion_id"] = res["character_id"]
        results.append(res)
    return results


async def get_build_recommendations(
    es: AsyncElasticsearch,
    champ_ids: List[str],
    item_names: List[str],
) -> List[Dict]:
    results = []
    for champ_id in champ_ids:
        must_clauses: List[Dict] = [{"term": {"character_id.keyword": champ_id}}]
        if item_names:
            must_clauses.append({"terms": {"item_name.keyword": item_names}})
        query = {"bool": {"must": must_clauses}}
        resp = await es_search(es, "champion_item_combo", query, size=10, sort=[{"total_games": {"order": "desc"}}])
        items_found = [hit["_source"]["item_name"] for hit in resp["hits"]["hits"]]
        if resp["hits"]["hits"]:
            top = resp["hits"]["hits"][0]["_source"]
            n = top["total_games"]
            results.append({
                "champion_id": champ_id,
                "recommended_items": items_found,
                "avg_placement": top["avg_placement"],
                "win_rate": top["wins"] / n if n else 0,
                "total_games": top["total_games"],
            })
    return results


async def get_meta_overview(es: AsyncElasticsearch) -> Dict:
    player_count = await es_count(es, "player_stats")

    champ_resp = await es_search(
        es, "champion_stats", {"match_all": {}}, size=5,
        sort=[{"win_rate": {"order": "desc"}}],
    )
    top_champions = []
    for hit in champ_resp["hits"]["hits"]:
        src = hit["_source"]
        if "character_id" in src and "champion_id" not in src:
            src["champion_id"] = src["character_id"]
        top_champions.append(src)

    comp_resp = await es_search(
        es, "comp_meta", {"match_all": {}}, size=5,
        sort=[{"win_rate": {"order": "desc"}}],
    )
    top_compositions = []
    for hit in comp_resp["hits"]["hits"]:
        src = hit["_source"]
        if "signature" in src and "comp_signature" not in src:
            src["comp_signature"] = src["signature"]
        top_compositions.append(src)

    item_resp = await es_search(
        es, "item_stats", {"match_all": {}}, size=5,
        sort=[{"total_games": {"order": "desc"}}],
    )
    top_items = [hit["_source"] for hit in item_resp["hits"]["hits"]]

    total_matches = 0
    for champ in top_champions:
        total_matches = max(total_matches, champ.get("total_games", 0))

    return {
        "total_players": player_count,
        "total_matches_analyzed": total_matches,
        "top_champions": top_champions,
        "top_compositions": top_compositions,
        "top_items": top_items,
    }
