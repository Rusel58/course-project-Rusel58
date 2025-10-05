from fastapi import APIRouter

from app.db import get_db
from app.errors import ApiError

router = APIRouter(tags=["items"])


@router.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
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
    raise ApiError(code="not_found", message="item not found", status=404)
