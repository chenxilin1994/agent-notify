from __future__ import annotations

import importlib.util
import json
import threading
import urllib.request
from pathlib import Path


def test_panel_markup_exposes_required_controls():
    html = Path("/home/chenxilin/.local/share/agent-notify/web/index.html").read_text(encoding="utf-8")
    assert 'id="history-filter"' in html
    assert 'id="copy-summary"' in html
    assert 'id="latest-summary"' in html
    assert 'id="history-list"' in html


def test_panel_script_wires_required_controls():
    script = Path("/home/chenxilin/.local/share/agent-notify/web/app.js").read_text(encoding="utf-8")
    assert 'getElementById("copy-summary")' in script
    assert 'getElementById("history-filter")' in script
    assert 'addEventListener("click"' in script
    assert 'addEventListener("change"' in script


def _load_render_panel_module():
    path = Path("/home/chenxilin/.local/share/agent-notify/bin/render-panel.py")
    spec = importlib.util.spec_from_file_location("render_panel", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_panel_derives_roots_from_file():
    module = _load_render_panel_module()
    root = Path(module.__file__).resolve().parents[1]
    assert module.WEB_ROOT == root / "web"
    assert module.STATE_ROOT == root / "state"


def test_render_panel_serves_state_json(tmp_path: Path):
    module = _load_render_panel_module()
    web_root = tmp_path / "web"
    state_root = tmp_path / "state"
    web_root.mkdir()
    state_root.mkdir()
    (web_root / "index.html").write_text("<!doctype html><title>ok</title>", encoding="utf-8")
    latest_payload = {"summary": "latest summary"}
    history_payload = [{"agent": "codex", "summary": "done"}]
    (state_root / "latest.json").write_text(json.dumps(latest_payload), encoding="utf-8")
    (state_root / "history.json").write_text(json.dumps(history_payload), encoding="utf-8")

    server = module.build_server("127.0.0.1", 0, web_root=web_root, state_root=state_root)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        with urllib.request.urlopen(f"{base_url}/state/latest.json") as response:
            assert json.load(response) == latest_payload
        with urllib.request.urlopen(f"{base_url}/state/history.json") as response:
            assert json.load(response) == history_payload
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
