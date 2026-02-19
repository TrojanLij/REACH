"""Admin API for plugin discovery and management."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from fastapi import APIRouter, HTTPException

from ..db.schemas import (
    PluginFilterOut,
    PluginFilterSourceOut,
    PluginFilterTestRequest,
    PluginFilterTestResponse,
)
from ..routing.filters import FILTERS
from ..routing.dynamic import _render_template

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


def _classify_filter_source(fn: Callable[..., str]) -> str:
    module_name = getattr(fn, "__module__", "")
    file_path = getattr(fn, "__code__", None)
    filename = file_path.co_filename if file_path else ""
    if ".routing.filters." in module_name:
        return "builtin"
    if "plugins/IFTTT/filters/" in filename.replace("\\", "/"):
        return "external"
    return "unknown"


def _filter_file_path(fn: Callable[..., str]) -> Path | None:
    file_path = getattr(getattr(fn, "__code__", None), "co_filename", None)
    if not isinstance(file_path, str) or not file_path.strip():
        return None
    try:
        return Path(file_path).resolve()
    except Exception:
        return None


def _allowed_filter_roots() -> list[Path]:
    roots: list[Path] = []
    roots.append((Path.cwd() / "src" / "reach" / "core" / "routing" / "filters").resolve())
    roots.append((Path.cwd() / "plugins" / "IFTTT" / "filters").resolve())
    roots.append((Path.home() / ".reach" / "plugins" / "IFTTT" / "filters").resolve())
    return roots


def _is_allowed_filter_path(path: Path) -> bool:
    for root in _allowed_filter_roots():
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


@router.get("/ifttt/filters", response_model=list[PluginFilterOut])
def list_ifttt_filters() -> list[PluginFilterOut]:
    """Return loaded IFTTT filter plugins with lightweight metadata."""
    items: list[PluginFilterOut] = []
    for name, fn in sorted(FILTERS.items(), key=lambda entry: entry[0]):
        module_name = getattr(fn, "__module__", "")
        file_path = _filter_file_path(fn)
        normalized_file = None
        if file_path is not None:
            normalized_file = str(file_path)
        items.append(
            PluginFilterOut(
                name=name,
                source=_classify_filter_source(fn),
                module=module_name or "unknown",
                file=normalized_file,
            )
        )
    return items


@router.get("/ifttt/filters/{filter_name}/source", response_model=PluginFilterSourceOut)
def get_ifttt_filter_source(filter_name: str) -> PluginFilterSourceOut:
    """Return source code for one loaded IFTTT filter."""
    fn = FILTERS.get(filter_name)
    if fn is None:
        raise HTTPException(status_code=404, detail="Filter not found")

    path = _filter_file_path(fn)
    if path is None:
        raise HTTPException(status_code=404, detail="Filter source file not available")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Filter source file not found")
    if not _is_allowed_filter_path(path):
        raise HTTPException(status_code=403, detail="Filter source path is not allowed")

    try:
        code = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read filter source: {exc}") from exc

    return PluginFilterSourceOut(
        name=filter_name,
        source=_classify_filter_source(fn),
        file=str(path),
        code=code,
    )


@router.post("/ifttt/filters/test", response_model=PluginFilterTestResponse)
def test_ifttt_filter_expression(payload: PluginFilterTestRequest) -> PluginFilterTestResponse:
    """Evaluate a template/filter expression against mock context data."""
    expression = payload.expression.strip()
    if not expression:
        raise HTTPException(status_code=400, detail="Expression cannot be empty")

    # Convenience: allow bare expressions like `body|json_get:foo` without braces.
    if "{{" in expression and "}}" in expression:
        template = expression
    else:
        template = "{{ " + expression + " }}"

    try:
        result = _render_template(template, payload.context)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to evaluate expression: {exc}") from exc

    return PluginFilterTestResponse(template=template, result=result)
