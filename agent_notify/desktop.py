from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def pick_notification_backend() -> str:
    if shutil.which("notify-send"):
        return "notify-send"
    if shutil.which("powershell.exe"):
        return "powershell.exe"
    return "stderr"


def pick_browser_opener() -> str:
    if shutil.which("xdg-open"):
        return "xdg-open"
    if shutil.which("powershell.exe"):
        return "powershell.exe"
    return "stderr"


def start_server_if_needed() -> None:
    """Start HTTP server as a background process if not already running."""
    import subprocess

    # Check if server is already running
    result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True,
        text=True,
    )
    if ":8765" in result.stdout:
        return  # Server already running

    # Start server as a detached process
    subprocess.Popen(
        ["python3", "-m", "agent_notify.server", "8765"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # Detach from current process
    )


def open_in_browser(target: str | Path) -> None:
    """Open the web UI in browser via HTTP server to avoid CORS issues."""
    # Start HTTP server if not running
    start_server_if_needed()

    # Open HTTP URL instead of file:// URL (avoids CORS)
    url = "http://localhost:8765"
    opener = pick_browser_opener()

    if opener == "xdg-open":
        subprocess.run(["xdg-open", url], check=False)
        return
    if opener == "powershell.exe":
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "Start-Process", url],
            check=False,
        )
        return
    print(f"Open in browser: {url}", file=sys.stderr)


def show_notification(title: str, body: str) -> None:
    backend = pick_notification_backend()
    if backend == "notify-send":
        subprocess.run(["notify-send", title, body], check=False)
        return
    if backend == "powershell.exe":
        script = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]"
            " > $null; "
            "$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02; "
            "$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template); "
            "$texts = $xml.GetElementsByTagName('text'); "
            "$texts.Item(0).AppendChild($xml.CreateTextNode($env:AGENT_NOTIFY_TITLE)) > $null; "
            "$texts.Item(1).AppendChild($xml.CreateTextNode($env:AGENT_NOTIFY_BODY)) > $null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
            "$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Agent Notify'); "
            "$notifier.Show($toast)"
        )
        env = dict(os.environ)
        env["AGENT_NOTIFY_TITLE"] = title
        env["AGENT_NOTIFY_BODY"] = body
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            check=False,
            env=env,
        )
        return
    print(f"{title}: {body}", file=sys.stderr)
