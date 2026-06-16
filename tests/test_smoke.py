from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path("/home/chenxilin/.local/share/agent-notify")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_notify.notify import json as notify_json  # noqa: E402
from agent_notify import notify as notify_module  # noqa: E402
from agent_notify.state import trim_history  # noqa: E402


def test_trim_history_keeps_exactly_fifty_latest_items():
    history = [{"id": str(i)} for i in range(60)]
    trimmed = trim_history(history, limit=50)
    assert len(trimmed) == 50
    assert trimmed[0]["id"] == "10"
    assert trimmed[-1]["id"] == "59"


def test_process_hook_payload_writes_latest_and_history(tmp_path: Path, monkeypatch):
    state_dir = tmp_path / "state"
    web_dir = tmp_path / "web"
    detail_path = web_dir / "index.html"
    web_dir.mkdir()
    detail_path.write_text("<!doctype html>", encoding="utf-8")

    monkeypatch.setattr(notify_module, "STATE_DIR", state_dir)
    monkeypatch.setattr(notify_module, "WEB_DIR", web_dir)
    monkeypatch.setattr(notify_module, "DETAIL_PATH", detail_path)

    notifications = []
    opened = []
    monkeypatch.setattr(notify_module, "show_notification", lambda title, body: notifications.append((title, body)))
    monkeypatch.setattr(notify_module, "open_in_browser", lambda target: opened.append(str(target)))

    for index in range(60):
        payload = {
            "hookEventName": "Stop",
            "cwd": f"/home/chenxilin/project/demo-{index}",
            "session_id": f"session-{index}",
            "model": "gpt-5.5",
            "summary": f"summary-{index}",
        }
        notify_module.process_hook_payload(payload)

    latest_path = state_dir / "latest.json"
    history_path = state_dir / "history.json"
    latest = notify_json.loads(latest_path.read_text(encoding="utf-8"))
    history = notify_json.loads(history_path.read_text(encoding="utf-8"))

    assert latest["summary"] == "summary-59"
    assert latest["detail_path"] == str(detail_path)
    assert len(history) == 50
    assert history[0]["summary"] == "summary-10"
    assert history[-1]["summary"] == "summary-59"
    assert notifications[-1] == ("回答完成", "summary-59")
    assert opened[-1] == str(detail_path)
