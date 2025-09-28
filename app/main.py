import datetime as dt
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="SecDev Course App", version="0.1.0")


# ==== Унифицированные ошибки API ====
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
    # Нормализуем все HTTPException в наш конверт ошибок
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    # Валидационные ошибки FastAPI/Pydantic -> единый формат
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "request validation failed",
            }
        },
    )


# ==== Health ====
@app.get("/health")
def health():
    return {"status": "ok"}


# ==== Простейшая сущность из тестов ====
_DB = {"items": [], "workouts": []}


@app.post("/items")
def create_item(name: str):
    # Тест ожидает 422 и конверт ошибок при пустом имени
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    # Тест ожидает 404 и {"error": {"code": "not_found", ...}}
    raise ApiError(code="not_found", message="item not found", status=404)


# ==== Workout Log (минимальная реализация 5 REST-методов) ====
class WorkoutIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    date: dt.date = Field(default_factory=dt.date.today)
    notes: Optional[str] = None
    duration_min: Optional[int] = Field(default=None, ge=1, le=1440)


class WorkoutOut(WorkoutIn):
    id: int


class WorkoutUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date: Optional[dt.date] = None
    notes: Optional[str] = None
    duration_min: Optional[int] = Field(default=None, ge=1, le=1440)


def _find_workout_or_404(workout_id: int) -> dict:
    for w in _DB["workouts"]:
        if w["id"] == workout_id:
            return w
    raise ApiError(code="not_found", message="workout not found", status=404)


@app.get("/workouts", response_model=list[WorkoutOut])
def list_workouts():
    return _DB["workouts"]


@app.post("/workouts", response_model=WorkoutOut, status_code=201)
def create_workout(payload: WorkoutIn):
    wid = len(_DB["workouts"]) + 1
    w = {"id": wid, **payload.model_dump()}
    _DB["workouts"].append(w)
    return w


@app.get("/workouts/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: int):
    return _find_workout_or_404(workout_id)


@app.patch("/workouts/{workout_id}", response_model=WorkoutOut)
def update_workout(workout_id: int, payload: WorkoutUpdate):
    w = _find_workout_or_404(workout_id)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and (data["title"] is None or data["title"] == ""):
        # доп. защита, чтобы не превратить в пустой title
        raise ApiError(
            code="validation_error", message="title must be 1..100 chars", status=422
        )
    w.update(data)
    return w


@app.delete("/workouts/{workout_id}", status_code=204)
def delete_workout(workout_id: int):
    w = _find_workout_or_404(workout_id)
    _DB["workouts"].remove(w)
    # 204 No Content
    return None
