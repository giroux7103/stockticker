from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as games_router
from app.config import settings

app = FastAPI(title="Stock Ticker Backend", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(games_router)


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}
