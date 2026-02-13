from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from typing import Iterator

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from reach.core.db.base import Base
from reach.core.db.models import Route


def find_free_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    except PermissionError:
        pytest.skip("Local socket bind is not permitted in this environment")


def wait_for_http(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=0.8)
            if response.status_code < 500:
                return
        except Exception as exc:
            last_error = exc
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for server at {url}: {last_error}")


def wait_for_process_start(proc: subprocess.Popen[str], timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            output = ""
            if proc.stdout is not None:
                output = proc.stdout.read() or ""
            raise RuntimeError(f"Process exited during startup. Output:\n{output}")
        time.sleep(0.1)


def wait_for_dns(host: str, port: int, timeout: float = 8.0) -> None:
    from dnslib import DNSRecord

    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            query = DNSRecord.question("probe.local", qtype="A")
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(0.8)
                sock.sendto(query.pack(), (host, port))
                payload, _ = sock.recvfrom(2048)
            response = DNSRecord.parse(payload)
            if response.header.id == query.header.id:
                return
        except Exception as exc:
            last_error = exc
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for DNS server at {host}:{port}: {last_error}")


@contextmanager
def run_uvicorn_app(
    *,
    app_ref: str,
    host: str,
    port: int,
    db_file: Path,
    repo_root: Path,
    ready_url: str,
) -> Iterator[subprocess.Popen[str]]:
    env = os.environ.copy()
    env["REACH_DB_FILE"] = str(db_file)
    env["PYTHONPATH"] = f"{repo_root / 'src'}:{env.get('PYTHONPATH', '')}"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            app_ref,
            "--factory",
            "--host",
            host,
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_http(ready_url, timeout=12)
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@contextmanager
def run_dns_server(
    *,
    host: str,
    port: int,
    db_file: Path,
    repo_root: Path,
) -> Iterator[subprocess.Popen[str]]:
    env = os.environ.copy()
    env["REACH_DB_FILE"] = str(db_file)
    env["PYTHONPATH"] = f"{repo_root / 'src'}:{env.get('PYTHONPATH', '')}"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "reach.dns.server",
            "--host",
            host,
            "--port",
            str(port),
            "--zones-refresh",
            "0.2",
            "--log-level",
            "warning",
        ],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_process_start(proc, timeout=4.0)
        wait_for_dns(host, port, timeout=8.0)
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture
def db_file(tmp_path: Path) -> Path:
    return tmp_path / "reach_e2e.db"


@pytest.fixture
def db_session_factory(db_file: Path):
    engine = create_engine(
        f"sqlite:///{db_file}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def run_id() -> str:
    return secrets.token_hex(4)


@pytest.fixture
def seed_route(db_session_factory):
    def _seed(
        *,
        method: str,
        path: str,
        response_body: str,
        status_code: int = 200,
        content_type: str = "text/plain",
    ) -> Route:
        with db_session_factory() as session:
            route = Route(
                method=method.upper(),
                path=path.lstrip("/"),
                status_code=status_code,
                response_body=response_body,
                content_type=content_type,
                body_encoding="none",
            )
            route.set_headers({})
            session.add(route)
            session.commit()
            session.refresh(route)
            return route

    return _seed


@pytest.fixture
def free_port():
    return find_free_port


@pytest.fixture
def uvicorn_runner():
    return run_uvicorn_app


@pytest.fixture
def dns_runner():
    return run_dns_server
