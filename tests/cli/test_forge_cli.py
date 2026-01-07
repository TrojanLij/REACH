from __future__ import annotations

import re

from typer.testing import CliRunner

from reach.cli.main import app


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _run_cli(args: list[str]) -> tuple[int, str]:
    runner = CliRunner()
    result = runner.invoke(app, args, env={"TERM": "dumb"})
    return result.exit_code, _strip_ansi(result.output)


def test_forge_list_payloads() -> None:
    code, output = _run_cli(["forge", "--list"])
    assert code == 0
    assert "Forge Payload Kinds" in output
    assert "xss_gh0st" in output


def test_forge_list_payload_kind_details() -> None:
    code, output = _run_cli(["forge", "--list", "--kind", "xss_gh0st"])
    assert code == 0
    assert "xss_gh0st" in output
    assert "Parameters" in output
    assert "command" in output


def test_forge_payload_new_dry_run() -> None:
    code, output = _run_cli(
        ["forge", "payload", "new", "xss_gh0st", "--dry-run", "--payload-kwarg", "command=id"]
    )
    assert code == 0
    assert "Payload (xss_gh0st):" in output
    assert "fn('id')" in output


def test_forge_payload_new_requires_endpoint_without_dry_run() -> None:
    code, output = _run_cli(["forge", "payload", "new", "xss_gh0st"])
    assert code != 0
    assert "Missing --endpoint" in output
