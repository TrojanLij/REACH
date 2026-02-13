from __future__ import annotations

from pathlib import Path
import re
import select
import secrets
import shutil
import socket
import subprocess
import sys
import time
import uuid

import pytest


def _should_log(request: pytest.FixtureRequest) -> bool:
    return request.config.getoption("verbose") > 0 or request.config.getoption("capture") == "no"


def _log(request: pytest.FixtureRequest, message: str) -> None:
    if not _should_log(request):
        return
    terminal_reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter is not None:
        terminal_reporter.write_line(f"[dns-test] {message}")
    else:
        print(f"[dns-test] {message}")


def _free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _token_to_ipv4(token: str) -> str:
    # 8 hex chars -> 4 octets
    return ".".join(str(int(token[i : i + 2], 16)) for i in range(0, 8, 2))


def _ipv4_to_token(ipv4: str) -> str:
    return "".join(f"{int(part):02x}" for part in ipv4.split("."))


def _extract_first_ipv4(text: str) -> str | None:
    match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    return match.group(0) if match else None


def _wait_for_server_ready(
    *,
    request: pytest.FixtureRequest,
    proc: subprocess.Popen[str],
    ready_text: str,
    timeout: float = 5.0,
) -> None:
    if proc.stdout is None:
        pytest.fail("DNS server stdout is unavailable")

    deadline = time.time() + timeout
    collected: list[str] = []
    while time.time() < deadline:
        if proc.poll() is not None:
            remaining = proc.stdout.read()
            output = "".join(collected) + (remaining or "")
            pytest.fail(f"DNS server exited before ready. Output:\n{output}")

        ready, _, _ = select.select([proc.stdout], [], [], 0.2)
        if not ready:
            continue

        line = proc.stdout.readline()
        if not line:
            continue

        collected.append(line)
        stripped = line.strip()
        _log(request, f"server: {stripped}")
        if ready_text in stripped:
            return

    output = "".join(collected)
    pytest.fail(f"Timed out waiting for server startup line: {ready_text!r}. Output:\n{output}")


def test_dns_server_dig_returns_matching_verification_token(request: pytest.FixtureRequest) -> None:
    if shutil.which("dig") is None:
        pytest.skip("dig is required for this integration test")

    repo_root = Path(__file__).resolve().parents[3]
    server_script = repo_root / "scripts" / "dns_test_server.py"
    assert server_script.exists(), f"Missing DNS test server script: {server_script}"
    
    verification_token = secrets.token_hex(4)
    fake_domain = f"{uuid.uuid4().hex}.test"
    query_name = f"{verification_token}.{fake_domain}"
    encoded_ip = _token_to_ipv4(verification_token)
    port = _free_udp_port()
    _log(
        request,
        (
            f"token={verification_token} domain={fake_domain} query={query_name} "
            f"encoded_ip={encoded_ip} port={port}"
        ),
    )

    server_proc = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(server_script),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--domain",
            fake_domain,
            "--a",
            encoded_ip,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    dig_cmd = [
        "dig",
        "+short",
        "@127.0.0.1",
        "-p",
        str(port),
        query_name,
        "A",
    ]

    dig_stdout = ""
    try:
        _log(request, f"starting DNS test server: {server_script}")
        _wait_for_server_ready(
            request=request,
            proc=server_proc,
            ready_text=f"listening on 127.0.0.1:{port} for domain {fake_domain}",
        )
        deadline = time.time() + 10
        while time.time() < deadline:
            if server_proc.poll() is not None:
                server_output = ""
                if server_proc.stdout is not None:
                    server_output = server_proc.stdout.read()
                pytest.fail(f"DNS server exited early. Output:\n{server_output}")

            result = subprocess.run(dig_cmd, capture_output=True, text=True, timeout=2, check=False)
            dig_stdout = result.stdout.strip()
            _log(
                request,
                f"dig returncode={result.returncode} stdout={dig_stdout!r} stderr={result.stderr.strip()!r}",
            )
            if result.returncode == 0 and dig_stdout:
                break
            time.sleep(0.2)
        else:
            pytest.fail(f"dig returned no answer before timeout. Last stdout={dig_stdout!r}")

        ipv4_answer = _extract_first_ipv4(dig_stdout)
        assert ipv4_answer is not None, f"No A record found in dig output: {dig_stdout!r}"
        _log(request, f"ipv4_answer={ipv4_answer}")

        received_token = _ipv4_to_token(ipv4_answer)
        _log(request, f"decoded_token={received_token}")
        assert received_token == verification_token
    finally:
        _log(request, "stopping DNS test server")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
            server_proc.wait(timeout=3)
