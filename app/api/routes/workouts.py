from __future__ import annotations

from datetime import date as _date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Response

from app.db import get_db
from app.errors import ApiError

BODY_REQUIRED = Body(...)

router = APIRouter(prefix="/workouts", tags=["workouts"])


def _rows() -> List[Dict[str, Any]]:
    db = get_db()
    # приводим хранилище к списку
    if "workouts" not in db or not isinstance(db["workouts"], list):
        db["workouts"] = []
    return db["workouts"]


def _next_id(rows: List[Dict[str, Any]]) -> int:
    return max([w["id"] for w in rows], default=0) + 1


def _find(rows: List[Dict[str, Any]], wid: int) -> Optional[Dict[str, Any]]:
    return next((w for w in rows if w.get("id") == wid), None)


@router.post("", status_code=201)
def create_workout(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:  # noqa: B008
    rows = _rows()

    title = payload.get("title")
    if not title:
        raise ApiError(
            422,
            "Unprocessable Entity",
            "Request validation failed",
            extras={
                "error_code": "validation_error",
                "errors": [{"loc": "body.title", "msg": "required", "type": "missing"}],
            },
        )

    duration_raw = payload.get("duration_min", None)
    if duration_raw is None:
        duration = 1
    else:
        try:
            duration = int(duration_raw)
        except (TypeError, ValueError):
            duration = 0
        if duration < 1:
            raise ApiError(
                422,
                "Unprocessable Entity",
                "Request validation failed",
                extras={
                    "error_code": "validation_error",
                    "errors": [
                        {
                            "loc": "body.duration_min",
                            "msg": ">= 1",
                            "type": "greater_than_equal",
                        }
                    ],
                },
            )

    wid = _next_id(rows)
    w = {
        "id": wid,
        "title": title,
        "notes": payload.get("notes"),
        "duration_min": duration,
        "date": payload.get("date") or _date.today().isoformat(),
    }
    rows.append(w)
    return w


@router.get("", status_code=200)
def list_workouts(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows = list(_rows())
    if date_from or date_to:
        lo = date_from or "0000-00-00"
        hi = date_to or "9999-12-31"
        rows = [w for w in rows if lo <= w["date"] <= hi]
    rows.sort(key=lambda w: w["date"])
    return rows


@router.get("/{wid}")
def get_workout(wid: int) -> Dict[str, Any]:
    rows = _rows()
    w = _find(rows, wid)
    if not w:
        raise ApiError(
            404, "Not Found", "Workout not found", extras={"error_code": "not_found"}
        )
    return w


@router.patch("/{wid}")
def patch_workout(
    wid: int,
    payload: Dict[str, Any] = BODY_REQUIRED,  # B008 не триггерится
) -> Dict[str, Any]:
    rows = _rows()
    w = _find(rows, wid)
    if not w:
        raise ApiError(
            404, "Not Found", "Workout not found", extras={"error_code": "not_found"}
        )

    if "title" in payload and payload["title"] == "":
        raise ApiError(
            422,
            "Unprocessable Entity",
            "Title must not be empty",
            extras={
                "error_code": "validation_error",
                "errors": [
                    {
                        "loc": "body.title",
                        "msg": "min length 1",
                        "type": "string_too_short",
                    }
                ],
            },
        )

    if "duration_min" in payload:
        try:
            new_dur = int(payload["duration_min"])
        except (TypeError, ValueError):
            new_dur = 0
        if new_dur < 1:
            raise ApiError(
                422,
                "Unprocessable Entity",
                "Request validation failed",
                extras={
                    "error_code": "validation_error",
                    "errors": [
                        {
                            "loc": "body.duration_min",
                            "msg": ">= 1",
                            "type": "greater_than_equal",
                        }
                    ],
                },
            )

    for k, v in payload.items():
        if v is not None:
            w[k] = v
    return w


@router.delete("/{wid}", status_code=204, response_class=Response)
def delete_workout(wid: int) -> Response:
    rows = _rows()
    w = _find(rows, wid)
    if not w:
        raise ApiError(
            404, "Not Found", "Workout not found", extras={"error_code": "not_found"}
        )
    rows.remove(w)
    return Response(status_code=204)
