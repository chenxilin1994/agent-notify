from __future__ import annotations

import json
from pathlib import Path
import sys
import socketserver
from io import BytesIO


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_notify import server  # noqa: E402


def test_server_identity_exposes_runtime_paths():
    identity = server.build_identity()

    assert identity["app"] == "agent-notify"
    assert identity["root"] == str(ROOT)
    assert identity["db_path"].endswith("/state/agent_notify.db")


def test_server_handles_requests_with_threading_tcp_server():
    http_server = server.ReuseAddrServer("127.0.0.1", 0, server.APIHandler)
    try:
        assert isinstance(http_server.server, socketserver.ThreadingTCPServer)
        assert http_server.server.allow_reuse_address is True
    finally:
        http_server.server_close()


class _PostHandler(server.APIHandler):
    def __init__(self, body: dict):
        self.rfile = BytesIO(json.dumps(body).encode("utf-8"))
        self.headers = {"Content-Length": str(len(json.dumps(body).encode("utf-8")))}
        self.status = None
        self.payload = None

    def send_json(self, data, status: int = 200):
        self.status = status
        self.payload = data


def test_send_command_endpoint_dispatches_latest_event(monkeypatch):
    sent = []
    latest = {
        "agent": "codex",
        "session_id": "session-123",
        "cwd": "/tmp/project",
    }

    monkeypatch.setattr(server, "get_latest", lambda: latest)
    monkeypatch.setattr(
        server,
        "send_ai_command",
        lambda event, command: sent.append((event, command)) or {"ok": True, "pid": 1234},
    )

    handler = _PostHandler({"command": "继续修复"})
    handler.handle_send_command()

    assert handler.status == 200
    assert handler.payload == {"ok": True, "pid": 1234}
    assert sent == [(latest, "继续修复")]


def test_send_command_endpoint_returns_400_for_invalid_request(monkeypatch):
    monkeypatch.setattr(server, "get_latest", lambda: {"agent": "codex"})

    handler = _PostHandler({"command": "   "})
    handler.handle_send_command()

    assert handler.status == 400
    assert "命令不能为空" in handler.payload["error"]
