from __future__ import annotations

from datetime import UTC, datetime, timedelta
import secrets
import shutil
import subprocess
import time
from typing import Any, TypedDict
import uuid

import httpx
import pytest


class LogsAuditTrace(TypedDict):
    run_id: str
    route1: str
    route2: str
    hash1: str
    hash2: str
    domain: str
    fqdn: str
    created_route2_id: int
    create_route2_status: int
    update_route2_status: int
    delete_route2_status: int
    started_at: datetime
    finished_at: datetime
    direct_route1_status: int
    direct_route1_body: str
    method_switch_status: int
    method_switch_body: str
    domain_curl_returncode: int
    domain_curl_stdout: str
    domain_curl_stderr: str
    logs: list[dict[str, Any]]


def _parse_log_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


@pytest.fixture
def logs_audit_trace(
    repo_root, db_file, db_session_factory, seed_route, free_port, uvicorn_runner, dns_runner, run_id
) -> LogsAuditTrace:
    if shutil.which("dig") is None:
        pytest.skip("dig is required for logs audit test")
    if shutil.which("curl") is None:
        pytest.skip("curl is required for logs audit test")

    hash1 = secrets.token_hex(8)
    hash2 = secrets.token_hex(8)
    route1 = f"log50-r1-{run_id}"
    route2 = f"log50-r2-{run_id}"
    domain = f"log50-{uuid.uuid4().hex}.test"
    fqdn = f"{route1}.{domain}"
    seed_route(method="GET", path=route1, response_body=f"hash1:{hash1}")

    public_port = free_port()
    admin_port = free_port()
    dns_port = free_port()
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
        started_at = datetime.now(UTC)

        httpx.get(f"{admin_base}/api/routes", timeout=5.0).raise_for_status()
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
        route2_id = int(create_route2.json()["id"])

        httpx.get(f"{admin_base}/api/routes", timeout=5.0).raise_for_status()
        update_route2 = httpx.patch(
            f"{admin_base}/api/routes/{route2_id}",
            json={"method": "POST"},
            timeout=5.0,
        )
        update_route2.raise_for_status()

        direct_route1 = httpx.get(f"{public_base}/{route1}", timeout=5.0)
        method_switch_request = httpx.post(f"{public_base}/{route2}", timeout=5.0)
        delete_route2 = httpx.delete(f"{admin_base}/api/routes/{route2_id}", timeout=5.0)
        assert delete_route2.status_code == 204
        httpx.get(f"{admin_base}/api/routes", timeout=5.0).raise_for_status()

        zone_create = httpx.post(
            f"{admin_base}/api/dns/zones",
            json={
                "zone": domain,
                "a": "127.0.0.1",
                "wildcard": True,
                "enabled": True,
            },
            timeout=5.0,
        )
        zone_create.raise_for_status()

        with dns_runner(
            host="127.0.0.1",
            port=dns_port,
            db_file=db_file,
            repo_root=repo_root,
        ):
            dig_cmd = ["dig", "+short", "@127.0.0.1", "-p", str(dns_port), fqdn, "A"]
            for _ in range(30):
                dig_result = subprocess.run(dig_cmd, capture_output=True, text=True, timeout=2, check=False)
                if dig_result.returncode == 0 and "127.0.0.1" in dig_result.stdout:
                    break
                time.sleep(0.2)
            else:
                pytest.fail(f"dig did not resolve expected A record for {fqdn}")

            curl_cmd = [
                "curl",
                "--silent",
                "--show-error",
                "--resolve",
                f"{fqdn}:{public_port}:127.0.0.1",
                f"http://{fqdn}:{public_port}/{route1}",
            ]
            domain_curl = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=5, check=False)

        logs: list[dict[str, Any]] = []
        deadline = time.time() + 6.0
        while time.time() < deadline:
            resp = httpx.get(
                f"{admin_base}/api/logs",
                params={"since_id": 0, "limit": 2000},
                timeout=5.0,
            )
            resp.raise_for_status()
            logs = resp.json()

            has_dns = any(
                (entry.get("protocol") or "").lower() == "dns"
                and domain in (entry.get("path") or "").lower()
                for entry in logs
            )
            has_domain_http = any(
                fqdn in (entry.get("host") or "")
                and (entry.get("protocol") or "").lower() == "http"
                for entry in logs
            )
            if has_dns and has_domain_http:
                break
            time.sleep(0.2)

        finished_at = datetime.now(UTC)

    return {
        "run_id": run_id,
        "route1": route1,
        "route2": route2,
        "hash1": hash1,
        "hash2": hash2,
        "domain": domain,
        "fqdn": fqdn,
        "created_route2_id": route2_id,
        "create_route2_status": create_route2.status_code,
        "update_route2_status": update_route2.status_code,
        "delete_route2_status": delete_route2.status_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "direct_route1_status": direct_route1.status_code,
        "direct_route1_body": direct_route1.text,
        "method_switch_status": method_switch_request.status_code,
        "method_switch_body": method_switch_request.text,
        "domain_curl_returncode": domain_curl.returncode,
        "domain_curl_stdout": domain_curl.stdout,
        "domain_curl_stderr": domain_curl.stderr,
        "logs": logs,
    }


@pytest.mark.e2e
@pytest.mark.integration
def test_logs_include_route1_public_request(logs_audit_trace: LogsAuditTrace) -> None:
    assert logs_audit_trace["direct_route1_status"] == 200
    assert logs_audit_trace["hash1"] in logs_audit_trace["direct_route1_body"]
    route1_hits = [
        entry
        for entry in logs_audit_trace["logs"]
        if (entry.get("protocol") or "").lower() == "http"
        and entry.get("path") == f"/{logs_audit_trace['route1']}"
        and entry.get("status_code") == 200
    ]
    assert route1_hits, "Expected a logged public request for route1"


@pytest.mark.e2e
@pytest.mark.integration
def test_logs_include_route2_crud_and_method_switch_request(logs_audit_trace: LogsAuditTrace) -> None:
    assert logs_audit_trace["create_route2_status"] == 201
    assert logs_audit_trace["update_route2_status"] == 200
    assert logs_audit_trace["delete_route2_status"] == 204
    assert logs_audit_trace["method_switch_status"] == 200
    assert logs_audit_trace["hash2"] in logs_audit_trace["method_switch_body"]
    assert any(
        (entry.get("protocol") or "").lower() == "http"
        and entry.get("method") == "POST"
        and entry.get("path") == f"/{logs_audit_trace['route2']}"
        and entry.get("status_code") == 200
        for entry in logs_audit_trace["logs"]
    )


@pytest.mark.e2e
@pytest.mark.integration
def test_logs_include_dns_query_for_test_domain(logs_audit_trace: LogsAuditTrace) -> None:
    dns_entries = [
        entry
        for entry in logs_audit_trace["logs"]
        if (entry.get("protocol") or "").lower() == "dns"
    ]
    assert dns_entries, "Expected DNS entries in request logs"
    assert any(logs_audit_trace["domain"] in (entry.get("path") or "").lower() for entry in dns_entries)


@pytest.mark.e2e
@pytest.mark.integration
def test_logs_include_http_request_using_domain(logs_audit_trace: LogsAuditTrace) -> None:
    assert logs_audit_trace["domain_curl_returncode"] == 0, logs_audit_trace["domain_curl_stderr"]
    assert logs_audit_trace["hash1"] in logs_audit_trace["domain_curl_stdout"]
    assert any(
        (entry.get("protocol") or "").lower() == "http"
        and logs_audit_trace["fqdn"] in (entry.get("host") or "")
        and entry.get("path") == f"/{logs_audit_trace['route1']}"
        for entry in logs_audit_trace["logs"]
    )


@pytest.mark.e2e
@pytest.mark.integration
def test_logs_have_time_correlation_and_sequence(logs_audit_trace: LogsAuditTrace) -> None:
    margin = timedelta(seconds=10)
    start = logs_audit_trace["started_at"] - margin
    end = logs_audit_trace["finished_at"] + margin

    related = [
        entry
        for entry in logs_audit_trace["logs"]
        if logs_audit_trace["run_id"] in (entry.get("path") or "")
        or logs_audit_trace["run_id"] in (entry.get("host") or "")
        or (
            (entry.get("protocol") or "").lower() == "dns"
            and logs_audit_trace["domain"] in (entry.get("path") or "").lower()
        )
    ]
    assert related, "Expected related log entries to validate timestamp correlation"

    sorted_related = sorted(related, key=lambda item: int(item["id"]))
    timestamps = [_parse_log_ts(str(entry["timestamp"])) for entry in sorted_related]

    assert all(start <= ts <= end for ts in timestamps)
    assert timestamps == sorted(timestamps)


@pytest.mark.e2e
@pytest.mark.integration
def test_logs_are_public_route_focused_without_admin_clutter(logs_audit_trace: LogsAuditTrace) -> None:
    related_http = [
        entry
        for entry in logs_audit_trace["logs"]
        if (entry.get("protocol") or "").lower() == "http"
        and (
            entry.get("path") in {f"/{logs_audit_trace['route1']}", f"/{logs_audit_trace['route2']}"}
            or logs_audit_trace["fqdn"] in (entry.get("host") or "")
        )
    ]
    assert related_http, "Expected public HTTP log evidence for route1/route2/domain-host traffic"
    assert all(not str(entry.get("path") or "").startswith("/api/") for entry in related_http)
