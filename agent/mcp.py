import json, os, subprocess, threading, queue, uuid, sys
from typing import Any, Dict, Optional

class MCPProcess:
    """
    Минимальный клиент JSON-RPC по stdио для @modelcontextprotocol/server-bash,
    которого мы запускаем через npx. Метод call(method, params) возвращает result.
    """
    def __init__(self, command: str, args: list[str], env: Optional[Dict[str,str]] = None):
        env_all = os.environ.copy()
        if env:
            env_all.update(env)
        self.proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,  # бинарный режим для корректного чтения Content-Length
            bufsize=0,
            env=env_all
        )
        self._q = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self):
        assert self.proc.stdout is not None
        stdout = self.proc.stdout
        while True:
            line = stdout.readline()
            if not line:
                return
            # Пропускаем любой нефреймированный вывод (npm/npx логи и т.п.)
            if not line.lower().startswith(b"content-length:"):
                try:
                    self._q.put(("log", line.decode("utf-8", errors="replace").strip()))
                except Exception:
                    self._q.put(("log", "<binary>"))
                continue

            # Парсим Content-Length
            try:
                length_val = line.split(b":", 1)[1].strip()
                content_length = int(length_val)
            except Exception:
                self._q.put(("log", line.decode("utf-8", errors="replace").strip()))
                continue

            # Считываем оставшиеся заголовки до пустой строки
            while True:
                l2 = stdout.readline()
                if not l2:
                    return
                if l2 in (b"\r\n", b"\n", b""):
                    break

            # Читаем тело фиксированной длины
            body = b""
            remaining = content_length
            while remaining > 0:
                chunk = stdout.read(remaining)
                if not chunk:
                    return
                body += chunk
                remaining -= len(chunk)

            try:
                msg = json.loads(body.decode("utf-8"))
                self._q.put(("msg", msg))
            except Exception:
                self._q.put(("log", body.decode("utf-8", errors="replace")))

    def call(self, method: str, params: Dict[str, Any]) -> Any:
        """
        Отправляет JSON-RPC запрос и ждёт ответ с тем же id.
        """
        _id = str(uuid.uuid4())
        req = {"jsonrpc":"2.0","id":_id,"method":method,"params":params}
        payload = json.dumps(req).encode("utf-8")
        header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
        assert self.proc.stdin is not None
        self.proc.stdin.write(header + payload)
        self.proc.stdin.flush()
        # ждём ответ
        while True:
            kind, payload = self._q.get()
            if kind == "log":
                # можно логировать, если нужно
                continue
            msg = payload
            if msg.get("id") == _id:
                if "error" in msg and msg["error"]:
                    raise RuntimeError(str(msg["error"]))
                return msg.get("result")

    def close(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass

class BashMCP(MCPProcess):
    def __init__(self):
        # На Windows исполняемый файл npx — это npx.cmd
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        super().__init__(npx_cmd, ["-y", "@modelcontextprotocol/server-bash"])
        # Попытка инициализации протокола MCP (без фатала при несовпадении версии)
        try:
            self.call("initialize", {
                "clientInfo": {"name": "ai-agent", "version": "0.1.0"},
                "protocolVersion": "2024-11-05"
            })
        except Exception:
            # Некоторые сервера допускают прямые вызовы без initialize
            pass

    def exec(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        params = {"command": command}
        if cwd:
            params["cwd"] = cwd
        return self.call("bash/exec", params)

