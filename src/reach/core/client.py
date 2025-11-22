import httpx
from typing import Optional, Any, Dict, List

class CoreClient:
    """
    Thin client for REACH Core's REST API.

    This is what forge, cli, and external plugins should use.
    """

    def __init__(self, base_url: str, token: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # --- Example core API methods ---

    def list_routes(self) -> List[Dict[str, Any]]:
        resp = httpx.get(
            f"{self.base_url}/api/routes",
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def create_route(self, route: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.post(
            f"{self.base_url}/api/routes",
            json=route,
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def save_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.post(
            f"{self.base_url}/api/payloads",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()
