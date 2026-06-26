import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logger import get_logger

ASGIReceive = Callable[[], Awaitable[dict[str, Any]]]
ASGISend = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[dict[str, Any], ASGIReceive, ASGISend], Awaitable[None]]

logger = get_logger("app.middleware")


class LoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: ASGIReceive, send: ASGISend) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.monotonic()
        status_code: list[int | None] = [None]

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.exception(
                "Request failed",
                extra={
                    "method": scope.get("method", ""),
                    "path": scope.get("path", ""),
                    "duration_ms": round(duration_ms, 1),
                },
            )
            raise

        duration_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "Request completed",
            extra={
                "method": scope.get("method", ""),
                "path": scope.get("path", ""),
                "status_code": status_code[0],
                "duration_ms": round(duration_ms, 1),
            },
        )
