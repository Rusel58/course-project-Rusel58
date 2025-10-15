from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse


def problem(
    *,
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extras: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> JSONResponse:
    """RFC 7807 problem+json payload + корректный media type."""
    payload: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": correlation_id,
    }
    if extras:
        payload.update(extras)
    return JSONResponse(
        payload, status_code=status, media_type="application/problem+json"
    )


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        title: str,
        detail: str,
        *,
        code: Optional[str] = None,
        type_: str = "about:blank",
        extras: Optional[Dict[str, Any]] = None,
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type_ = type_
        self.code = code
        self.extras = extras or {}


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    cid = getattr(request.state, "correlation_id", None)
    extras = dict(exc.extras)
    if exc.code is not None:
        extras.setdefault("error_code", exc.code)
    return problem(
        status=exc.status,
        title=exc.title,
        detail=exc.detail,
        type_=exc.type_,
        extras=extras,
        correlation_id=cid,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Приводит любые FastAPI HTTPException к RFC7807.
    - 5xx: маскируем detail
    - 4xx: отдаём безопасный detail (str), без стеков/внутрянки
    """
    cid = getattr(request.state, "correlation_id", None)
    status = exc.status_code or 500
    # Заголовок по статусу (e.g., 404 -> "Not Found")
    title = (
        HTTPStatus(status).phrase
        if status in HTTPStatus._value2member_map_
        else "HTTP Error"
    )

    if status >= 500:
        detail = "Unexpected server error."
        type_ = "about:blank"
    else:
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        type_ = "about:blank"

    return problem(
        status=status,
        title=title,
        detail=detail,
        type_=type_,
        correlation_id=cid,
    )


async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Pydantic-валидация → RFC7807 с расширением 'errors' (список полей).
    """
    cid = getattr(request.state, "correlation_id", None)
    errors: List[Dict[str, Any]] = []
    for e in exc.errors():
        # loc: ('body','field') -> 'body.field'
        loc = ".".join(str(x) for x in e.get("loc", []))
        errors.append(
            {
                "loc": loc,
                "msg": e.get("msg"),
                "type": e.get("type"),
            }
        )

    return problem(
        status=422,
        title="Unprocessable Entity",
        detail="Request validation failed",
        type_="https://example.com/problems/validation-error",
        extras={"errors": errors, "error_code": "validation_error"},
        correlation_id=cid,
    )
