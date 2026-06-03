from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.dependencies import verify_api_key, rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(exist_ok=True)
    Path(get_settings().DB_BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="Git Habits Analyzer",
    description="Cross-repository Git commit habit analysis API",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key), Depends(rate_limiter)],
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

from app.api.repos import router as repos_router
from app.api.analysis import router as analysis_router
from app.api.tasks import router as tasks_router
from app.api.stats import router as stats_router
from app.api.collaboration import router as collaboration_router
from app.api.violations import router as violations_router
from app.api.export import router as export_router

app.include_router(repos_router)
app.include_router(analysis_router)
app.include_router(tasks_router)
app.include_router(stats_router)
app.include_router(collaboration_router)
app.include_router(violations_router)
app.include_router(export_router)


@app.get("/api/health", dependencies=[])
def health_check():
    return {"status": "ok"}
