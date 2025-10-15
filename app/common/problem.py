from typing import Any, Dict, Optional
from uuid import uuid4

from starlette.responses import JSONResponse


def problem(
    status: int,
    title: str,
    detail: str,
    *,
    type_: str = "about:blank",
    extras: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> JSONResponse:
    payload: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": correlation_id or str(uuid4()),
    }
    if extras:
        payload.update(extras)
    return JSONResponse(payload, status_code=status)
