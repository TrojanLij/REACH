"""Protocol registry for REACH Core."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict


@dataclass(frozen=True)
class ProtocolRegistration:
    name: str
    public_app: str
    init_db: Callable[[], None] | None = None
    description: str | None = None
    server_type: str = "asgi"
    run: Callable[[str, int], None] | None = None


_REGISTRY: Dict[str, ProtocolRegistration] = {}


def register_protocol(
    name: str,
    *,
    public_app: str,
    init_db: Callable[[], None] | None = None,
    description: str | None = None,
    server_type: str = "asgi",
    run: Callable[[str, int], None] | None = None,
) -> None:
    key = name.lower()
    _REGISTRY[key] = ProtocolRegistration(
        name=key,
        public_app=public_app,
        init_db=init_db,
        description=description,
        server_type=server_type,
        run=run,
    )


def get_protocol(name: str) -> ProtocolRegistration:
    key = name.lower()
    if key not in _REGISTRY:
        raise KeyError(f"Unknown protocol: {name}")
    return _REGISTRY[key]


def list_protocols() -> Dict[str, ProtocolRegistration]:
    return dict(_REGISTRY)
