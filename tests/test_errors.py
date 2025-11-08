import httpx
import pytest
import pytest_asyncio

from app.errors import ApiError
from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------- RFC7807 базовый контракт ----------
@pytest.mark.asyncio
async def test_rfc7807_contract(app):
    @app.get("/boom")
    async def boom():
        raise ApiError(
            status=400,
            title="Bad input",
            detail="Invalid data",
            type_="https://example.com/probs/bad-input",
        )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/boom")
    assert r.status_code == 400
    body = r.json()
    assert {"type", "title", "status", "detail", "correlation_id"} <= body.keys()
    assert body["title"] == "Bad input"
    assert body["status"] == 400


# ---------- Корреляция ----------
@pytest.mark.asyncio
async def test_correlation_id_echo(app):
    @app.get("/boom2")
    async def boom2():
        raise ApiError(status=404, title="Not found", detail="Nope")

    cid = "test-cid-123"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"x-correlation-id": cid}
    ) as ac:
        r = await ac.get("/boom2")
    assert r.headers.get("x-correlation-id") == cid
    assert r.json()["correlation_id"] == cid


# ---------- “Старые” сценарии, но в новом формате RFC7807 ----------
@pytest.mark.asyncio
async def test_not_found_item(client):
    r = await client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    # RFC7807 поля всегда есть
    assert {"type", "title", "status", "detail", "correlation_id"} <= body.keys()
    # если items-роутер кидает ApiError(code="not_found"), расширение присутствует
    if "error_code" in body:
        assert body["error_code"] == "not_found"


@pytest.mark.asyncio
async def test_validation_error(client):
    r = await client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert {"type", "title", "status", "detail", "correlation_id"} <= body.keys()
    # наш request_validation_handler добавляет расширения
    assert body.get("error_code") == "validation_error"
    assert isinstance(body.get("errors", []), list)
