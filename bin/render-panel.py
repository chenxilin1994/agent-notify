#!/usr/bin/env python3
from __future__ import annotations

import argparse
import posixpath
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
STATE_ROOT = ROOT / "state"


def _safe_join(root: Path, request_path: str) -> str:
    relative = posixpath.normpath(unquote(urlsplit(request_path).path))
    parts = [part for part in relative.split("/") if part and part != "."]
    resolved = root
    for part in parts:
        if part == "..":
            continue
        resolved = resolved / part
    return str(resolved)


class PanelRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, web_root: Path, state_root: Path, **kwargs) -> None:
        self.web_root = web_root
        self.state_root = state_root
        super().__init__(*args, directory=str(web_root), **kwargs)

    def translate_path(self, path: str) -> str:
        request_path = urlsplit(path).path
        if request_path == "/state" or request_path.startswith("/state/"):
            suffix = request_path.removeprefix("/state")
            return _safe_join(self.state_root, suffix or "/")
        return _safe_join(self.web_root, request_path)


def build_server(host: str, port: int, *, web_root: Path = WEB_ROOT, state_root: Path = STATE_ROOT) -> ThreadingHTTPServer:
    def handler(*args, **kwargs):
        return PanelRequestHandler(*args, web_root=web_root, state_root=state_root, **kwargs)

    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the agent notify panel.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = build_server(args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
