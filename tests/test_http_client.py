import httpx
import pytest

from app.common.http_client import get_with_policies


@pytest.mark.asyncio
async def test_retries_with_backoff(monkeypatch):
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    RealAsyncClient = httpx.AsyncClient  # важно: сохранить до monkeypatch

    def _factory(*args, **kwargs):
        kwargs["transport"] = transport
        return RealAsyncClient(*args, **kwargs)

    monkeypatch.setattr("app.common.http_client.httpx.AsyncClient", _factory)

    r = await get_with_policies("http://example.com")
    assert r.status_code == 200
    assert attempts["n"] == 2
