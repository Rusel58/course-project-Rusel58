from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Workout Log API", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


class SetSchema(BaseModel):
    """Подход: повторы и вес."""

    reps: int = Field(..., ge=1, le=100, description="Количество повторов (1..100)")
    weight_kg: float = Field(..., ge=0.0, le=1000.0, description="Вес в кг (0..1000)")


class ExerciseSchema(BaseModel):
    """Упражнение: имя и набор подходов."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Название упражнения (1..100)"
    )
    sets: List[SetSchema] = Field(default_factory=list, description="Список подходов")


class WorkoutCreate(BaseModel):
    """Тело запроса на создание тренировки."""

    date: date
    notes: Optional[str] = Field(None, max_length=500)
    exercises: List[ExerciseSchema] = Field(default_factory=list)


class WorkoutUpdate(BaseModel):
    """Тело запроса на частичное обновление тренировки."""

    date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)
    exercises: Optional[List[ExerciseSchema]] = None


class Workout(BaseModel):
    """Ответная модель тренировки."""

    id: int
    uid: str
    date: date
    notes: Optional[str] = None
    exercises: List[ExerciseSchema]
    created_at: datetime


_DB: Dict[str, List[Workout]] = {"workouts": []}


def _get_workout_or_404(workout_id: int) -> Workout:
    """Вернуть тренировку или кинуть 404 в нашем формате."""
    for w in _DB["workouts"]:
        if w.id == workout_id:
            return w
    raise ApiError(code="not_found", message="workout not found", status=404)


# 1) GET /workouts — список с опциональными фильтрами по дате
@app.get("/workouts", response_model=List[Workout], summary="List workouts")
def list_workouts(
    date_from: Optional[date] = Query(
        None, description="Фильтр: дата с (включительно)"
    ),
    date_to: Optional[date] = Query(None, description="Фильтр: дата по (включительно)"),
):
    items = _DB["workouts"]
    if date_from:
        items = [w for w in items if w.date >= date_from]
    if date_to:
        items = [w for w in items if w.date <= date_to]
    return items


# 2) POST /workouts — создать тренировку
@app.post(
    "/workouts", response_model=Workout, status_code=201, summary="Create workout"
)
def create_workout(payload: WorkoutCreate):
    new = Workout(
        id=len(_DB["workouts"]) + 1,
        uid=str(uuid4()),
        date=payload.date,
        notes=payload.notes,
        exercises=payload.exercises,
        created_at=datetime.utcnow(),
    )
    _DB["workouts"].append(new)
    return new


# 3) GET /workouts/{id} — получить одну тренировку
@app.get("/workouts/{workout_id}", response_model=Workout, summary="Get workout by id")
def get_workout(workout_id: int):
    return _get_workout_or_404(workout_id)


# 4) PATCH /workouts/{id} — частично обновить тренировку
@app.patch(
    "/workouts/{workout_id}", response_model=Workout, summary="Partially update workout"
)
def patch_workout(workout_id: int, payload: WorkoutUpdate):
    current = _get_workout_or_404(workout_id)
    updates = payload.model_dump(
        exclude_unset=True
    )  # Pydantic v2; в v1 используйте payload.dict(exclude_unset=True)
    updated = current.model_copy(
        update=updates
    )  # Pydantic v2; в v1 используйте current.copy(update=updates)

    # заменить объект в хранилище
    for idx, w in enumerate(_DB["workouts"]):
        if w.id == workout_id:
            _DB["workouts"][idx] = updated
            break
    return updated


# 5) DELETE /workouts/{id} — удалить тренировку
@app.delete("/workouts/{workout_id}", status_code=204, summary="Delete workout")
def delete_workout(workout_id: int):
    # гарантируем 404, если нет
    _ = _get_workout_or_404(workout_id)
    _DB["workouts"] = [w for w in _DB["workouts"] if w.id != workout_id]
    # 204 — без тела ответа
