"""Process hook payloads and store events."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from agent_notify.desktop import open_in_browser, show_notification
from agent_notify.storage import get_category_rules, insert_event


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
DETAIL_PATH = WEB_DIR / "index.html"


def classify_event(user_input: str, summary: str, transcript_path: str) -> str:
    """Classify event based on keywords and tools used."""
    rules = get_category_rules()

    # Get tools used from transcript
    tools_used = []
    if transcript_path and Path(transcript_path).exists():
        try:
            lines = Path(transcript_path).read_text().strip().split("\n")
            for line in lines:
                entry = json.loads(line)
                entry_type = entry.get("type", "")

                # Claude Code format: check for tool_use in message
                if entry_type == "assistant":
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_name = item.get("name", "")
                                if tool_name:
                                    tools_used.append(tool_name)

                # Codex format: check for tool_invocation
                elif entry_type == "tool_invocation":
                    payload_data = entry.get("payload", {})
                    tool_name = payload_data.get("name", "")
                    if tool_name:
                        tools_used.append(tool_name)
        except (json.JSONDecodeError, KeyError):
            pass

    # Combine user_input and summary for keyword matching
    text_content = f"{user_input} {summary}".lower()

    # Score each category
    best_match = None
    best_score = 0

    for rule in rules:
        if not rule.get("enabled", True):
            continue

        score = 0

        # Keyword matching
        keywords = rule.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in text_content:
                score += 1

        # Tool matching
        rule_tools = rule.get("tools", [])
        for tool in rule_tools:
            if tool in tools_used:
                score += 2  # Tools have higher weight

        # Update best match
        if score > best_score:
            best_score = score
            best_match = rule.get("category")

    return best_match or "未分类"


def generate_highlight_data(user_input: str, summary: str, category: str) -> str:
    """Generate highlight data for the event."""
    # Get category rules to find matched keywords
    rules = get_category_rules()

    matched_keywords = []
    matched_tools = []
    category_matched = category

    # Find keywords that matched
    text_content = f"{user_input} {summary}".lower()
    for rule in rules:
        if rule.get("category") == category:
            keywords = rule.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_content:
                    matched_keywords.append(keyword)

    highlight_data = {
        "keywords_matched": matched_keywords[:10],  # Limit to 10
        "category_matched": category_matched,
    }

    return json.dumps(highlight_data, ensure_ascii=False)


def normalize_hook_payload(payload: dict, source_agent: str) -> dict:
    cwd = payload.get("cwd", "")
    timestamp = datetime.now(timezone.utc).isoformat()

    # Claude Code Stop hook provides last_assistant_message directly
    summary = payload.get("last_assistant_message") or ""
    model = payload.get("model", "")

    # Get token usage from payload
    input_tokens = payload.get("input_tokens", 0) or payload.get("usage", {}).get("input_tokens", 0)
    output_tokens = payload.get("output_tokens", 0) or payload.get("usage", {}).get("output_tokens", 0)

    # Get user input, assistant message and model from transcript JSONL file
    user_input = ""
    transcript_path = payload.get("transcript_path")
    if transcript_path and Path(transcript_path).exists():
        try:
            # JSONL: each line is a separate JSON object
            lines = Path(transcript_path).read_text().strip().split("\n")

            # First pass: find model and token usage from the latest turn_context or assistant
            if not model:
                for line in reversed(lines):
                    entry = json.loads(line)
                    entry_type = entry.get("type", "")

                    # Check turn_context for model
                    if entry_type == "turn_context":
                        payload_data = entry.get("payload", {})
                        model = payload_data.get("model", "")
                        if model:
                            break

                    # Check assistant message for model (Claude format)
                    elif entry_type == "assistant":
                        msg = entry.get("message", {})
                        model = msg.get("model", "")
                        if model:
                            break

            # Also check for token usage in result entries
            if not input_tokens or not output_tokens:
                for line in reversed(lines):
                    entry = json.loads(line)
                    entry_type = entry.get("type", "")

                    # Check for usage in assistant message
                    if entry_type == "assistant":
                        msg = entry.get("message", {})
                        usage = msg.get("usage", {})
                        if usage:
                            input_tokens = usage.get("input_tokens", input_tokens)
                            output_tokens = usage.get("output_tokens", output_tokens)

                    # Check for result entry with usage
                    elif entry_type == "result":
                        result_usage = entry.get("usage", {})
                        if result_usage:
                            input_tokens = result_usage.get("input_tokens", input_tokens)
                            output_tokens = result_usage.get("output_tokens", output_tokens)

                    if input_tokens and output_tokens:
                        break

            # Second pass: find user input
            for line in reversed(lines):
                entry = json.loads(line)
                entry_type = entry.get("type", "")

                # Claude Code format: type == "user"
                if entry_type == "user" and not user_input:
                    msg = entry.get("message", {})
                    content = msg.get("content", "")
                    if isinstance(content, str) and content and not content.startswith('{'):
                        user_input = content
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                user_input = item.get("text", "")
                                break

                # Codex format: type == "user_message"
                elif entry_type == "user_message" and not user_input:
                    payload_data = entry.get("payload", {})
                    user_input = payload_data.get("message", "")

                # Also check for event_msg with user input
                elif entry_type == "event_msg" and not user_input:
                    payload_data = entry.get("payload", {})
                    if payload_data.get("type") == "user_message":
                        user_input = payload_data.get("message", "")

                if user_input:
                    break

            # Third pass: find summary if not provided
            if not summary:
                for line in reversed(lines):
                    entry = json.loads(line)
                    entry_type = entry.get("type", "")

                    # Codex format: type == "agent_message"
                    if entry_type == "agent_message":
                        payload_data = entry.get("payload", {})
                        summary = payload_data.get("message", "")
                        if summary:
                            break

                    # Claude Code format: type == "assistant"
                    elif entry_type == "assistant":
                        msg = entry.get("message", {})
                        content = msg.get("content", "")
                        if isinstance(content, str) and content:
                            summary = content
                            break
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    summary = item.get("text", "")
                                    break
                            if summary:
                                break

                    # Also check for event_msg
                    elif entry_type == "event_msg":
                        payload_data = entry.get("payload", {})
                        if payload_data.get("type") == "agent_message":
                            summary = payload_data.get("message", "")
                            if summary:
                                break
                        elif payload_data.get("type") == "task_complete":
                            summary = payload_data.get("last_agent_message", "")
                            if summary:
                                break

        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback if no summary found
    if not summary:
        summary = "任务已完成"

    # Classify the event
    auto_category = classify_event(user_input, summary, transcript_path or "")

    # Generate highlight data
    highlight_data = generate_highlight_data(user_input, summary, auto_category)

    return {
        "id": f"{timestamp}-{source_agent}",
        "agent": source_agent,
        "title": "回答完成",
        "project_name": Path(cwd).name if cwd else "",
        "cwd": cwd,
        "session_id": payload.get("session_id", ""),
        "timestamp": timestamp,
        "summary": summary,
        "status": "completed",
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "source_event": payload.get("hook_event_name", "Stop"),
        "user_input": user_input,
        "detail_path": str(DETAIL_PATH),
        "auto_category": auto_category,
        "highlight_data": highlight_data,
    }


def detect_source_agent(payload: dict) -> str:
    """Detect which agent triggered the hook."""
    # Check explicit source_agent field
    if payload.get("source_agent") in {"codex", "claude"}:
        return payload["source_agent"]

    # Check transcript_path first - most reliable indicator
    transcript_path = payload.get("transcript_path", "")
    if transcript_path:
        if ".codex" in transcript_path or "codex" in transcript_path.lower():
            return "codex"
        if ".claude" in transcript_path or "claude" in transcript_path.lower():
            return "claude"

    # Check session_id patterns
    session_id = str(payload.get("session_id", "")).lower()
    if "codex" in session_id:
        return "codex"
    if "claude" in session_id:
        return "claude"

    # Check cwd
    cwd = payload.get("cwd", "")
    if ".codex" in cwd or "codex" in cwd.lower():
        return "codex"
    if ".claude" in cwd or "claude" in cwd.lower():
        return "claude"

    # Check model field
    model = payload.get("model", "")
    if model:
        if "gpt" in model.lower() or "codex" in model.lower():
            return "codex"
        if "claude" in model.lower() or "glm" in model.lower():
            return "claude"

    # Check environment variable
    env_model = os.environ.get("ANTHROPIC_MODEL", "")
    if env_model:
        if "gpt" in env_model.lower() or "codex" in env_model.lower():
            return "codex"
        if "claude" in env_model.lower() or "glm" in env_model.lower():
            return "claude"

    # Default to codex if transcript_path contains rollout (Codex session pattern)
    if "rollout" in transcript_path.lower():
        return "codex"

    # Default to claude for Claude Code environment
    return "claude"


def process_hook_payload(payload: dict) -> dict:
    event = normalize_hook_payload(payload, source_agent=detect_source_agent(payload))
    # Store in SQLite (no limit on history)
    insert_event(event)
    # No desktop notification - web UI is enough
    # show_notification(event["title"], event["summary"])
    open_in_browser(event["detail_path"])
    return event


def main() -> int:
    raw_input = sys.stdin.read().strip()
    payload = json.loads(raw_input) if raw_input else {}

    # Debug: log actual payload structure
    debug_log = Path(ROOT) / "state" / "hook_payload_debug.json"
    debug_log.parent.mkdir(exist_ok=True)
    debug_log.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    process_hook_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())