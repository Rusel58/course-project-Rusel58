from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

import httpx

from app import settings

_ALLOWED_SCHEMES = {"http", "https"}


def _validate_url(url: str) -> None:
    parts = urlsplit(url)
    scheme = (parts.scheme or "").lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError("Disallowed URL scheme")
    if not parts.netloc:
        raise ValueError("URL must be absolute")


def default_timeout() -> httpx.Timeout:
    connect = float(getattr(settings, "HTTP_CONNECT_TIMEOUT", 2.0))
    read = float(getattr(settings, "HTTP_READ_TIMEOUT", 5.0))
    return httpx.Timeout(connect=connect, read=read, write=read, pool=read)


async def get_with_policies(url: str) -> httpx.Response:
    """
    Безопасные политики для исходящих HTTP:
    - Разрешены только http/https и только абсолютные URL.
    - Автоматические редиректы отключены.
    - Таймауты по умолчанию из settings.
    - Простой backoff-ретрай на сетевых/таймаут-ошибках.
    """
    _validate_url(url)

    retries = int(getattr(settings, "HTTP_MAX_RETRIES", 2))
    backoff = float(getattr(settings, "HTTP_BACKOFF_BASE", 0.2))
    last_err: Exception | None = None

    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    headers = {"User-Agent": "course-project/secure-http-client"}

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(
                timeout=default_timeout(),
                limits=limits,
                headers=headers,
                follow_redirects=False,
                verify=True,
            ) as client:
                return await client.get(url)
        except (httpx.ConnectError, httpx.ReadTimeout) as e:
            last_err = e
            if attempt == retries:
                raise
            await asyncio.sleep(backoff * (2**attempt))

    if last_err is not None:
        raise last_err
    raise RuntimeError("Unexpected state in get_with_policies")
