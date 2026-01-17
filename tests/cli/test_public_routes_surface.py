# tests/test_public_routes_surface.py
import pytest
from fastapi.testclient import TestClient

from reach.core.globals import RESERVED_PREFIXES

from reach.core.server import create_public_app, init_db

ALL_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
# Known paths we want to keep non-public (docs, openapi, debug/admin)
SHOULD_404 = [
    "/docs",
    "/docs/",
    "/redoc",
    "/redoc/",
    "/openapi.json",
    "/api",
    "/api/",
    "/api/routes",
    "/api/logs",
    "/api/health",
    "/debug/routes",
    "/favicon.ico",
]


@pytest.fixture(scope="module")
def public_client() -> TestClient:
    """Single public app instance for these surface checks."""
    init_db()  # ensure tables exist for app startup
    app = create_public_app()
    return TestClient(app)


@pytest.mark.parametrize("method", ALL_METHODS, ids=lambda m: m)
@pytest.mark.parametrize("path", SHOULD_404, ids=lambda p: p)
def test_public_surface_has_no_extra_routes(public_client: TestClient, method: str, path: str):
    resp = public_client.request(method, path)
    assert resp.status_code == 404, (
        f"{method} {path} unexpectedly exposed "
        f"(status {resp.status_code}, body={resp.text})"
    )


@pytest.mark.parametrize("method", ALL_METHODS, ids=lambda m: m)
def test_dynamic_catch_all_returns_clean_404_when_no_route(public_client: TestClient, method: str):
    resp = public_client.request(method, "/some/random/path")
    assert resp.status_code == 404, f"{method} /some/random/path returned {resp.status_code} body={resp.text}"
    # Dynamic catch-all returns a structured 404; tolerate other 404 bodies too
    detail = resp.json().get("detail")
    assert detail in {"No dynamic route matched", "Not Found"}
