from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("agent_notify.notify", ROOT / "agent_notify" / "notify.py")
module = module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)

normalize_hook_payload = module.normalize_hook_payload


def test_normalize_codex_payload_uses_fallback_summary():
    event = normalize_hook_payload(
        {
            "hookEventName": "Stop",
            "cwd": "/home/chenxilin/project/win_channel/win_brain_v2",
            "session_id": "abc123",
            "model": "gpt-5.5",
        },
        source_agent="codex",
    )
    assert event["agent"] == "codex"
    assert event["project_name"] == "win_brain_v2"
    assert event["summary"] == "任务已完成，可查看详情"
    assert event["title"] == "回答完成"
    assert event["status"] == "completed"
    assert event["detail_path"].endswith("/.local/share/agent-notify/web/index.html")
    assert event["raw_excerpt"] == "任务已完成，可查看详情"
    assert event["source_event"] == "Stop"
    assert isinstance(event["timestamp"], str)
    assert event["timestamp"]


def test_normalize_claude_payload_prefers_short_text():
    event = normalize_hook_payload(
        {
            "hookEventName": "Stop",
            "cwd": "/home/chenxilin/project/win_channel/win_brain",
            "session_id": "xyz789",
            "model": "glm-5",
            "final_message": "已完成回答，详情见面板",
        },
        source_agent="claude",
    )
    assert event["agent"] == "claude"
    assert event["summary"] == "已完成回答，详情见面板"
    assert event["title"] == "回答完成"
    assert event["status"] == "completed"
    assert event["detail_path"].endswith("/.local/share/agent-notify/web/index.html")
    assert event["raw_excerpt"] == "已完成回答，详情见面板"
    assert event["source_event"] == "Stop"
    assert isinstance(event["timestamp"], str)
    assert event["timestamp"]
