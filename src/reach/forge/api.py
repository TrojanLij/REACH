from dataclasses import dataclass
import inspect
from typing import Dict, Any

from .generators import REGISTRY


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

    if kind not in REGISTRY:
        raise ValueError(f"Unknown payload kind: {kind!r}")

    fn = REGISTRY[kind]
    sig = inspect.signature(fn)

    required_params = [
        name
        for name, param in sig.parameters.items()
        if param.default is inspect._empty
        and param.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]
    missing = [name for name in required_params if name not in kwargs]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Missing required payload params: {missing_list}")

    # If the generator accepts **kwargs, pass everything; otherwise filter to known params.
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        call_kwargs = kwargs
    else:
        call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

    value = fn(**call_kwargs)
    # Simple family grouping: everything before first "_" is family
    family = kind.split("_", 1)[0] if "_" in kind else kind
    return Payload(kind=kind, value=value, metadata={"family": family})


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

    def create_route_with_payload(
        self,
        *,
        kind: str,
        path: str,
        method: str = "GET",
        status_code: int = 200,
        content_type: str = "text/html",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a payload and create a dynamic route serving it via the admin API.
        """
        payload = generate_payload(kind, **kwargs)

        # Normalize path: admin API expects no leading slash
        normalized_path = path.lstrip("/")

        route_body = {
            "method": method.upper(),
            "path": normalized_path,
            "status_code": status_code,
            "response_body": payload.value,
            "content_type": content_type,
            "body_encoding": "none",
        }

        created_route = self.core_client.create_route(route_body)
        return {"route": created_route, "payload": payload}
