import os
from typing import Any, Dict, Optional

import requests


class MCPHttpClient:
    """
    Простейший HTTP‑клиент для MCP сервера.
    Предполагается REST‑обёртка с эндпоинтами:
      - GET  /capabilities
      - GET  /tools/list
      - POST /tools/call  (json: { name: string, arguments: object })
    Токен GitHub пробрасывается в заголовке Authorization: Bearer <token> (если задан).
    """

    def __init__(self, base_url: str, github_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if github_token:
            self.session.headers.update({"Authorization": f"Bearer {github_token}"})

    def _get_first_ok(self, paths: list[str]) -> Dict[str, Any]:
        last_exc: Exception | None = None
        for p in paths:
            try:
                resp = self.session.get(f"{self.base_url}{p}", timeout=30)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        raise RuntimeError("No endpoints responded")

    def _post_first_ok(self, paths: list[str], json_payload: Dict[str, Any]) -> Dict[str, Any]:
        last_exc: Exception | None = None
        for p in paths:
            try:
                resp = self.session.post(f"{self.base_url}{p}", json=json_payload, timeout=60)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        raise RuntimeError("No endpoints responded")

    def capabilities(self) -> Dict[str, Any]:
        return self._get_first_ok(["/capabilities", "/v1/capabilities", "/mcp/capabilities"])

    def tools_list(self) -> Dict[str, Any]:
        return self._get_first_ok(["/tools/list", "/v1/tools/list", "/mcp/tools/list"])

    def tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"name": name, "arguments": arguments}
        # Строгий режим под локальный сервер: используем только /tools/call
        return self._post_first_ok(["/tools/call"], payload)


