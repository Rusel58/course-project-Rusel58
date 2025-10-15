# app/common/http_client.py
from __future__ import annotations

import asyncio

import httpx

from app import settings  # абсолютный импорт, не относительный!


def default_timeout() -> httpx.Timeout:
    # Поддерживает и константы, и ленивые геттеры из settings
    connect = getattr(settings, "HTTP_CONNECT_TIMEOUT", 2.0)
    read = getattr(settings, "HTTP_READ_TIMEOUT", 5.0)
    return httpx.Timeout(connect=connect, read=read, write=read, pool=read)


async def get_with_policies(url: str) -> httpx.Response:
    retries = int(getattr(settings, "HTTP_MAX_RETRIES", 2))
    backoff = float(getattr(settings, "HTTP_BACKOFF_BASE", 0.2))
    last_err: Exception | None = None

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=default_timeout()) as client:
                return await client.get(url)
        except (httpx.ConnectError, httpx.ReadTimeout) as e:
            last_err = e
            if attempt == retries:
                raise
            await asyncio.sleep(backoff * (2**attempt))
    assert last_err
    raise last_err
