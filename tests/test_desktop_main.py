from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_JS = ROOT / "desktop" / "main.js"


def test_electron_server_uses_resource_root_for_pythonpath():
    source = MAIN_JS.read_text(encoding="utf-8")

    assert "const resourcePath = getResourcePath();" in source
    assert "cwd: resourcePath" in source
    assert "PYTHONPATH: resourcePath" in source
    assert "PYTHONPATH: serverPath" not in source
