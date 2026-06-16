from pathlib import Path
import io
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_notify.desktop import (
    open_in_browser,
    pick_browser_opener,
    pick_notification_backend,
    show_notification,
)


def test_backend_selection_prefers_notify_send(monkeypatch):
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/notify-send" if name == "notify-send" else None,
    )
    assert pick_notification_backend() == "notify-send"


def test_browser_opener_prefers_xdg_open(monkeypatch):
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/xdg-open" if name == "xdg-open" else None,
    )
    assert pick_browser_opener() == "xdg-open"


def test_browser_opener_falls_back_to_powershell(monkeypatch):
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
        if name == "powershell.exe"
        else None,
    )
    assert pick_browser_opener() == "powershell.exe"


def test_notification_backend_falls_back_to_stderr(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert pick_notification_backend() == "stderr"


def test_show_notification_dispatches_selected_backend(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/notify-send" if name == "notify-send" else None,
    )
    monkeypatch.setattr("subprocess.run", lambda args, check=False: calls.append((args, check)))
    show_notification("Done", "Body")
    assert calls == [(["notify-send", "Done", "Body"], False)]


def test_open_in_browser_dispatches_selected_backend(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/xdg-open" if name == "xdg-open" else None,
    )
    monkeypatch.setattr("subprocess.run", lambda args, check=False: calls.append((args, check)))
    open_in_browser("/tmp/example.html")
    assert calls == [(["xdg-open", "/tmp/example.html"], False)]


def test_show_notification_dispatches_powershell_backend(monkeypatch):
    calls = []

    def fake_run(args, check=False, env=None):
        calls.append((args, check, env))

    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
        if name == "powershell.exe"
        else None,
    )
    monkeypatch.setattr("subprocess.run", fake_run)

    show_notification("It's done", "Body with quote '")

    assert len(calls) == 1
    args, check, env = calls[0]
    assert args[:3] == ["powershell.exe", "-NoProfile", "-Command"]
    assert check is False
    assert env["AGENT_NOTIFY_TITLE"] == "It's done"
    assert env["AGENT_NOTIFY_BODY"] == "Body with quote '"


def test_open_in_browser_falls_back_to_stderr(monkeypatch):
    stderr = io.StringIO()
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr("sys.stderr", stderr)
    open_in_browser("/tmp/example.html")
    assert "Open in browser: /tmp/example.html" in stderr.getvalue()
