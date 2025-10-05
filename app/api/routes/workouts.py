import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Query

from app.db import get_db
from app.errors import ApiError
from app.schemas.workouts import WorkoutIn, WorkoutOut, WorkoutUpdate

router = APIRouter(tags=["workouts"])


def _find_workout_or_404(workout_id: int) -> dict:
    db = get_db()
    for w in db["workouts"]:
        if w["id"] == workout_id:
            return w
    raise ApiError(code="not_found", message="workout not found", status=404)


@router.get("/workouts", response_model=list[WorkoutOut])
def list_workouts(
    date_from: Annotated[dt.date | None, Query()] = None,
    date_to: Annotated[dt.date | None, Query()] = None,
):
    db = get_db()
    res = db["workouts"]
    if date_from is not None:
        res = [w for w in res if w["date"] >= date_from]
    if date_to is not None:
        res = [w for w in res if w["date"] <= date_to]
    return res


@router.post("/workouts", response_model=WorkoutOut, status_code=201)
def create_workout(payload: WorkoutIn):
    db = get_db()
    wid = len(db["workouts"]) + 1
    w = {"id": wid, **payload.model_dump()}
    db["workouts"].append(w)
    return w


@router.get("/workouts/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int):
    return _find_workout_or_404(workout_id)


@router.patch("/workouts/{workout_id}", response_model=WorkoutOut)
def update_workout(workout_id: int, payload: WorkoutUpdate):
    w = _find_workout_or_404(workout_id)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and (data["title"] is None or data["title"] == ""):
        raise ApiError(
            code="validation_error", message="title must be 1..100 chars", status=422
        )
    w.update(data)
    return w


@router.delete("/workouts/{workout_id}", status_code=204)
def delete_workout(workout_id: int):
    db = get_db()
    w = _find_workout_or_404(workout_id)
    db["workouts"].remove(w)
    return None
