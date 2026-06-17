from __future__ import annotations

import json
from pathlib import Path
import sys


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
        assert http_server.server.__class__.__name__ == "ThreadingTCPServer"
    finally:
        http_server.server_close()
