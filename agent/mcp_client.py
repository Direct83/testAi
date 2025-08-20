import os, json, subprocess, threading, queue, uuid, sys, time
from typing import Any, Dict, Optional

# Минимальный MCP-клиент по stdio с корректным handshake (initialize → initialized),
# tools/list и tools/call.

class MCPClient:
    def __init__(self, command: str, args: list[str], env: Optional[Dict[str, str]] = None):
        env_all = os.environ.copy()
        if env:
            env_all.update(env)
        self.proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if not self.proc.stdin or not self.proc.stdout:
            raise RuntimeError("Failed to start MCP server process")
        self._q: "queue.Queue[dict]" = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._id = 0
        self._initialized = False
        self.initialize()

    def _read_loop(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                self._q.put(msg)
            except Exception:
                # Пропускаем лог-строки
                pass

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _rpc(self, method: str, params: Optional[dict] = None, timeout: float = 30.0) -> dict:
        rid = self._next_id()
        req = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            req["params"] = params
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()

        # Ждём ответ с нужным id
        start = time.time()
        while time.time() - start < timeout:
            try:
                msg = self._q.get(timeout=timeout)
            except queue.Empty:
                break
            if msg.get("id") == rid:
                if "error" in msg and msg["error"]:
                    raise RuntimeError(str(msg["error"]))
                return msg.get("result", {})
        raise TimeoutError(f"MCP request timeout: {method}")

    def initialize(self):
        # Handshake согласно спецификации MCP.
        _ = self._rpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {},
            },
            "clientInfo": {"name": "workflow-agent", "version": "1.0.0"},
        })
        # Отправляем уведомление initialized
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        self.proc.stdin.flush()
        self._initialized = True

    def tools_list(self) -> dict:
        return self._rpc("tools/list", {})

    def tools_call(self, name: str, arguments: dict) -> dict:
        return self._rpc("tools/call", {"name": name, "arguments": arguments})

    def close(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass


