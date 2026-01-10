"""WSS public app factory for REACH Core."""

from __future__ import annotations

from base64 import b64decode, b64encode

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from ... import logging as reach_logging
from ...db import Base, SessionLocal, engine, models
from ...globals import RESERVED_PREFIXES
from ..registry import register_protocol


def init_db() -> None:
    """
    Initialize database schema.

    Call this explicitly from the CLI or your own bootstrap code so that
    app import does not have side effects.
    """
    Base.metadata.create_all(bind=engine)


def _is_reserved_path(full_path: str) -> bool:
    """Return True if the request path should bypass dynamic routing."""
    return any(full_path.startswith(prefix) for prefix in RESERVED_PREFIXES)


def _fetch_route(path: str) -> models.Route | None:
    db = SessionLocal()
    try:
        stmt = select(models.Route).where(
            models.Route.method.in_(["WSS", "WS"]),
            models.Route.path == path,
        )
        return db.execute(stmt).scalar_one_or_none()
    finally:
        db.close()


def create_public_app() -> FastAPI:
    """
    Public-facing app: serves dynamic WebSocket routes.
    Typically bound to a port like 8000.
    """
    app = FastAPI(
        title="REACH Core (public WSS)",
        description="Public server for dynamic WebSocket routes",
        version="0.1.0",
        docs_url="None",
        redoc_url=None,
        openapi_url=None,
    )

    @app.websocket("/{full_path:path}")
    async def websocket_router(websocket: WebSocket, full_path: str) -> None:
        if _is_reserved_path(full_path):
            await websocket.accept()
            await websocket.close(code=1008)
            return

        norm_path = full_path.lstrip("/")
        db_route = _fetch_route(norm_path)

        client_ip = websocket.client.host if websocket.client else None
        host = websocket.headers.get("host")

        await websocket.accept()

        if not db_route:
            reach_logging.add_log(
                protocol="wss",
                method="WSS",
                path="/" + full_path,
                route_id=None,
                status_code=404,
                headers={k: v for k, v in websocket.headers.items()},
                query_params={k: v for k, v in websocket.query_params.items()},
                body=None,
                client_ip=client_ip,
                host=host,
            )
            await websocket.close(code=1008)
            return

        reach_logging.add_log(
            protocol="wss",
            method="WSS",
            path="/" + full_path,
            route_id=db_route.id,
            status_code=101,
            headers={k: v for k, v in websocket.headers.items()},
            query_params={k: v for k, v in websocket.query_params.items()},
            body=None,
            client_ip=client_ip,
            host=host,
        )

        if db_route.response_body:
            if getattr(db_route, "body_encoding", "none") == "base64":
                try:
                    payload = b64decode(db_route.response_body)
                except Exception:
                    payload = None
                if payload is not None:
                    await websocket.send_bytes(payload)
                else:
                    await websocket.send_text(db_route.response_body)
            else:
                await websocket.send_text(db_route.response_body)

        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                if message.get("type") != "websocket.receive":
                    continue

                if message.get("text") is not None:
                    reach_logging.add_log(
                        protocol="wss",
                        method="MESSAGE",
                        path="/" + full_path,
                        route_id=db_route.id,
                        status_code=None,
                        headers={},
                        query_params={},
                        body=message["text"],
                        client_ip=client_ip,
                        host=host,
                    )
                elif message.get("bytes") is not None:
                    raw_b64 = b64encode(message["bytes"]).decode("ascii")
                    reach_logging.add_log(
                        protocol="wss",
                        method="MESSAGE",
                        path="/" + full_path,
                        route_id=db_route.id,
                        status_code=None,
                        headers={},
                        query_params={},
                        body=None,
                        client_ip=client_ip,
                        host=host,
                        raw_bytes=raw_b64,
                        raw_bytes_encoding="base64",
                    )
        except WebSocketDisconnect:
            pass

    return app

def create_app() -> FastAPI:
    """
    Backwards-compatible helper returning the public app.
    """
    return create_public_app()

register_protocol(
    "wss",
    public_app="reach.core.protocols.wss.server:create_public_app",
    init_db=init_db,
    description="Public WSS server (FastAPI/Uvicorn).",
)
