from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_notify import desktop_watcher  # noqa: E402
from agent_notify.desktop_watcher import extract_completed_session_payloads  # noqa: E402


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_extracts_codex_desktop_final_answer_payload(tmp_path: Path):
    session_file = tmp_path / "sessions" / "2026" / "06" / "17" / "rollout.jsonl"
    _write_jsonl(
        session_file,
        [
            {
                "timestamp": "2026-06-17T01:40:28.000Z",
                "type": "session_meta",
                "payload": {
                    "id": "desktop-session-1",
                    "cwd": "/home/chenxilin/.local/share/agent-notify",
                    "originator": "Codex Desktop",
                    "source": "vscode",
                },
            },
            {
                "timestamp": "2026-06-17T01:40:47.000Z",
                "type": "turn_context",
                "payload": {"model": "gpt-5.5"},
            },
            {
                "timestamp": "2026-06-17T01:41:01.000Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [{"type": "output_text", "text": "桌面端回答完成"}],
                },
            },
        ],
    )

    payloads = extract_completed_session_payloads(session_file)

    assert len(payloads) == 1
    assert payloads[0]["source_agent"] == "codex"
    assert payloads[0]["hook_event_name"] == "CodexDesktopSessionComplete"
    assert payloads[0]["cwd"] == "/home/chenxilin/.local/share/agent-notify"
    assert payloads[0]["session_id"] == "desktop-session-1"
    assert payloads[0]["model"] == "gpt-5.5"
    assert payloads[0]["summary"] == "桌面端回答完成"
    assert payloads[0]["transcript_path"] == str(session_file)
    assert payloads[0]["_desktop_event_key"] == "desktop-session-1:2026-06-17T01:41:01.000Z:final_answer"


def test_extracts_task_complete_when_no_final_answer(tmp_path: Path):
    session_file = tmp_path / "sessions" / "rollout.jsonl"
    _write_jsonl(
        session_file,
        [
            {
                "timestamp": "2026-06-17T01:40:28.000Z",
                "type": "session_meta",
                "payload": {"id": "desktop-session-2", "cwd": "/tmp/demo"},
            },
            {
                "timestamp": "2026-06-17T01:41:10.000Z",
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "last_agent_message": "任务已经完成",
                },
            },
        ],
    )

    payloads = extract_completed_session_payloads(session_file)

    assert len(payloads) == 1
    assert payloads[0]["session_id"] == "desktop-session-2"
    assert payloads[0]["summary"] == "任务已经完成"
    assert payloads[0]["_desktop_event_key"] == "desktop-session-2:2026-06-17T01:41:10.000Z:task_complete"


def test_extracts_multiple_final_answers_from_one_session(tmp_path: Path):
    session_file = tmp_path / "sessions" / "rollout.jsonl"
    _write_jsonl(
        session_file,
        [
            {
                "timestamp": "2026-06-17T01:40:28.000Z",
                "type": "session_meta",
                "payload": {"id": "desktop-session-multi", "cwd": "/tmp/demo"},
            },
            {
                "timestamp": "2026-06-17T01:41:01.000Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [{"type": "output_text", "text": "第一轮完成"}],
                },
            },
            {
                "timestamp": "2026-06-17T01:42:01.000Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [{"type": "output_text", "text": "第二轮完成"}],
                },
            },
        ],
    )

    payloads = extract_completed_session_payloads(session_file)

    assert [payload["summary"] for payload in payloads] == ["第一轮完成", "第二轮完成"]
    assert [payload["_desktop_event_key"] for payload in payloads] == [
        "desktop-session-multi:2026-06-17T01:41:01.000Z:final_answer",
        "desktop-session-multi:2026-06-17T01:42:01.000Z:final_answer",
    ]


def test_scan_once_processes_new_completion_only_once(tmp_path: Path, monkeypatch):
    sessions_root = tmp_path / "sessions"
    state_path = tmp_path / "state" / "seen.json"
    session_file = sessions_root / "2026" / "06" / "17" / "rollout.jsonl"
    _write_jsonl(
        session_file,
        [
            {
                "timestamp": "2026-06-17T01:40:28.000Z",
                "type": "session_meta",
                "payload": {"id": "desktop-session-3", "cwd": "/tmp/project"},
            },
            {
                "timestamp": "2026-06-17T01:41:01.000Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [{"type": "output_text", "text": "只处理一次"}],
                },
            },
        ],
    )
    processed = []
    monkeypatch.setattr(desktop_watcher, "process_hook_payload", processed.append)

    first_count = desktop_watcher.scan_once(sessions_root, state_path)
    second_count = desktop_watcher.scan_once(sessions_root, state_path)

    assert first_count == 1
    assert second_count == 0
    assert [payload["summary"] for payload in processed] == ["只处理一次"]


def test_scan_once_can_baseline_existing_sessions_without_processing(tmp_path: Path, monkeypatch):
    sessions_root = tmp_path / "sessions"
    state_path = tmp_path / "state" / "seen.json"
    session_file = sessions_root / "rollout.jsonl"
    _write_jsonl(
        session_file,
        [
            {
                "timestamp": "2026-06-17T01:40:28.000Z",
                "type": "session_meta",
                "payload": {"id": "desktop-session-4", "cwd": "/tmp/project"},
            },
            {
                "timestamp": "2026-06-17T01:41:01.000Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [{"type": "output_text", "text": "历史完成事件"}],
                },
            },
        ],
    )
    processed = []
    monkeypatch.setattr(desktop_watcher, "process_hook_payload", processed.append)

    count = desktop_watcher.scan_once(sessions_root, state_path, baseline_existing=True)

    assert count == 0
    assert processed == []
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["seen"] == ["desktop-session-4:2026-06-17T01:41:01.000Z:final_answer"]
    assert str(session_file) in state["files"]


def test_scan_once_skips_unchanged_session_files(tmp_path: Path, monkeypatch):
    sessions_root = tmp_path / "sessions"
    state_path = tmp_path / "state" / "seen.json"
    session_file = sessions_root / "rollout.jsonl"
    _write_jsonl(session_file, [])
    calls = []

    def fake_extract(path: Path) -> list[dict]:
        calls.append(path)
        return []

    monkeypatch.setattr(desktop_watcher, "extract_completed_session_payloads", fake_extract)

    first_count = desktop_watcher.scan_once(sessions_root, state_path)
    second_count = desktop_watcher.scan_once(sessions_root, state_path)

    assert first_count == 0
    assert second_count == 0
    assert calls == [session_file]


def test_iter_session_files_limits_to_recent_files(tmp_path: Path):
    sessions_root = tmp_path / "sessions"
    for index in range(25):
        session_file = sessions_root / f"rollout-{index:02d}.jsonl"
        _write_jsonl(session_file, [])
        mtime = 1_000 + index
        session_file.touch()
        import os

        os.utime(session_file, (mtime, mtime))

    files = list(desktop_watcher.iter_session_files(sessions_root, limit=3))

    assert [path.name for path in files] == [
        "rollout-22.jsonl",
        "rollout-23.jsonl",
        "rollout-24.jsonl",
    ]
