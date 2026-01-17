"""Reserved path helpers shared by public routers."""

from __future__ import annotations

from functools import wraps
import inspect
from typing import Any, Callable, Awaitable

from fastapi import HTTPException, WebSocket

from ..globals import RESERVED_PREFIXES


def is_reserved_path(full_path: str) -> bool:
    """Return True if the request path should bypass public routing."""
    return any(full_path.startswith(prefix) for prefix in RESERVED_PREFIXES)


def reject_reserved_paths(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that rejects reserved prefixes for HTTP and WebSocket handlers.
    """
    sig = inspect.signature(fn)
    is_async = inspect.iscoroutinefunction(fn)

    async def _async_reject(*args: Any, **kwargs: Any) -> Any:
        bound = sig.bind_partial(*args, **kwargs)
        full_path = bound.arguments.get("full_path")
        if isinstance(full_path, str) and is_reserved_path(full_path):
            websocket = bound.arguments.get("websocket")
            if isinstance(websocket, WebSocket):
                await websocket.accept()
                await websocket.close(code=1008)
                return None
            raise HTTPException(status_code=404, detail="Not found")
        return await fn(*args, **kwargs)

    def _sync_reject(*args: Any, **kwargs: Any) -> Any:
        bound = sig.bind_partial(*args, **kwargs)
        full_path = bound.arguments.get("full_path")
        if isinstance(full_path, str) and is_reserved_path(full_path):
            raise HTTPException(status_code=404, detail="Not found")
        return fn(*args, **kwargs)

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Awaitable[Any] | Any:
        if is_async:
            return _async_reject(*args, **kwargs)
        return _sync_reject(*args, **kwargs)

    return wrapper
