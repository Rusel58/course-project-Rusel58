from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.routes import items, uploads, workouts
from app.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    request_validation_handler,
)
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware_errors import ProblemJSONMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="SecDev Course App", version="0.1.0")

    # порядок важен: сначала твоя мидлвара, затем корреляция
    app.add_middleware(ProblemJSONMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # роутеры
    app.include_router(items.router)
    app.include_router(workouts.router)
    app.include_router(uploads.router)

    # обработчики ошибок (RFC7807)
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    return app


app = create_app()
