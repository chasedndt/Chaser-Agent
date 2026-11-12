"""A minimal MCP client over stdio, standard library only.

A server's tool list is a menu, not a grant. Callers pick the exact tools they
expose and wrap each one with their own scope checks; a tool the caller did not
name cannot be called through this client even when the server offers it.
"""

from __future__ import annotations

import json
import queue
import subprocess
import threading
from typing import Any

PROTOCOL_VERSION = "2025-06-18"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class McpError(RuntimeError):
    pass


class McpStdioClient:
    def __init__(self, command: list[str], *, allowed_tools: frozenset[str], timeout: float = 90.0, env: dict[str, str] | None = None) -> None:
        self.command = command
        self.allowed_tools = allowed_tools
        self.timeout = timeout
        self.env = env
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._next_id = 0
        self._lines: queue.Queue[str | None] = queue.Queue()

    def _pump(self, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            self._lines.put(line)
        self._lines.put(None)

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        assert self._process is not None and self._process.stdin is not None
        self._next_id += 1
        identifier = self._next_id
        self._process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}, ensure_ascii=True) + "\n")
        self._process.stdin.flush()
        while True:
            try:
                line = self._lines.get(timeout=self.timeout)
            except queue.Empty as exc:
                self.close()
                raise McpError(f"MCP server did not answer {method} in time") from exc
            if line is None:
                self.close()
                raise McpError("MCP server closed its output")
            try:
                message = json.loads(line)
            except ValueError:
                continue  # Servers may write noise; only JSON-RPC replies count.
            if message.get("id") != identifier:
                continue
            if "error" in message:
                raise McpError(str(message["error"].get("message", "MCP error"))[:400])
            return message.get("result") or {}

    def start(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        self._lines = queue.Queue()
        self._process = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            encoding="utf-8", errors="replace", env=self.env, creationflags=NO_WINDOW,
        )
        threading.Thread(target=self._pump, args=(self._process,), daemon=True).start()
        self._request("initialize", {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "chaser-agent", "version": "0.2"}})

    def list_tools(self) -> list[dict[str, Any]]:
        with self._lock:
            self.start()
            return [tool for tool in self._request("tools/list", {}).get("tools", []) if tool.get("name") in self.allowed_tools]

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self.allowed_tools:
            raise McpError(f"{name} is not exposed through this client")
        with self._lock:
            self.start()
            result = self._request("tools/call", {"name": name, "arguments": arguments})
        text = "".join(part.get("text", "") for part in result.get("content", []) if part.get("type") == "text")
        if result.get("isError"):
            raise McpError(text[:400] or "The tool reported an error")
        return result.get("structuredContent", text)

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is None:
            return
        try:
            if process.stdin:
                process.stdin.close()
            process.terminate()
            process.wait(5)
        except (OSError, subprocess.SubprocessError):
            process.kill()
