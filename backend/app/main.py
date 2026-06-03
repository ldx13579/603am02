from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="Git Habits Analyzer",
    description="Cross-repository Git commit habit analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.repos import router as repos_router
from app.api.analysis import router as analysis_router
from app.api.tasks import router as tasks_router

app.include_router(repos_router)
app.include_router(analysis_router)
app.include_router(tasks_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
