from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "sqlite:///./data/analysis.db"
    REPOS_YAML_PATH: str = "repos.yaml"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    API_KEY: str = "changeme-secret-key"
    API_KEY_HEADER: str = "X-API-Key"

    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    DB_BACKUP_DIR: str = "./data/backups"
    DB_BACKUP_KEEP_COUNT: int = 7

    CACHE_TTL_SECONDS: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
