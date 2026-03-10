from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
import re
import subprocess
from typing import Literal

from rich.console import Console

from reach.forge.exploits import PLUGIN_REGISTRY as EXPLOIT_PLUGIN_REGISTRY
from reach.forge.generators import PLUGIN_REGISTRY as GENERATOR_PLUGIN_REGISTRY

PluginType = Literal["generator", "exploit"]


@dataclass
class DependencyReport:
    kind: str
    plugin_type: str
    requires_python: list[str]
    requires_system: list[str]
    missing_python: list[str]


def _parse_dist_name(requirement: str) -> str:
    token = requirement.strip()
    if not token:
        return ""
    token = re.split(r"[<>=!~\s\[]", token, maxsplit=1)[0]
    return token.strip()


def _registry_for(plugin_type: PluginType) -> dict[str, dict]:
    if plugin_type == "generator":
        return GENERATOR_PLUGIN_REGISTRY
    return EXPLOIT_PLUGIN_REGISTRY


def _selected_kinds(registry: dict[str, dict], kind: str | None, all_kinds: bool) -> list[str]:
    if all_kinds:
        return sorted(registry.keys())
    if not kind:
        raise ValueError("provide --kind <name> or --all")

    normalized = kind.lower()
    if normalized not in registry:
        raise ValueError(f"unknown kind: {kind}")
    return [normalized]


def build_dependency_reports(
    *,
    plugin_type: PluginType,
    kind: str | None,
    all_kinds: bool,
) -> list[DependencyReport]:
    registry = _registry_for(plugin_type)
    kinds = _selected_kinds(registry, kind, all_kinds)

    reports: list[DependencyReport] = []
    for selected_kind in kinds:
        meta = registry[selected_kind]
        requires_python = list(meta.get("requires_python", []))
        requires_system = list(meta.get("requires_system", []))

        missing_python: list[str] = []
        for req in requires_python:
            dist_name = _parse_dist_name(req)
            if not dist_name:
                continue
            try:
                metadata.version(dist_name)
            except metadata.PackageNotFoundError:
                missing_python.append(req)

        reports.append(
            DependencyReport(
                kind=selected_kind,
                plugin_type=plugin_type,
                requires_python=requires_python,
                requires_system=requires_system,
                missing_python=missing_python,
            )
        )

    return reports


def print_dependency_reports(console: Console, reports: list[DependencyReport]) -> bool:
    all_ok = True
    for report in reports:
        console.print(f"[bold]{report.plugin_type}:{report.kind}[/bold]")
        console.print(f"  python deps: {report.requires_python or []}")
        console.print(f"  system deps: {report.requires_system or []}")
        if report.missing_python:
            all_ok = False
            console.print(f"  [red]missing python deps:[/red] {report.missing_python}")
        else:
            console.print("  [green]python deps satisfied[/green]")

        if report.requires_system:
            console.print("  [yellow]system deps require manual validation/install[/yellow]")

    return all_ok


def install_missing_python_dependencies(
    *,
    reports: list[DependencyReport],
    python_bin: str,
    upgrade: bool,
    dry_run: bool,
) -> tuple[list[str], int]:
    missing: list[str] = []
    for report in reports:
        missing.extend(report.missing_python)

    unique_missing = sorted(set(missing))
    if not unique_missing:
        return [], 0

    cmd = [python_bin, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.extend(unique_missing)

    if dry_run:
        return cmd, 0

    completed = subprocess.run(cmd, check=False)
    return cmd, completed.returncode
