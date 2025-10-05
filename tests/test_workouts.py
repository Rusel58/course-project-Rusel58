import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db():
    """
    Чистим in-memory БД перед каждым тестом, чтобы тесты были независимыми.
    """
    db = get_db()
    db["workouts"].clear()
    db["items"].clear()
    yield


def test_create_workout_201_and_get_by_id_200():
    payload = {"title": "Leg day", "notes": "squats", "duration_min": 45}
    r = client.post("/workouts", json=payload)
    assert r.status_code == 201
    w = r.json()
    assert w["id"] == 1
    assert w["title"] == "Leg day"
    assert w["notes"] == "squats"
    assert w["duration_min"] == 45
    # дата по умолчанию — сегодня (строка ISO)
    assert isinstance(w["date"], str) and len(w["date"]) == 10

    r2 = client.get(f"/workouts/{w['id']}")
    assert r2.status_code == 200
    assert r2.json()["title"] == "Leg day"


def test_create_validation_error_from_pydantic_422():
    # duration_min < 1 нарушает схему -> RequestValidationError -> наш формат
    r = client.post("/workouts", json={"title": "Bad", "duration_min": 0})
    assert r.status_code == 422
    body = r.json()
    assert "error" in body and body["error"]["code"] == "validation_error"


def test_list_workouts_with_date_filters():
    # создаём в разные даты
    client.post("/workouts", json={"title": "A", "date": "2025-09-01"})
    client.post("/workouts", json={"title": "B", "date": "2025-09-10"})
    client.post("/workouts", json={"title": "C", "date": "2025-09-20"})

    r = client.get(
        "/workouts", params={"date_from": "2025-09-05", "date_to": "2025-09-15"}
    )
    assert r.status_code == 200
    data = r.json()
    titles = [w["title"] for w in data]
    assert titles == ["B"]  # попадает только B
    for w in data:
        assert "2025-09-05" <= w["date"] <= "2025-09-15"


def test_patch_workout_ok_and_validation_guard():
    # создаём
    r = client.post("/workouts", json={"title": "X"})
    wid = r.json()["id"]

    # защита от пустого title -> 422 с нашим кодом
    r_bad = client.patch(f"/workouts/{wid}", json={"title": ""})
    assert r_bad.status_code == 422
    assert r_bad.json()["error"]["code"] == "validation_error"

    # частичный апдейт — ok
    r_ok = client.patch(
        f"/workouts/{wid}", json={"notes": "updated", "duration_min": 30}
    )
    assert r_ok.status_code == 200
    body = r_ok.json()
    assert body["notes"] == "updated"
    assert body["duration_min"] == 30
    assert body["title"] == "X"  # остался прежним


def test_delete_workout_204_then_404():
    r = client.post("/workouts", json={"title": "ToDelete"})
    wid = r.json()["id"]

    r_del = client.delete(f"/workouts/{wid}")
    assert r_del.status_code == 204
    assert r_del.text == "" or r_del.content == b""  # 204 No Content

    r_404 = client.get(f"/workouts/{wid}")
    assert r_404.status_code == 404
    body = r_404.json()
    assert "error" in body and body["error"]["code"] == "not_found"
