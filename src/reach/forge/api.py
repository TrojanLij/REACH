from dataclasses import dataclass
import inspect
from typing import Any, Dict

from .exploits import REGISTRY as EXPLOIT_REGISTRY
from .generators import REGISTRY


@dataclass
class GeneratorOutput:
    kind: str
    value: str
    metadata: Dict[str, Any]


# Backward-compat alias for existing imports.
Payload = GeneratorOutput


@dataclass
class ExploitExecution:
    kind: str
    output: Any
    metadata: Dict[str, Any]


def generate_generator(kind: str, **kwargs) -> GeneratorOutput:
    """
    Core forge generator API. Does NOT depend on reach.core.
    """
    kind = kind.lower()

    if kind not in REGISTRY:
        raise ValueError(f"Unknown generator kind: {kind!r}")

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
        raise ValueError(f"Missing required generator params: {missing_list}")

    # If the generator accepts **kwargs, pass everything; otherwise filter to known params.
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        call_kwargs = kwargs
    else:
        call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

    value = fn(**call_kwargs)
    family = kind.split("_", 1)[0] if "_" in kind else kind
    return GeneratorOutput(kind=kind, value=value, metadata={"family": family})


def generate_payload(kind: str, **kwargs) -> GeneratorOutput:
    """
    Backward-compatible alias for generate_generator.
    """
    return generate_generator(kind, **kwargs)


def execute_exploit(kind: str, **kwargs) -> ExploitExecution:
    """
    Execute a forge exploit module.
    """
    kind = kind.lower()

    if kind not in EXPLOIT_REGISTRY:
        raise ValueError(f"Unknown exploit kind: {kind!r}")

    fn = EXPLOIT_REGISTRY[kind]
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
        raise ValueError(f"Missing required exploit params: {missing_list}")

    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        call_kwargs = kwargs
    else:
        call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

    output = fn(**call_kwargs)
    family = kind.split("_", 1)[0] if "_" in kind else kind
    return ExploitExecution(kind=kind, output=output, metadata={"family": family})


class ForgeController:
    """
    Optional helper that integrates forge with REACH Core.
    It uses reach.core.CoreClient to persist generated output, etc.
    """

    def __init__(self, core_client):
        self.core_client = core_client

    def create_and_store_generator(self, kind: str, **kwargs) -> Dict[str, Any]:
        output = generate_generator(kind, **kwargs)
        body = {
            "kind": output.kind,
            "value": output.value,
            "metadata": output.metadata,
        }
        stored = self.core_client.save_payload(body)
        return stored

    def create_and_store_payload(self, kind: str, **kwargs) -> Dict[str, Any]:
        """
        Backward-compatible alias for create_and_store_generator.
        """
        return self.create_and_store_generator(kind, **kwargs)

    def create_route_with_generator(
        self,
        *,
        kind: str,
        path: str,
        method: str = "GET",
        status_code: int = 200,
        content_type: str = "text/html",
        headers: Dict[str, Any] | None = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate output and create a dynamic route serving it via the admin API.
        """
        output = generate_generator(kind, **kwargs)

        normalized_path = path.lstrip("/")
        normalized_headers = {str(k): str(v) for k, v in (headers or {}).items()}

        route_body = {
            "method": method.upper(),
            "path": normalized_path,
            "status_code": status_code,
            "response_body": output.value,
            "content_type": content_type,
            "body_encoding": "none",
            "headers": normalized_headers,
        }

        created_route = self.core_client.create_route(route_body)
        return {"route": created_route, "generator": output}

    def create_route_with_payload(
        self,
        *,
        kind: str,
        path: str,
        method: str = "GET",
        status_code: int = 200,
        content_type: str = "text/html",
        headers: Dict[str, Any] | None = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Backward-compatible alias for create_route_with_generator.
        """
        result = self.create_route_with_generator(
            kind=kind,
            path=path,
            method=method,
            status_code=status_code,
            content_type=content_type,
            headers=headers,
            **kwargs,
        )
        result["payload"] = result["generator"]
        return result
