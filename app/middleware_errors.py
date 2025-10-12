import json
import os
import traceback
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ProblemJSONMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        corr = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        try:
            response: Response = await call_next(request)
            response.headers["x-correlation-id"] = corr
            return response
        except Exception as e:
            is_prod = os.getenv("APP_ENV") == "production"
            problem = {
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": None if is_prod else "".join(traceback.format_exception(e)),
                "correlation_id": corr,
            }
            return Response(
                content=json.dumps(problem),
                media_type="application/problem+json",
                status_code=500,
                headers={"x-correlation-id": corr},
            )
