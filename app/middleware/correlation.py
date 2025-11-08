import re
from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

HEADER = b"x-correlation-id"
_ALLOWED_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def _sanitize_correlation_id(raw: str | None) -> str:
    """Разрешаем только безопасный ASCII-токен 1..64, иначе генерируем UUID4."""
    if not raw:
        return str(uuid4())
    s = raw.strip()
    if "\r" in s or "\n" in s:
        return str(uuid4())
    if not _ALLOWED_RE.fullmatch(s):
        return str(uuid4())
    return s


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        cid_bytes = None
        for k, v in scope.get("headers") or []:
            if k.lower() == HEADER:
                cid_bytes = v
                break

        raw = (
            cid_bytes.decode("ascii", "ignore")
            if isinstance(cid_bytes, (bytes, bytearray))
            else None
        )
        cid_str = _sanitize_correlation_id(raw)

        scope.setdefault("state", {})["correlation_id"] = cid_str

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = [
                    (k, v) for (k, v) in (message.get("headers") or []) if k.lower() != HEADER
                ]
                headers.append((HEADER, cid_str.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
