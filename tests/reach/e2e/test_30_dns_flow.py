from __future__ import annotations

import re
import secrets
import shutil
import subprocess
import time
from typing import Any, TypedDict
import uuid

import httpx
import pytest


class DnsFlowTrace(TypedDict):
    dns_port: int
    dns_domain: str
    dns_hash: str
    route1: str
    hash1: str
    fqdn: str
    zone_create_status: int
    aaaa_answer: str
    recovered_dns_hash: str
    curl_returncode: int
    curl_stdout: str
    curl_stderr: str


def _token_to_ipv6(token: str) -> str:
    # 32 hex chars -> 8 groups of 4 chars
    return ":".join(token[i : i + 4] for i in range(0, 32, 4))


def _ipv6_to_token(ipv6: str) -> str:
    groups = ipv6.split(":")
    expanded = []
    for group in groups:
        if not group:
            continue
        expanded.append(group.zfill(4))
    return "".join(expanded).lower()


def _extract_first_ipv6(text: str) -> str | None:
    match = re.search(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", text)
    return match.group(0) if match else None


@pytest.fixture
def dns_flow_trace(
    repo_root, db_file, db_session_factory, seed_route, free_port, uvicorn_runner, dns_runner, run_id
) -> DnsFlowTrace:
    if shutil.which("dig") is None:
        pytest.skip("dig is required for DNS flow test")
    if shutil.which("curl") is None:
        pytest.skip("curl is required for DNS flow test")

    hash1 = secrets.token_hex(8)
    dns_hash = secrets.token_hex(16)
    route1 = f"route-{run_id}-{hash1[:8]}"
    dns_domain = f"dns-{run_id}-{uuid.uuid4().hex}.test"
    fqdn = f"{route1}.{dns_domain}"
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
        zone_create = httpx.post(
            f"{admin_base}/api/dns/zones",
            json={
                "zone": dns_domain,
                "a": "127.0.0.1",
                "aaaa": _token_to_ipv6(dns_hash),
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
            dig_cmd = [
                "dig",
                "+short",
                "@127.0.0.1",
                "-p",
                str(dns_port),
                fqdn,
                "AAAA",
            ]
            aaaa_output = ""
            for _ in range(30):
                dig_result = subprocess.run(dig_cmd, capture_output=True, text=True, timeout=2, check=False)
                aaaa_output = dig_result.stdout.strip()
                ipv6_answer = _extract_first_ipv6(aaaa_output)
                if dig_result.returncode == 0 and ipv6_answer:
                    break
                time.sleep(0.2)
            else:
                pytest.fail(f"dig AAAA did not return an answer: {aaaa_output!r}")

            ipv6_answer = _extract_first_ipv6(aaaa_output)
            assert ipv6_answer is not None
            recovered_dns_hash = _ipv6_to_token(ipv6_answer)

            curl_cmd = [
                "curl",
                "--silent",
                "--show-error",
                "--resolve",
                f"{fqdn}:{public_port}:127.0.0.1",
                f"http://{fqdn}:{public_port}/{route1}",
            ]
            curl_result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=5, check=False)

        return {
            "dns_port": dns_port,
            "dns_domain": dns_domain,
            "dns_hash": dns_hash,
            "route1": route1,
            "hash1": hash1,
            "fqdn": fqdn,
            "zone_create_status": zone_create.status_code,
            "aaaa_answer": ipv6_answer,
            "recovered_dns_hash": recovered_dns_hash,
            "curl_returncode": curl_result.returncode,
            "curl_stdout": curl_result.stdout,
            "curl_stderr": curl_result.stderr,
        }


@pytest.mark.e2e
@pytest.mark.integration
def test_dns_server_starts_on_random_port(dns_flow_trace: DnsFlowTrace) -> None:
    assert 1024 <= dns_flow_trace["dns_port"] <= 65535


@pytest.mark.e2e
@pytest.mark.integration
def test_dns_flow_uses_random_domain_and_hash(dns_flow_trace: DnsFlowTrace) -> None:
    assert dns_flow_trace["dns_domain"].endswith(".test")
    assert len(dns_flow_trace["dns_hash"]) == 32


@pytest.mark.e2e
@pytest.mark.integration
def test_dig_recovers_dns_hash_from_record(dns_flow_trace: DnsFlowTrace) -> None:
    assert dns_flow_trace["aaaa_answer"]
    assert dns_flow_trace["recovered_dns_hash"] == dns_flow_trace["dns_hash"]


@pytest.mark.e2e
@pytest.mark.integration
def test_dns_record_is_tied_to_route1_domain(dns_flow_trace: DnsFlowTrace) -> None:
    assert dns_flow_trace["zone_create_status"] == 201
    assert dns_flow_trace["fqdn"].startswith(f"{dns_flow_trace['route1']}.")


@pytest.mark.e2e
@pytest.mark.integration
def test_curl_domain_route_returns_hash1(dns_flow_trace: DnsFlowTrace) -> None:
    assert dns_flow_trace["curl_returncode"] == 0, dns_flow_trace["curl_stderr"]
    assert dns_flow_trace["hash1"] in dns_flow_trace["curl_stdout"]
