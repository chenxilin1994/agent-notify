from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from agent_notify.command_sender import CommandRequestError, build_resume_command, send_command


def test_builds_codex_resume_command_with_prompt():
    assert build_resume_command("codex", "session-123", "继续修复") == [
        "codex",
        "resume",
        "session-123",
        "继续修复",
    ]


def test_builds_claude_resume_command_with_prompt():
    assert build_resume_command("claude", "session-456", "继续修复") == [
        "claude",
        "--resume",
        "session-456",
        "继续修复",
    ]


def test_send_command_starts_process_in_event_cwd(monkeypatch, tmp_path: Path):
    calls = []

    class FakeProcess:
        pid = 4242

    def fake_popen(args, **kwargs):
        calls.append((args, kwargs))
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = send_command(
        {
            "agent": "codex",
            "session_id": "session-123",
            "cwd": str(tmp_path),
        },
        "继续修复",
    )

    assert result == {
        "ok": True,
        "pid": 4242,
        "agent": "codex",
        "session_id": "session-123",
        "cwd": str(tmp_path),
        "args": ["codex", "resume", "session-123", "继续修复"],
    }
    assert calls[0][0] == ["codex", "resume", "session-123", "继续修复"]
    assert calls[0][1]["cwd"] == str(tmp_path)
    assert calls[0][1]["start_new_session"] is True
    assert calls[0][1]["stdin"] == subprocess.DEVNULL
    assert calls[0][1]["stdout"] == subprocess.DEVNULL
    assert calls[0][1]["stderr"] == subprocess.DEVNULL


@pytest.mark.parametrize(
    "event, command, message",
    [
        ({"agent": "codex", "cwd": "/tmp"}, "继续", "缺少 session_id"),
        ({"agent": "codex", "session_id": "s", "cwd": "/tmp"}, "   ", "命令不能为空"),
        ({"agent": "unknown", "session_id": "s", "cwd": "/tmp"}, "继续", "不支持的 AI"),
    ],
)
def test_send_command_validates_request(event, command, message):
    with pytest.raises(CommandRequestError) as exc:
        send_command(event, command)

    assert message in str(exc.value)
