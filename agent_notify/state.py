from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def trim_history(history: list[dict], limit: int = 50) -> list[dict]:
    return history[-limit:]


def _fsync_parent_directory(path: Path) -> None:
    dir_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
        _fsync_parent_directory(path)
    finally:
        tmp_path.unlink(missing_ok=True)
