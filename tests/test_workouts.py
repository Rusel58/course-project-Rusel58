import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.db import get_db
from app.main import create_app


@pytest.fixture(autouse=True)
def _clean_db():
    """Чистим in-memory БД перед каждым тестом."""
    db = get_db()
    db["workouts"].clear()
    db["items"].clear()
    yield


@pytest_asyncio.fixture
async def client():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def _assert_problem_json(body: dict):
    assert {"type", "title", "status", "detail", "correlation_id"} <= body.keys()


@pytest.mark.asyncio
async def test_create_workout_201_and_get_by_id_200(client: AsyncClient):
    payload = {"title": "Leg day", "notes": "squats", "duration_min": 45}
    r = await client.post("/workouts", json=payload)
    assert r.status_code == 201
    w = r.json()
    assert w["id"] == 1
    assert w["title"] == "Leg day"
    assert w["notes"] == "squats"
    assert w["duration_min"] == 45
    # дата по умолчанию — ISO YYYY-MM-DD
    assert isinstance(w["date"], str) and len(w["date"]) == 10

    r2 = await client.get(f"/workouts/{w['id']}")
    assert r2.status_code == 200
    assert r2.json()["title"] == "Leg day"


@pytest.mark.asyncio
async def test_create_validation_error_from_pydantic_422(client: AsyncClient):
    # duration_min < 1 нарушает схему -> RequestValidationError -> RFC7807
    r = await client.post("/workouts", json={"title": "Bad", "duration_min": 0})
    assert r.status_code == 422
    body = r.json()
    await _assert_problem_json(body)
    assert body.get("error_code") == "validation_error"
    # опционально проверим, что есть детализация по полям
    assert isinstance(body.get("errors", []), list)


@pytest.mark.asyncio
async def test_list_workouts_with_date_filters(client: AsyncClient):
    # создаём в разные даты
    await client.post("/workouts", json={"title": "A", "date": "2025-09-01"})
    await client.post("/workouts", json={"title": "B", "date": "2025-09-10"})
    await client.post("/workouts", json={"title": "C", "date": "2025-09-20"})

    r = await client.get(
        "/workouts", params={"date_from": "2025-09-05", "date_to": "2025-09-15"}
    )
    assert r.status_code == 200
    data = r.json()
    titles = [w["title"] for w in data]
    assert titles == ["B"]  # попадает только B
    for w in data:
        assert "2025-09-05" <= w["date"] <= "2025-09-15"


@pytest.mark.asyncio
async def test_patch_workout_ok_and_validation_guard(client: AsyncClient):
    # создаём
    r = await client.post("/workouts", json={"title": "X"})
    wid = r.json()["id"]

    # защита от пустого title -> 422 с нашим кодом
    r_bad = await client.patch(f"/workouts/{wid}", json={"title": ""})
    assert r_bad.status_code == 422
    body = r_bad.json()
    await _assert_problem_json(body)
    assert body.get("error_code") == "validation_error"

    # частичный апдейт — ok
    r_ok = await client.patch(
        f"/workouts/{wid}", json={"notes": "updated", "duration_min": 30}
    )
    assert r_ok.status_code == 200
    body_ok = r_ok.json()
    assert body_ok["notes"] == "updated"
    assert body_ok["duration_min"] == 30
    assert body_ok["title"] == "X"  # остался прежним


@pytest.mark.asyncio
async def test_delete_workout_204_then_404(client: AsyncClient):
    r = await client.post("/workouts", json={"title": "ToDelete"})
    wid = r.json()["id"]

    r_del = await client.delete(f"/workouts/{wid}")
    assert r_del.status_code == 204
    # 204 No Content: тело пустое
    assert r_del.content in (b"",)

    r_404 = await client.get(f"/workouts/{wid}")
    assert r_404.status_code == 404
    body = r_404.json()
    await _assert_problem_json(body)
    # если маршруты поднимают ApiError(404, ..., extras={"error_code": "not_found"})
    # то проверим расширение:
    if "error_code" in body:
        assert body["error_code"] == "not_found"
