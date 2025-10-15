from fastapi import APIRouter

from app.db import get_db
from app.errors import ApiError

router = APIRouter(tags=["items"])


@router.post("/items", status_code=201)
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            422,
            "Unprocessable Entity",
            "name must be 1..100 chars",
            extras={"error_code": "validation_error"},
        )
    db = get_db()
    item = {"id": len(db["items"]) + 1, "name": name}
    db["items"].append(item)
    return item


@router.get("/items/{item_id}")
def get_item(item_id: int):
    db = get_db()
    for it in db["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(
        404,
        "Not Found",
        "Item not found",
        extras={"error_code": "not_found"},
    )
