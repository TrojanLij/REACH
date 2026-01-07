from __future__ import annotations

import inspect
from textwrap import dedent

import typer
from rich.console import Console
from rich.table import Table

from reach.forge.generators import REGISTRY


def forge_list_payloads(kind: str | None = None) -> None:
    """
    Show help/usage for Forge payload generators.
    """
    console = Console()

    if kind is None:
        table = Table(title="Forge Payload Kinds")
        table.add_column("Kind", style="cyan")
        table.add_column("Summary", style="white")
        for name, fn in sorted(REGISTRY.items()):
            doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
            table.add_row(name, doc)
        console.print(table)
        return

    kind = kind.lower()
    if kind not in REGISTRY:
        console.print(f"[red]Unknown payload kind:[/red] {kind}")
        console.print("Available kinds: " + ", ".join(sorted(REGISTRY.keys())))
        raise typer.Exit(code=1)

    fn = REGISTRY[kind]
    sig = inspect.signature(fn)
    raw_doc = dedent(fn.__doc__ or "").strip()
    doc_lines = raw_doc.splitlines()
    doc = "\n".join(doc_lines).strip()

    # crude parse of "Params:" section for descriptions
    param_desc: dict[str, str] = {}
    if "Params:" in doc_lines:
        params_start = doc_lines.index("Params:")
        for line in doc_lines[params_start + 1 :]:
            line = line.strip()
            if not line or line.lower().startswith("returns"):
                break
            if line.startswith("-"):
                # "- name: description"
                try:
                    name_part, desc_part = line[1:].split(":", 1)
                    param_desc[name_part.strip()] = desc_part.strip()
                except ValueError:
                    continue

    console.print(f"[bold]{kind}[/bold]  [dim]{fn.__module__}:{fn.__name__}[/dim]")
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
