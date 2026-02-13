from __future__ import annotations

import secrets
from typing import Any, TypedDict

import httpx
import pytest


class AdminCrudTrace(TypedDict):
    admin_port: int
    admin_health_status: int
    route1: str
    route2: str
    hash2: str
    routes_before: list[dict[str, Any]]
    create_route2_status: int
    created_route2: dict[str, Any]
    routes_after_create: list[dict[str, Any]]
    update_route2_status: int
    updated_route2: dict[str, Any]
    public_get_after_update_status: int
    public_post_after_update_status: int
    public_post_after_update_body: str
    delete_route2_status: int
    routes_final: list[dict[str, Any]]


@pytest.fixture
def admin_crud_trace(
    repo_root, db_file, db_session_factory, seed_route, free_port, uvicorn_runner, run_id
) -> AdminCrudTrace:
    hash1 = secrets.token_hex(8)
    hash2 = secrets.token_hex(8)
    route1 = f"route-{run_id}-{hash1[:8]}"
    route2 = f"route-{run_id}-{hash2[:8]}"
    seed_route(method="GET", path=route1, response_body=f"hash1:{hash1}")

    public_port = free_port()
    admin_port = free_port()
    public_base = f"http://127.0.0.1:{public_port}"
    admin_base = f"http://127.0.0.1:{admin_port}"

    with uvicorn_runner(
        app_ref="reach.core.protocols.http.server:create_public_app",
        host="127.0.0.1",
        port=public_port,
        db_file=db_file,
        repo_root=repo_root,
        ready_url=f"{public_base}/definitely-missing-path",
    ), uvicorn_runner(
        app_ref="reach.core.server:create_admin_app",
        host="127.0.0.1",
        port=admin_port,
        db_file=db_file,
        repo_root=repo_root,
        ready_url=f"{admin_base}/api/health",
    ):
        health = httpx.get(f"{admin_base}/api/health", timeout=5.0)

        list_before = httpx.get(f"{admin_base}/api/routes", timeout=5.0)
        list_before.raise_for_status()
        routes_before = list_before.json()

        create_route2 = httpx.post(
            f"{admin_base}/api/routes",
            json={
                "method": "GET",
                "path": route2,
                "status_code": 200,
                "response_body": f"hash2:{hash2}",
                "content_type": "text/plain",
                "body_encoding": "none",
                "headers": {},
            },
            timeout=5.0,
        )
        create_route2.raise_for_status()
        created_route2 = create_route2.json()

        list_after_create = httpx.get(f"{admin_base}/api/routes", timeout=5.0)
        list_after_create.raise_for_status()
        routes_after_create = list_after_create.json()

        update_route2 = httpx.patch(
            f"{admin_base}/api/routes/{created_route2['id']}",
            json={"method": "POST"},
            timeout=5.0,
        )
        update_route2.raise_for_status()
        updated_route2 = update_route2.json()

        get_old_method = httpx.get(f"{public_base}/{route2}", timeout=5.0)
        post_new_method = httpx.post(f"{public_base}/{route2}", timeout=5.0)

        delete_route2 = httpx.delete(f"{admin_base}/api/routes/{created_route2['id']}", timeout=5.0)

        list_final = httpx.get(f"{admin_base}/api/routes", timeout=5.0)
        list_final.raise_for_status()
        routes_final = list_final.json()

        return {
            "admin_port": admin_port,
            "admin_health_status": health.status_code,
            "route1": route1,
            "route2": route2,
            "hash2": hash2,
            "routes_before": routes_before,
            "create_route2_status": create_route2.status_code,
            "created_route2": created_route2,
            "routes_after_create": routes_after_create,
            "update_route2_status": update_route2.status_code,
            "updated_route2": updated_route2,
            "public_get_after_update_status": get_old_method.status_code,
            "public_post_after_update_status": post_new_method.status_code,
            "public_post_after_update_body": post_new_method.text,
            "delete_route2_status": delete_route2.status_code,
            "routes_final": routes_final,
        }


@pytest.mark.e2e
@pytest.mark.integration
def test_admin_app_starts_on_random_port(admin_crud_trace: AdminCrudTrace) -> None:
    assert 1024 <= admin_crud_trace["admin_port"] <= 65535
    assert admin_crud_trace["admin_health_status"] == 200


@pytest.mark.e2e
@pytest.mark.integration
def test_admin_list_routes_shows_route1(admin_crud_trace: AdminCrudTrace) -> None:
    assert any(
        r["path"] == admin_crud_trace["route1"] and r["method"] == "GET"
        for r in admin_crud_trace["routes_before"]
    )


@pytest.mark.e2e
@pytest.mark.integration
def test_admin_create_route2_with_hash2(admin_crud_trace: AdminCrudTrace) -> None:
    assert admin_crud_trace["create_route2_status"] == 201
    assert admin_crud_trace["created_route2"]["path"] == admin_crud_trace["route2"]
    assert admin_crud_trace["created_route2"]["method"] == "GET"
    assert admin_crud_trace["hash2"] in admin_crud_trace["created_route2"]["response_body"]


@pytest.mark.e2e
@pytest.mark.integration
def test_admin_list_routes_shows_route2(admin_crud_trace: AdminCrudTrace) -> None:
    assert any(
        r["path"] == admin_crud_trace["route2"] and r["method"] == "GET"
        for r in admin_crud_trace["routes_after_create"]
    )


@pytest.mark.e2e
@pytest.mark.integration
def test_admin_updates_route2_method_get_to_post(admin_crud_trace: AdminCrudTrace) -> None:
    assert admin_crud_trace["update_route2_status"] == 200
    assert admin_crud_trace["updated_route2"]["path"] == admin_crud_trace["route2"]
    assert admin_crud_trace["updated_route2"]["method"] == "POST"


@pytest.mark.e2e
@pytest.mark.integration
def test_route2_accessible_with_new_method_and_hash2(admin_crud_trace: AdminCrudTrace) -> None:
    assert admin_crud_trace["public_get_after_update_status"] == 404
    assert admin_crud_trace["public_post_after_update_status"] == 200
    assert admin_crud_trace["hash2"] in admin_crud_trace["public_post_after_update_body"]


@pytest.mark.e2e
@pytest.mark.integration
def test_admin_deletes_route2(admin_crud_trace: AdminCrudTrace) -> None:
    assert admin_crud_trace["delete_route2_status"] == 204


@pytest.mark.e2e
@pytest.mark.integration
def test_admin_final_routes_only_include_route1(admin_crud_trace: AdminCrudTrace) -> None:
    final_keys = {(r["method"], r["path"]) for r in admin_crud_trace["routes_final"]}
    assert final_keys == {("GET", admin_crud_trace["route1"])}
