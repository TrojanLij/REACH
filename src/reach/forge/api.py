from dataclasses import dataclass
from typing import Dict, Any

from .generators import xss  # example; later load dynamically

@dataclass
class Payload:
    kind: str
    value: str
    metadata: Dict[str, Any]


def generate_payload(kind: str, **kwargs) -> Payload:
    """
    Core forge API. Does NOT depend on reach.core.
    """
    kind = kind.lower()

    if kind == "xss_basic":
        value = xss.basic_reflected(**kwargs)
        return Payload(kind="xss_basic", value=value, metadata={"family": "xss"})

    # later: other kinds, registry pattern, plugins, etc.
    raise ValueError(f"Unknown payload kind: {kind!r}")


class ForgeController:
    """
    Optional helper that integrates forge with REACH Core.
    It uses reach.core.CoreClient to persist generated payloads, etc.
    """

    def __init__(self, core_client):
        self.core_client = core_client

    def create_and_store_payload(self, kind: str, **kwargs) -> Dict[str, Any]:
        payload = generate_payload(kind, **kwargs)
        body = {
            "kind": payload.kind,
            "value": payload.value,
            "metadata": payload.metadata,
        }
        # uses Core REST API
        stored = self.core_client.save_payload(body)
        return stored
