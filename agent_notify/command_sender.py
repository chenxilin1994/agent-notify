"""Dispatch follow-up commands to the AI CLI session that produced an event."""
from __future__ import annotations

import subprocess
from pathlib import Path


class CommandRequestError(ValueError):
    """Raised when a follow-up command cannot be sent."""


def build_resume_command(agent: str, session_id: str, command: str) -> list[str]:
    agent_name = (agent or "").lower()
    if agent_name == "codex":
        return ["codex", "resume", session_id, command]
    if agent_name == "claude":
        return ["claude", "--resume", session_id, command]
    raise CommandRequestError(f"不支持的 AI: {agent or 'unknown'}")


def send_command(event: dict, command: str) -> dict:
    clean_command = (command or "").strip()
    if not clean_command:
        raise CommandRequestError("命令不能为空")

    session_id = str(event.get("session_id") or "").strip()
    if not session_id:
        raise CommandRequestError("缺少 session_id，无法续写对应会话")

    agent = str(event.get("agent") or "").strip().lower()
    args = build_resume_command(agent, session_id, clean_command)

    cwd = str(event.get("cwd") or "").strip()
    cwd_path = Path(cwd).expanduser() if cwd else Path.cwd()
    if not cwd_path.exists():
        cwd_path = Path.cwd()

    process = subprocess.Popen(
        args,
        cwd=str(cwd_path),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    return {
        "ok": True,
        "pid": process.pid,
        "agent": agent,
        "session_id": session_id,
        "cwd": str(cwd_path),
        "args": args,
    }
