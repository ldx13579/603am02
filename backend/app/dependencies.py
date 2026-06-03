from __future__ import annotations

import ipaddress
import json
import time

import redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    if not api_key or api_key not in settings.api_key_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


def _is_trusted_proxy(ip: str, trusted_proxies: list[str]) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        for proxy in trusted_proxies:
            if "/" in proxy:
                if addr in ipaddress.ip_network(proxy, strict=False):
                    return True
            else:
                if addr == ipaddress.ip_address(proxy):
                    return True
    except ValueError:
        pass
    return False


def get_client_ip(request: Request, settings: Settings = Depends(get_settings)) -> str:
    direct_ip = request.client.host if request.client else "unknown"

    if not _is_trusted_proxy(direct_ip, settings.TRUSTED_PROXIES):
        return direct_ip

    for header_name in settings.TRUSTED_PROXY_HEADERS:
        header_value = request.headers.get(header_name)
        if not header_value:
            continue

        if header_name.lower() == "x-forwarded-for":
            ips = [ip.strip() for ip in header_value.split(",")]
            for ip in reversed(ips):
                if not _is_trusted_proxy(ip, settings.TRUSTED_PROXIES):
                    return ip
            return ips[0]
        else:
            return header_value.strip()

    return direct_ip


def _resolve_client_ip(request: Request, settings: Settings) -> str:
    """Standalone IP resolution without FastAPI DI (for use inside dependencies)."""
    direct_ip = request.client.host if request.client else "unknown"

    if not _is_trusted_proxy(direct_ip, settings.TRUSTED_PROXIES):
        return direct_ip

    for header_name in settings.TRUSTED_PROXY_HEADERS:
        header_value = request.headers.get(header_name)
        if not header_value:
            continue
        if header_name.lower() == "x-forwarded-for":
            ips = [ip.strip() for ip in header_value.split(",")]
            for ip in reversed(ips):
                if not _is_trusted_proxy(ip, settings.TRUSTED_PROXIES):
                    return ip
            return ips[0]
        else:
            return header_value.strip()

    return direct_ip


class RateLimiter:
    def __init__(self, requests: int | None = None, window: int | None = None):
        self._requests = requests
        self._window = window

    async def __call__(
        self,
        request: Request,
        settings: Settings = Depends(get_settings),
    ) -> None:
        max_requests = self._requests or settings.RATE_LIMIT_REQUESTS
        window_seconds = self._window or settings.RATE_LIMIT_WINDOW_SECONDS

        client_ip = _resolve_client_ip(request, settings)
        key = f"rate_limit:{client_ip}:{request.url.path}"

        r = get_redis()
        current_time = int(time.time())
        window_start = current_time - window_seconds

        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(current_time * 1000 + id(request) % 1000): current_time})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 1)
        results = pipe.execute()

        request_count = results[2]

        if request_count > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s",
                headers={"Retry-After": str(window_seconds)},
            )


rate_limiter = RateLimiter()


class CacheService:
    def __init__(self):
        self._settings: Settings | None = None

    @property
    def settings(self) -> Settings:
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def get(self, key: str) -> dict | list | None:
        r = get_redis()
        cached = r.get(f"cache:{key}")
        if cached:
            return json.loads(cached)
        return None

    def set(self, key: str, value, ttl: int | None = None, max_ttl: int | None = None) -> None:
        r = get_redis()
        expire = ttl or self.settings.CACHE_TTL_SECONDS
        if max_ttl is not None:
            expire = min(expire, max_ttl)
        r.setex(f"cache:{key}", expire, json.dumps(value))

    def invalidate(self, pattern: str) -> None:
        r = get_redis()
        keys = r.keys(f"cache:{pattern}")
        if keys:
            r.delete(*keys)


cache_service = CacheService()
