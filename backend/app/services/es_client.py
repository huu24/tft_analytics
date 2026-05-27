from elasticsearch import AsyncElasticsearch
from app.config import settings

es_client: AsyncElasticsearch = None

async def get_es_client() -> AsyncElasticsearch:
    global es_client
    if es_client is None:
        es_client = AsyncElasticsearch([f"http://{settings.ES_HOST}:{settings.ES_PORT}"])
    return es_client

async def close_es_client():
    global es_client
    if es_client is not None:
        await es_client.close()
        es_client = None
