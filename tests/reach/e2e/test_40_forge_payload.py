from __future__ import annotations

import secrets
from typing import Any, TypedDict

import pytest
from sqlalchemy import select

from reach.core.client import CoreClient
from reach.core.db.models import Route
from reach.forge.api import ForgeController


class ForgeTrace(TypedDict):
    hash1: str
    route_path: str
    expected_headers: dict[str, str]
    payload_kind: str
    payload_value: str
    payload_family: str | None
    created_route: dict[str, Any]
    db_row: Route | None


@pytest.fixture
def forge_trace(repo_root, db_file, db_session_factory, free_port, uvicorn_runner, run_id) -> ForgeTrace:
    hash1 = secrets.token_hex(8)
    route_path = f"/forge-{run_id}-{hash1[:8]}"
    callback_url = f"https://callback.local/{hash1}"
    expected_headers = {"X-Verify-Hash": hash1}

    admin_port = free_port()
    admin_base = f"http://127.0.0.1:{admin_port}"

    with uvicorn_runner(
        app_ref="reach.core.server:create_admin_app",
        host="127.0.0.1",
        port=admin_port,
        db_file=db_file,
        repo_root=repo_root,
        ready_url=f"{admin_base}/api/health",
    ):
        controller = ForgeController(CoreClient(admin_base))
        result = controller.create_route_with_payload(
            kind="xss_basic",
            path=route_path,
            method="GET",
            status_code=200,
            content_type="text/html",
            headers=expected_headers,
            callback_url=callback_url,
        )

    payload = result["payload"]
    created_route = result["route"]

    with db_session_factory() as session:
        stmt = select(Route).where(
            Route.method == "GET",
            Route.path == route_path.lstrip("/"),
        )
        row = session.execute(stmt).scalar_one_or_none()

    return {
        "hash1": hash1,
        "route_path": route_path,
        "expected_headers": expected_headers,
        "payload_kind": payload.kind,
        "payload_value": payload.value,
        "payload_family": payload.metadata.get("family"),
        "created_route": created_route,
        "db_row": row,
    }


@pytest.mark.e2e
@pytest.mark.integration
def test_forge_creates_payload_and_route_with_hash1(forge_trace: ForgeTrace) -> None:
    assert forge_trace["hash1"] in forge_trace["payload_value"]
    assert forge_trace["payload_kind"] == "xss_basic"
    assert forge_trace["payload_family"] == "xss"
    assert forge_trace["created_route"]["method"] == "GET"
    assert forge_trace["created_route"]["path"] == forge_trace["route_path"].lstrip("/")


@pytest.mark.e2e
@pytest.mark.integration
def test_forge_route_row_exists_in_db(forge_trace: ForgeTrace) -> None:
    assert forge_trace["db_row"] is not None, "Expected route row to exist in DB after forge create"


@pytest.mark.e2e
@pytest.mark.integration
def test_forge_persisted_payload_and_template_fields(forge_trace: ForgeTrace) -> None:
    row = forge_trace["db_row"]
    assert row is not None
    assert row.response_body == forge_trace["payload_value"]
    assert row.status_code == 200
    assert row.content_type == "text/html"
    assert row.body_encoding == "none"
    assert row.headers == forge_trace["expected_headers"]
