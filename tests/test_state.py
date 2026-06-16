from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_notify.state import trim_history, write_json_atomic


def test_trim_history_keeps_last_fifty():
    history = [{"id": f"item-{i}"} for i in range(51)]
    trimmed = trim_history(history, limit=50)
    assert [item["id"] for item in trimmed] == [f"item-{i}" for i in range(1, 51)]


def test_write_json_atomic_creates_valid_json(tmp_path: Path):
    path = tmp_path / "latest.json"
    write_json_atomic(path, {"ok": True})
    assert path.read_text(encoding="utf-8").strip() == '{\n  "ok": true\n}'
