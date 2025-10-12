from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.routes import items, workouts
from app.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    request_validation_handler,
)
from app.middleware_errors import ProblemJSONMiddleware

app = FastAPI(title="SecDev Course App", version="0.1.0")

app.add_middleware(ProblemJSONMiddleware)


@app.get("/health")
def health():
    return {"status": "ok"}


# Подключаем роутеры (если нужен общий префикс, добавь prefix="/api")
app.include_router(items.router)
app.include_router(workouts.router)

# Единые обработчики ошибок
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_handler)
