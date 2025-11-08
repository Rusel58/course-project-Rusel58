import httpx
import pytest

from app.common.http_client import get_with_policies


@pytest.mark.asyncio
async def test_does_not_follow_redirects(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "https://evil.example/"})

    transport = httpx.MockTransport(handler)
    RealAsyncClient = httpx.AsyncClient

    def _factory(*args, **kwargs):
        kwargs["transport"] = transport
        return RealAsyncClient(*args, **kwargs)

    monkeypatch.setattr("app.common.http_client.httpx.AsyncClient", _factory)

    r = await get_with_policies("https://good.example/resource")
    assert r.status_code == 302
    assert r.headers.get("Location") == "https://evil.example/"


@pytest.mark.asyncio
async def test_disallows_non_http_schemes():
    with pytest.raises(ValueError):
        await get_with_policies("file:///etc/passwd")

    with pytest.raises(ValueError):
        await get_with_policies("mailto:root@localhost")

    with pytest.raises(ValueError):
        await get_with_policies("/relative/path")
