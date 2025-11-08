import re

import httpx
import pytest

from app.main import create_app

UUID_RE = re.compile(r"^[0-9a-fA-F\-]{36}$")


@pytest.mark.asyncio
async def test_correlation_id_sanitized_when_too_long():
    app = create_app()
    long_val = "x" * 200
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Correlation-ID": long_val},
    ) as ac:
        r = await ac.get("/health")
    cid = r.headers.get("x-correlation-id")
    assert cid and UUID_RE.match(cid), cid
    assert cid != long_val


@pytest.mark.asyncio
async def test_correlation_id_strips_crlf():
    app = create_app()
    bad = "demo\r\nX-Another: evil"  # CRLF-инъекция в заголовок
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-Correlation-ID": bad}
    ) as ac:
        r = await ac.get("/health")
    got = r.headers.get("x-correlation-id")
    assert got and got != bad and UUID_RE.match(got)


@pytest.mark.asyncio
async def test_correlation_id_rejects_invalid_chars():
    app = create_app()
    bad = "inv:alid"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-Correlation-ID": bad}
    ) as ac:
        r = await ac.get("/health")
    got = r.headers.get("x-correlation-id")
    assert got and got != bad and UUID_RE.match(got)


@pytest.mark.asyncio
async def test_correlation_id_allows_safe_chars_and_length_64():
    app = create_app()
    safe = "a" * 64
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-Correlation-ID": safe}
    ) as ac:
        r = await ac.get("/health")
    got = r.headers.get("x-correlation-id")
    assert got == safe


@pytest.mark.asyncio
async def test_correlation_id_length_65_becomes_uuid():
    app = create_app()
    bad = "a" * 65
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-Correlation-ID": bad}
    ) as ac:
        r = await ac.get("/health")
    got = r.headers.get("x-correlation-id")
    assert got and got != bad and UUID_RE.match(got)


@pytest.mark.asyncio
async def test_response_has_single_correlation_id_header():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
    count = sum(1 for k, _ in r.headers.raw if k.lower() == b"x-correlation-id")
    assert count == 1
