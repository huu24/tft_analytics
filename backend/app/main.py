from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import health, players, compositions, champions, items, analysis, recommend
from app.services.es_client import close_es_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_es_client()

app = FastAPI(title="TFT Analytics API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(compositions.router, prefix="/api/compositions", tags=["compositions"])
app.include_router(champions.router, prefix="/api/champions", tags=["champions"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])

@app.get("/")
async def root():
    return {"message": "TFT Analytics API", "version": "1.0.0"}
