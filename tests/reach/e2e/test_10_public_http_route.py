from __future__ import annotations

import secrets
from typing import TypedDict

import httpx
import pytest


class PublicRouteContext(TypedDict):
    public_port: int
    public_base: str
    route1: str
    hash1: str


@pytest.fixture
def public_route_context(
    repo_root, db_file, db_session_factory, seed_route, free_port, uvicorn_runner, run_id
) -> PublicRouteContext:
    hash1 = secrets.token_hex(8)
    route1 = f"route-{run_id}-{hash1[:8]}"
    seed_route(method="GET", path=route1, response_body=f"hash1:{hash1}")

    public_port = free_port()
    public_base = f"http://127.0.0.1:{public_port}"

    with uvicorn_runner(
        app_ref="reach.core.protocols.http.server:create_public_app",
        host="127.0.0.1",
        port=public_port,
        db_file=db_file,
        repo_root=repo_root,
        ready_url=f"{public_base}/definitely-missing-path",
    ):
        yield {
            "public_port": public_port,
            "public_base": public_base,
            "route1": route1,
            "hash1": hash1,
        }


@pytest.mark.e2e
@pytest.mark.integration
def test_public_http_starts_on_random_port(public_route_context: PublicRouteContext) -> None:
    response = httpx.get(f"{public_route_context['public_base']}/definitely-missing-path", timeout=5.0)
    assert 1024 <= public_route_context["public_port"] <= 65535
    assert response.status_code == 404


@pytest.mark.e2e
@pytest.mark.integration
def test_public_http_get_route1(public_route_context: PublicRouteContext) -> None:
    response = httpx.get(
        f"{public_route_context['public_base']}/{public_route_context['route1']}",
        timeout=5.0,
    )
    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.integration
def test_public_http_route1_response_contains_hash1(public_route_context: PublicRouteContext) -> None:
    response = httpx.get(
        f"{public_route_context['public_base']}/{public_route_context['route1']}",
        timeout=5.0,
    )
    assert public_route_context["hash1"] in response.text
