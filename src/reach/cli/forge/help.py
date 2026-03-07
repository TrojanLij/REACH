from __future__ import annotations

import inspect
from textwrap import dedent

import typer
from rich.console import Console
from rich.table import Table

from reach.forge.generators import REGISTRY
from reach.forge.exploits import REGISTRY as EXPLOIT_REGISTRY


def _render_kind_details(kind: str, fn: object, type_label: str) -> None:
    console = Console()
    sig = inspect.signature(fn)
    raw_doc = dedent(getattr(fn, "__doc__", "") or "").strip()
    doc_lines = raw_doc.splitlines()
    doc = "\n".join(doc_lines).strip()

    param_desc: dict[str, str] = {}
    if "Params:" in doc_lines:
        params_start = doc_lines.index("Params:")
        for line in doc_lines[params_start + 1 :]:
            line = line.strip()
            if not line or line.lower().startswith("returns"):
                break
            if line.startswith("-"):
                try:
                    name_part, desc_part = line[1:].split(":", 1)
                    param_desc[name_part.strip()] = desc_part.strip()
                except ValueError:
                    continue

    console.print(f"[bold]{kind}[/bold]  [dim]{type_label} | {fn.__module__}:{fn.__name__}[/dim]")
    if doc:
        console.print(doc)

    table = Table(title="Parameters", show_lines=False, header_style="bold")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="white", no_wrap=True)
    table.add_column("Default", style="magenta")
    table.add_column("Description", style="white")

    for name, param in sig.parameters.items():
        default = "required" if param.default is inspect._empty else repr(param.default)
        annot = ""
        if param.annotation is not inspect._empty:
            annot = getattr(param.annotation, "__name__", str(param.annotation))
        desc = param_desc.get(name, "")
        table.add_row(name, annot, default, desc)

    console.print(table)


def forge_list_catalog(kind: str | None = None) -> None:
    """
    Show cross-compatible Forge kinds across generators/exploits.
    """
    console = Console()
    entries: list[tuple[str, str, object]] = []
    for name, fn in sorted(REGISTRY.items()):
        entries.append((name, "generator", fn))
        entries.append((name, "payload-alias", fn))
    for name, fn in sorted(EXPLOIT_REGISTRY.items()):
        entries.append((name, "exploit", fn))

    if kind is None:
        table = Table(title="Forge Kinds")
        table.add_column("Kind", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Summary", style="white")
        table.add_column("Location", style="dim")
        for name, type_label, fn in sorted(entries, key=lambda x: (x[0], x[1])):
            doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
            location = inspect.getsourcefile(fn) or inspect.getfile(fn)
            table.add_row(name, type_label, doc, location)
        console.print(table)
        return

    normalized = kind.lower()
    matches = [entry for entry in entries if entry[0] == normalized]
    if not matches:
        all_kinds = sorted(set([name for name, _, _ in entries]))
        console.print(f"[red]Unknown forge kind:[/red] {kind}")
        console.print("Available kinds: " + ", ".join(all_kinds))
        raise typer.Exit(code=1)

    for name, type_label, fn in matches:
        _render_kind_details(name, fn, type_label)


def forge_list_generators(kind: str | None = None) -> None:
    """
    Show help/usage for Forge generators.
    """
    console = Console()

    if kind is None:
        table = Table(title="Forge Generator Kinds")
        table.add_column("Kind", style="cyan")
        table.add_column("Summary", style="white")
        table.add_column("Location", style="dim")
        for name, fn in sorted(REGISTRY.items()):
            doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
            location = inspect.getsourcefile(fn) or inspect.getfile(fn)
            table.add_row(name, doc, location)
        console.print(table)
        return

    kind = kind.lower()
    if kind not in REGISTRY:
        console.print(f"[red]Unknown generator kind:[/red] {kind}")
        console.print("Available kinds: " + ", ".join(sorted(REGISTRY.keys())))
        raise typer.Exit(code=1)

    _render_kind_details(kind, REGISTRY[kind], "generator")


def forge_list_payloads(kind: str | None = None) -> None:
    """
    Backward-compatible alias for forge_list_generators.
    """
    forge_list_generators(kind=kind)


def forge_list_exploits(kind: str | None = None) -> None:
    """
    Show help/usage for Forge exploit modules.
    """
    console = Console()

    if kind is None:
        table = Table(title="Forge Exploit Kinds")
        table.add_column("Kind", style="cyan")
        table.add_column("Summary", style="white")
        table.add_column("Location", style="dim")
        for name, fn in sorted(EXPLOIT_REGISTRY.items()):
            doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
            location = inspect.getsourcefile(fn) or inspect.getfile(fn)
            table.add_row(name, doc, location)
        console.print(table)
        return

    kind = kind.lower()
    if kind not in EXPLOIT_REGISTRY:
        console.print(f"[red]Unknown exploit kind:[/red] {kind}")
        console.print("Available kinds: " + ", ".join(sorted(EXPLOIT_REGISTRY.keys())))
        raise typer.Exit(code=1)

    _render_kind_details(kind, EXPLOIT_REGISTRY[kind], "exploit")
