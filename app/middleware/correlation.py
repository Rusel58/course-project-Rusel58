from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

HEADER = b"x-correlation-id"


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Читаем из заголовка или генерируем
        headers = dict(scope.get("headers") or [])
        cid = headers.get(HEADER, None)
        cid_str = (cid.decode() if isinstance(cid, (bytes, bytearray)) else cid) or str(
            uuid4()
        )

        # кладём в scope для хендлеров
        scope.setdefault("state", {})
        scope["state"]["correlation_id"] = cid_str

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers") or [])
                # убрать возможные дубликаты (регистронезависимо)
                raw_headers = [(k, v) for (k, v) in raw_headers if k.lower() != HEADER]
                raw_headers.append((HEADER, cid_str.encode()))
                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
