"""Watch Codex Desktop session logs and mirror completions into agent-notify."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterable

from agent_notify.notify import process_hook_payload


DEFAULT_SESSIONS_ROOT = Path("/mnt/c/Users/xilig/.codex/sessions")
STATE_PATH = Path(__file__).resolve().parents[1] / "state" / "desktop_watcher_seen.json"
RECENT_FILE_LIMIT = 20


def iter_session_files(root: Path, limit: int = RECENT_FILE_LIMIT) -> Iterable[Path]:
    if not root.exists():
        return []
    files = sorted(root.glob("**/*.jsonl"), key=lambda path: path.stat().st_mtime)
    if limit <= 0:
        return files
    return files[-limit:]


def load_seen(path: Path = STATE_PATH) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, list):
        return set()
    return {str(item) for item in data}


def save_seen(seen: set[str], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def extract_completed_session_payloads(session_file: Path) -> list[dict]:
    session_meta: dict = {}
    model = ""
    completed_payloads: list[dict] = []

    try:
        lines = session_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        entry_type = entry.get("type")
        payload = entry.get("payload") or {}

        if entry_type == "session_meta":
            session_meta = payload
            continue

        if entry_type == "turn_context" and not model:
            model = payload.get("model", "") or model
            continue

        if entry_type == "event_msg" and payload.get("type") == "task_complete":
            summary = payload.get("last_agent_message", "")
            if summary:
                completed_payloads.append(
                    _completion_payload(
                        session_file=session_file,
                        session_meta=session_meta,
                        model=model,
                        summary=summary,
                        event_timestamp=entry.get("timestamp", ""),
                        event_type="task_complete",
                    )
                )
            continue

        if entry_type != "response_item":
            continue

        if payload.get("type") == "message" and payload.get("role") == "assistant":
            if payload.get("phase") == "final_answer":
                text = _message_text(payload.get("content") or [])
                if text:
                    completed_payloads.append(
                        _completion_payload(
                            session_file=session_file,
                            session_meta=session_meta,
                            model=model,
                            summary=text,
                            event_timestamp=entry.get("timestamp", ""),
                            event_type="final_answer",
                        )
                    )

    if _has_final_answer(completed_payloads):
        return [payload for payload in completed_payloads if payload["_desktop_event_type"] == "final_answer"]
    return completed_payloads


def _completion_payload(
    *,
    session_file: Path,
    session_meta: dict,
    model: str,
    summary: str,
    event_timestamp: str,
    event_type: str,
) -> dict:
    session_id = session_meta.get("id", session_file.stem)
    event_key = f"{session_id}:{event_timestamp}:{event_type}"
    return {
        "source_agent": "codex",
        "hook_event_name": "CodexDesktopSessionComplete",
        "hookEventName": "CodexDesktopSessionComplete",
        "cwd": session_meta.get("cwd", ""),
        "session_id": session_id,
        "model": model,
        "last_assistant_message": summary,
        "summary": summary,
        "transcript_path": str(session_file),
        "_desktop_event_key": event_key,
        "_desktop_event_type": event_type,
    }


def _has_final_answer(payloads: list[dict]) -> bool:
    return any(payload["_desktop_event_type"] == "final_answer" for payload in payloads)


def _message_text(content: list[dict]) -> str:
    parts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("output_text") or item.get("input_text")
        if text:
            parts.append(str(text))
    return "\n".join(parts).strip()


def scan_once(
    root: Path = DEFAULT_SESSIONS_ROOT,
    state_path: Path = STATE_PATH,
    baseline_existing: bool = False,
) -> int:
    seen = load_seen(state_path)
    processed = 0

    for session_file in iter_session_files(root):
        for payload in extract_completed_session_payloads(session_file):
            event_key = payload["_desktop_event_key"]
            if event_key in seen:
                continue
            if baseline_existing:
                seen.add(event_key)
                continue
            payload = {key: value for key, value in payload.items() if not key.startswith("_desktop_")}
            process_hook_payload(payload)
            seen.add(event_key)
            processed += 1

    if processed or baseline_existing:
        save_seen(seen, state_path)
    return processed


def watch(root: Path = DEFAULT_SESSIONS_ROOT, state_path: Path = STATE_PATH, interval: float = 2.0) -> None:
    if not state_path.exists():
        scan_once(root, state_path, baseline_existing=True)
    while True:
        scan_once(root, state_path)
        time.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch Codex Desktop sessions for completed answers.")
    parser.add_argument("--sessions-root", type=Path, default=DEFAULT_SESSIONS_ROOT)
    parser.add_argument("--state-path", type=Path, default=STATE_PATH)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Process existing completed sessions instead of only future completions.",
    )
    args = parser.parse_args()

    if args.once:
        print(scan_once(args.sessions_root, args.state_path, baseline_existing=not args.backfill))
        return 0

    watch(args.sessions_root, args.state_path, args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
