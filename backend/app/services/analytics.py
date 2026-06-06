from typing import Any, Dict, List, Optional
from elasticsearch import AsyncElasticsearch
import psycopg2

from app.config import settings


async def serving_index(es: AsyncElasticsearch, logical_name: str) -> str:
    alias_name = f"tft_{logical_name}"
    if await es.indices.exists_alias(name=alias_name):
        return alias_name
    return logical_name


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


async def es_get_by_fields(
    es: AsyncElasticsearch,
    index: str,
    fields: List[str],
    value: str,
) -> Optional[Dict[str, Any]]:
    query = {
        "bool": {
            "should": [{"term": {field: value}} for field in fields],
            "minimum_should_match": 1,
        }
    }
    try:
        resp = await es.search(index=index, body={"query": query, "size": 1})
        hits = resp["hits"]["hits"]
        if hits:
            return hits[0]["_source"]
    except Exception:
        pass
    return None


def term_any(fields: List[str], value: str) -> Dict[str, Any]:
    return {
        "bool": {
            "should": [{"term": {field: value}} for field in fields],
            "minimum_should_match": 1,
        }
    }


async def es_count(es: AsyncElasticsearch, index: str, query: Optional[Dict] = None) -> int:
    body = {"query": query} if query else {"query": {"match_all": {}}}
    try:
        resp = await es.count(index=index, body=body)
        return resp["count"]
    except Exception:
        return 0


def load_active_raw_object_count() -> int:
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT raw_object_count
                    FROM data_versions
                    WHERE is_active = TRUE
                    ORDER BY published_at DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                return int(row[0]) if row else 0
        finally:
            conn.close()
    except Exception:
        return 0


def pg_connect():
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )


def load_player_names(puuids: List[str]) -> Dict[str, str]:
    if not puuids:
        return {}
    try:
        conn = pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT puuid, player_name
                    FROM crawler_players
                    WHERE puuid = ANY(%s) AND player_name IS NOT NULL
                    """,
                    (puuids,),
                )
                return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()
    except Exception:
        return {}


def search_player_names(name: str, limit: int) -> Dict[str, str]:
    try:
        conn = pg_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT puuid, player_name
                    FROM crawler_players
                    WHERE player_name ILIKE %s
                    ORDER BY
                        CASE WHEN player_name ILIKE %s THEN 0 ELSE 1 END,
                        player_name
                    LIMIT %s
                    """,
                    (f"%{name}%", f"{name}%", limit),
                )
                return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()
    except Exception:
        return {}


def enrich_player_names(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    names = load_player_names([row["puuid"] for row in rows if row.get("puuid")])
    for row in rows:
        row["player_name"] = names.get(row.get("puuid"))
    return rows


def enrich_player_name(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row or not row.get("puuid"):
        return row
    names = load_player_names([row["puuid"]])
    row["player_name"] = names.get(row["puuid"])
    return row


def normalize_pick_rate(row: Dict[str, Any], total_matches: int) -> Dict[str, Any]:
    if total_matches > 0 and "total_games" in row:
        row["pick_rate"] = row["total_games"] / total_matches
    return row


async def get_player_stats(es: AsyncElasticsearch, puuid: str) -> Optional[Dict]:
    return enrich_player_name(await es_get_by_id(es, await serving_index(es, "player_stats"), "puuid", puuid))


async def list_players(
    es: AsyncElasticsearch,
    sort_by: str = "win_rate",
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:
    sort_field_map = {
        "win_rate": "win_rate",
        "avg_placement": "avg_placement",
        "top4_rate": "top4_rate",
        "total_games": "total_games",
    }
    sort_field = sort_field_map.get(sort_by, "win_rate")
    sort_order = "asc" if sort_field == "avg_placement" else "desc"
    sort = [{sort_field: {"order": sort_order}}]
    query = {"match_all": {}}
    resp = await es_search(es, await serving_index(es, "player_stats"), query, size=limit, from_=offset, sort=sort)
    return enrich_player_names([hit["_source"] for hit in resp["hits"]["hits"]])


async def get_player_champions(es: AsyncElasticsearch, puuid: str) -> List[Dict]:
    query = term_any(["puuid", "puuid.keyword"], puuid)
    resp = await es_search(es, await serving_index(es, "player_champion_stats"), query, size=100)
    results = []
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        if "character_id" in src and "champion_id" not in src:
            src["champion_id"] = src["character_id"]
        results.append(src)
    return results


async def get_player_traits(es: AsyncElasticsearch, puuid: str) -> List[Dict]:
    query = term_any(["puuid", "puuid.keyword"], puuid)
    resp = await es_search(es, await serving_index(es, "player_trait_stats"), query, size=100)
    return [hit["_source"] for hit in resp["hits"]["hits"]]


async def get_player_items(es: AsyncElasticsearch, puuid: str) -> List[Dict]:
    query = term_any(["puuid", "puuid.keyword"], puuid)
    resp = await es_search(es, await serving_index(es, "player_item_stats"), query, size=200)
    return [hit["_source"] for hit in resp["hits"]["hits"]]


async def search_players(es: AsyncElasticsearch, name: str, size: int = 20) -> List[Dict]:
    matched_names = search_player_names(name.strip(), size * 5)
    rows: List[Dict[str, Any]] = []
    if matched_names:
        query = {
            "bool": {
                "should": [{"term": {"puuid": puuid}} for puuid in matched_names],
                "minimum_should_match": 1,
            }
        }
        resp = await es_search(
            es,
            await serving_index(es, "player_stats"),
            query,
            size=size,
            sort=[{"total_games": {"order": "desc"}}],
        )
        rows = [hit["_source"] for hit in resp["hits"]["hits"]]
        for row in rows:
            row["player_name"] = matched_names.get(row.get("puuid"))

    if len(rows) < size:
        query = {"wildcard": {"puuid": f"*{name}*"}}
        resp = await es_search(es, await serving_index(es, "player_stats"), query, size=size - len(rows))
        seen = {row.get("puuid") for row in rows}
        fallback_rows = [hit["_source"] for hit in resp["hits"]["hits"] if hit["_source"].get("puuid") not in seen]
        rows.extend(enrich_player_names(fallback_rows))
    return rows[:size]


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
        es, await serving_index(es, "comp_meta"), query, size=limit, from_=offset,
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
    res = await es_get_by_fields(
        es,
        await serving_index(es, "comp_meta"),
        ["comp_signature", "signature", "signature.keyword"],
        comp_signature,
    )
    if res and "signature" in res and "comp_signature" not in res:
        res["comp_signature"] = res["signature"]
    return res


async def get_all_champions(
    es: AsyncElasticsearch,
    sort_by: str = "total_games",
    limit: int = 100,
    min_games: int = 10,
) -> tuple[List[Dict], int]:
    sort_field = sort_by if sort_by in ("win_rate", "top4_rate", "avg_placement", "total_games", "pick_rate") else "total_games"
    sort_order = "asc" if sort_field == "avg_placement" else "desc"
    resp = await es_search(
        es, await serving_index(es, "champion_stats"), {"range": {"total_games": {"gte": min_games}}}, size=limit,
        sort=[{sort_field: {"order": sort_order}}],
    )
    total = resp["hits"]["total"]["value"]
    items = []
    total_matches = load_active_raw_object_count()
    for hit in resp["hits"]["hits"]:
        src = hit["_source"]
        if "character_id" in src and "champion_id" not in src:
            src["champion_id"] = src["character_id"]
        normalize_pick_rate(src, total_matches)
        items.append(src)
    return items, total


async def get_champion_detail(es: AsyncElasticsearch, champion_id: str) -> Optional[Dict]:
    res = await es_get_by_fields(
        es,
        await serving_index(es, "champion_stats"),
        ["champion_id", "character_id", "character_id.keyword"],
        champion_id,
    )
    if res and "character_id" in res and "champion_id" not in res:
        res["champion_id"] = res["character_id"]
    return res


async def get_champion_items(es: AsyncElasticsearch, champion_id: str) -> List[Dict]:
    query = term_any(["champion_id", "character_id", "character_id.keyword"], champion_id)
    resp = await es_search(es, await serving_index(es, "champion_item_combo"), query, size=50, sort=[{"total_games": {"order": "desc"}}])
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
    query = term_any(["champion_id", "character_id", "character_id.keyword"], champion_id)
    resp = await es_search(es, await serving_index(es, "champion_trait_combo"), query, size=50, sort=[{"total_games": {"order": "desc"}}])
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
    min_games: int = 10,
) -> tuple[List[Dict], int]:
    sort_field = sort_by if sort_by in ("win_rate", "top4_rate", "total_games", "avg_placement") else "total_games"
    sort_order = "asc" if sort_field == "avg_placement" else "desc"
    resp = await es_search(
        es, await serving_index(es, "item_stats"), {"range": {"total_games": {"gte": min_games}}}, size=limit,
        sort=[{sort_field: {"order": sort_order}}],
    )
    total = resp["hits"]["total"]["value"]
    items = [hit["_source"] for hit in resp["hits"]["hits"]]
    total_matches = load_active_raw_object_count()
    for item in items:
        normalize_pick_rate(item, total_matches)
    return items, total


async def get_item_detail(es: AsyncElasticsearch, item_name: str) -> Optional[Dict]:
    return await es_get_by_id(es, await serving_index(es, "item_stats"), "item_name", item_name)


async def get_item_champions(es: AsyncElasticsearch, item_name: str) -> List[Dict]:
    query = term_any(["item_name", "item_name.keyword"], item_name)
    resp = await es_search(es, await serving_index(es, "champion_item_combo"), query, size=50, sort=[{"total_games": {"order": "desc"}}])
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
        must_clauses: List[Dict] = [term_any(["champion_id", "character_id", "character_id.keyword"], champ_id)]
        if item_names:
            must_clauses.append({
                "bool": {
                    "should": [
                        {"terms": {"item_name": item_names}},
                        {"terms": {"item_name.keyword": item_names}},
                    ],
                    "minimum_should_match": 1,
                }
            })
        query = {"bool": {"must": must_clauses}}
        resp = await es_search(es, await serving_index(es, "champion_item_combo"), query, size=10, sort=[{"total_games": {"order": "desc"}}])
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
    player_count = await es_count(es, await serving_index(es, "player_stats"))
    total_matches = load_active_raw_object_count()

    champ_resp = await es_search(
        es, await serving_index(es, "champion_stats"), {"range": {"total_games": {"gte": 50}}}, size=5,
        sort=[{"win_rate": {"order": "desc"}}],
    )
    top_champions = []
    for hit in champ_resp["hits"]["hits"]:
        src = hit["_source"]
        if "character_id" in src and "champion_id" not in src:
            src["champion_id"] = src["character_id"]
        normalize_pick_rate(src, total_matches)
        top_champions.append(src)

    comp_resp = await es_search(
        es, await serving_index(es, "comp_meta"), {"range": {"total_games": {"gte": 10}}}, size=5,
        sort=[{"win_rate": {"order": "desc"}}],
    )
    top_compositions = []
    for hit in comp_resp["hits"]["hits"]:
        src = hit["_source"]
        if "signature" in src and "comp_signature" not in src:
            src["comp_signature"] = src["signature"]
        top_compositions.append(src)

    item_resp = await es_search(
        es, await serving_index(es, "item_stats"), {"match_all": {}}, size=5,
        sort=[{"total_games": {"order": "desc"}}],
    )
    top_items = [hit["_source"] for hit in item_resp["hits"]["hits"]]
    for item in top_items:
        normalize_pick_rate(item, total_matches)

    return {
        "total_players": player_count,
        "total_matches_analyzed": total_matches,
        "top_champions": top_champions,
        "top_compositions": top_compositions,
        "top_items": top_items,
    }
