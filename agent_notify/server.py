"""HTTP server for agent-notify with SQLite backend."""
from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import subprocess
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
STATE_DIR = ROOT / "state"
DB_PATH = STATE_DIR / "agent_notify.db"

# Import storage functions
from agent_notify.storage import (
    delete_events_before_days,
    delete_all_events,
    get_stats,
    get_tags,
    create_tag,
    update_tag,
    delete_tag,
    get_event_tags,
    add_event_tag,
    remove_event_tag,
    set_event_tags,
    get_category_rules,
    update_category_rule,
    get_events_for_export,
    get_history,
)


class APIHandler(BaseHTTPRequestHandler):
    """Handler for web UI and SQLite API."""

    def log_message(self, format, *args) -> None:
        """Suppress default logging."""
        pass

    def send_json(self, data: dict | list, status: int = 200) -> None:
        """Send JSON response."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str = "text/html") -> None:
        """Send file response."""
        if not path.exists():
            self.send_error(404, "File not found")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API endpoints
        if path == "/api/latest":
            self.handle_latest()
        elif path == "/api/history":
            self.handle_history(query)
        elif path == "/api/stats":
            self.handle_stats()
        elif path == "/api/identity":
            self.send_json(build_identity())
        elif path == "/api/tags":
            self.handle_get_tags()
        elif path.startswith("/api/events/") and path.endswith("/tags"):
            # Extract event_id from path like /api/events/{event_id}/tags
            event_id = path.split("/")[-2]
            self.handle_get_event_tags(event_id)
        elif path == "/api/categories":
            self.handle_get_categories()
        elif path == "/api/analytics":
            self.handle_analytics()
        elif path.startswith("/api/session/"):
            # Extract session_id from path like /api/session/{session_id}
            session_id = path.split("/")[-1]
            self.handle_session(session_id)
        elif path == "/api/export/csv":
            self.handle_export_csv(query)
        elif path == "/api/export/json":
            self.handle_export_json(query)
        # Static files
        elif path == "/" or path == "/index.html":
            self.send_file(WEB_DIR / "index.html", "text/html")
        elif path == "/styles.css":
            self.send_file(WEB_DIR / "styles.css", "text/css")
        elif path == "/app.js":
            self.send_file(WEB_DIR / "app.js", "application/javascript")
        else:
            self.send_error(404, "Not found")

    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/cleanup":
            self.handle_cleanup()
        elif path == "/api/clear-all":
            self.handle_clear_all()
        elif path == "/api/tags":
            self.handle_create_tag()
        elif path.startswith("/api/events/") and path.endswith("/bookmark"):
            # Extract event_id from path like /api/events/{event_id}/bookmark
            event_id = path.split("/")[-2]
            self.handle_bookmark(event_id)
        elif path.startswith("/api/events/") and path.endswith("/tags"):
            # Extract event_id from path like /api/events/{event_id}/tags
            event_id = path.split("/")[-2]
            self.handle_add_event_tag(event_id)
        else:
            self.send_error(404, "Not found")

    def do_PUT(self) -> None:
        """Handle PUT requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Match /api/tags/{tag_id}
        match = re.match(r"^/api/tags/([^/]+)$", path)
        if match:
            tag_id = match.group(1)
            self.handle_update_tag(tag_id)
            return

        # Match /api/categories/{rule_id}
        match = re.match(r"^/api/categories/([^/]+)$", path)
        if match:
            rule_id = match.group(1)
            self.handle_update_category(rule_id)
            return

        self.send_error(404, "Not found")

    def do_DELETE(self) -> None:
        """Handle DELETE requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Match /api/tags/{tag_id}
        match = re.match(r"^/api/tags/([^/]+)$", path)
        if match:
            tag_id = match.group(1)
            self.handle_delete_tag(tag_id)
            return

        # Match /api/events/{event_id}/tags/{tag_id}
        match = re.match(r"^/api/events/([^/]+)/tags/([^/]+)$", path)
        if match:
            event_id = match.group(1)
            tag_id = match.group(2)
            self.handle_remove_event_tag(event_id, tag_id)
            return

        self.send_error(404, "Not found")

    def handle_latest(self) -> None:
        """Get latest event."""
        try:
            STATE_DIR.mkdir(exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()

            if row:
                self.send_json(dict(row))
            else:
                self.send_json({"error": "No events found"}, 404)
        except sqlite3.OperationalError:
            self.send_json({"error": "Database not initialized"}, 404)

    def handle_history(self, query: dict) -> None:
        """Get paginated history."""
        try:
            # Parse query parameters
            page = int(query.get("page", ["1"])[0])
            per_page = int(query.get("per_page", ["20"])[0])
            agent = query.get("agent", [None])[0]
            project = query.get("project", [None])[0]
            time_days = query.get("time_days", [None])[0]
            category = query.get("category", [None])[0]
            search = query.get("search", [None])[0]
            search_mode = query.get("search_mode", ["normal"])[0]
            bookmarked = query.get("bookmarked", ["false"])[0] == "true"
            date_start = query.get("date_start", [None])[0]
            date_end = query.get("date_end", [None])[0]
            sort_column = query.get("sort", ["timestamp"])[0]
            sort_direction = query.get("dir", ["desc"])[0]

            events, total, projects, categories = get_history(
                page=page,
                per_page=per_page,
                agent=agent,
                project=project,
                time_days=time_days,
                category=category,
                search=search,
                search_mode=search_mode,
                bookmarked=bookmarked,
                date_start=date_start,
                date_end=date_end,
                sort_column=sort_column,
                sort_direction=sort_direction,
            )

            total_pages = (total + per_page - 1) // per_page

            self.send_json({
                "events": events,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": total_pages,
                },
                "projects": projects,
                "categories": categories,
            })
        except Exception as e:
            self.send_json({
                "events": [],
                "pagination": {"page": 1, "per_page": 20, "total": 0, "total_pages": 0},
                "projects": [],
                "categories": [],
            })

    def handle_stats(self) -> None:
        """Get database statistics."""
        try:
            stats = get_stats()
            self.send_json(stats)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # =====================
    # Tag Handlers
    # =====================

    def handle_get_tags(self) -> None:
        """Get all tags."""
        try:
            tags = get_tags()
            self.send_json(tags)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_create_tag(self) -> None:
        """Create a new tag."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            name = data.get("name", "")
            color = data.get("color", "#7b61ff")

            if not name:
                self.send_json({"error": "Name required"}, 400)
                return

            tag = create_tag(name, color)
            self.send_json(tag)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_update_tag(self, tag_id: str) -> None:
        """Update a tag."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            tag = update_tag(tag_id, name=data.get("name"), color=data.get("color"))
            if tag:
                self.send_json(tag)
            else:
                self.send_json({"error": "Tag not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_delete_tag(self, tag_id: str) -> None:
        """Delete a tag."""
        try:
            deleted = delete_tag(tag_id)
            if deleted:
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Tag not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_get_event_tags(self, event_id: str) -> None:
        """Get tags for an event."""
        try:
            tags = get_event_tags(event_id)
            self.send_json(tags)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_add_event_tag(self, event_id: str) -> None:
        """Add tags to an event (supports single tag_id or array of tag_ids)."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # Support both single tag_id and array of tag_ids
            tag_ids = data.get("tag_ids", [])
            if not tag_ids:
                tag_id = data.get("tag_id", "")
                if tag_id:
                    tag_ids = [tag_id]

            if not tag_ids:
                self.send_json({"error": "tag_id or tag_ids required"}, 400)
                return

            # Set all tags for the event
            set_event_tags(event_id, tag_ids)
            self.send_json({"success": True, "tags": tag_ids})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_remove_event_tag(self, event_id: str, tag_id: str) -> None:
        """Remove a tag from an event."""
        try:
            removed = remove_event_tag(event_id, tag_id)
            if removed:
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Tag not assigned to event"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_bookmark(self, event_id: str) -> None:
        """Toggle bookmark status for an event."""
        try:
            STATE_DIR.mkdir(exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            # Get current status
            cursor.execute("SELECT bookmarked FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            if row is None:
                conn.close()
                self.send_json({"error": "Event not found"}, 404)
                return

            current_status = row[0] or False
            new_status = not current_status

            # Update
            cursor.execute("UPDATE events SET bookmarked = ? WHERE id = ?", (new_status, event_id))
            conn.commit()
            conn.close()

            self.send_json({"success": True, "bookmarked": new_status})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # =====================
    # Category Handlers
    # =====================

    def handle_get_categories(self) -> None:
        """Get all category rules."""
        try:
            rules = get_category_rules()
            self.send_json(rules)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_analytics(self) -> None:
        """Get analytics data for charts."""
        try:
            analytics = self.get_analytics_data()
            self.send_json(analytics)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_session(self, session_id: str) -> None:
        """Get all events for a session."""
        try:
            STATE_DIR.mkdir(exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM events
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))

            rows = cursor.fetchall()
            conn.close()

            events = [dict(row) for row in rows]
            self.send_json(events)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def get_analytics_data(self) -> dict:
        """Calculate analytics statistics."""
        STATE_DIR.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get daily stats for last 30 days
        cursor.execute("""
            SELECT
                date(timestamp) as day,
                COUNT(*) as total,
                SUM(CASE WHEN agent = 'claude' THEN 1 ELSE 0 END) as claude_count,
                SUM(CASE WHEN agent = 'codex' THEN 1 ELSE 0 END) as codex_count,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens
            FROM events
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY date(timestamp)
            ORDER BY day
        """)
        daily_stats = [dict(row) for row in cursor.fetchall()]

        # Get token totals by agent
        cursor.execute("""
            SELECT
                agent,
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output
            FROM events
            GROUP BY agent
        """)
        token_totals = {row[0]: {"input": row[1] or 0, "output": row[2] or 0} for row in cursor.fetchall()}

        # Get average response length
        cursor.execute("""
            SELECT AVG(LENGTH(summary)) as avg_length,
                   AVG(input_tokens + output_tokens) as avg_tokens
            FROM events
            WHERE summary IS NOT NULL
        """)
        avg_row = cursor.fetchone()

        # Get total and week counts
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM events WHERE timestamp >= datetime('now', '-7 days')")
        week_events = cursor.fetchone()[0]

        conn.close()

        return {
            "daily_stats": daily_stats,
            "claude_input_tokens": token_totals.get("claude", {}).get("input", 0),
            "claude_output_tokens": token_totals.get("claude", {}).get("output", 0),
            "codex_input_tokens": token_totals.get("codex", {}).get("input", 0),
            "codex_output_tokens": token_totals.get("codex", {}).get("output", 0),
            "avg_response_length": round(avg_row[0] or 0),
            "avg_tokens": round(avg_row[1] or 0),
            "total_events": total_events,
            "week_events": week_events,
        }

    def handle_update_category(self, rule_id: str) -> None:
        """Update a category rule."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            rule = update_category_rule(
                rule_id,
                category=data.get("category"),
                keywords=data.get("keywords"),
                tools=data.get("tools"),
                priority=data.get("priority"),
                color=data.get("color"),
                enabled=data.get("enabled"),
            )
            if rule:
                self.send_json(rule)
            else:
                self.send_json({"error": "Rule not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # =====================
    # Export Handlers
    # =====================

    def handle_export_csv(self, query: dict) -> None:
        """Export events as CSV."""
        try:
            agent = query.get("agent", [None])[0]
            project = query.get("project", [None])[0]
            category = query.get("category", [None])[0]
            time_days = query.get("time_days", [None])[0]

            events = get_events_for_export(
                agent=agent,
                project=project,
                category=category,
                time_days=time_days,
            )

            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "timestamp", "agent", "auto_category", "tags",
                "project_name", "model", "user_input", "summary"
            ])

            # Data
            for event in events:
                writer.writerow([
                    event.get("timestamp", ""),
                    event.get("agent", ""),
                    event.get("auto_category", ""),
                    ",".join(event.get("tags", [])),
                    event.get("project_name", ""),
                    event.get("model", ""),
                    event.get("user_input", ""),
                    event.get("summary", ""),
                ])

            csv_content = output.getvalue()

            # Send CSV response
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=agent_notify_export.csv")
            self.send_header("Content-Length", len(csv_content))
            self.end_headers()
            self.wfile.write(csv_content.encode("utf-8"))

        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_export_json(self, query: dict) -> None:
        """Export events as JSON."""
        try:
            agent = query.get("agent", [None])[0]
            project = query.get("project", [None])[0]
            category = query.get("category", [None])[0]
            time_days = query.get("time_days", [None])[0]

            events = get_events_for_export(
                agent=agent,
                project=project,
                category=category,
                time_days=time_days,
            )

            export_data = {
                "export_time": datetime.now(timezone.utc).isoformat(),
                "total": len(events),
                "events": events,
            }

            json_content = json.dumps(export_data, ensure_ascii=False, indent=2)

            # Send JSON response
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=agent_notify_export.json")
            self.send_header("Content-Length", len(json_content))
            self.end_headers()
            self.wfile.write(json_content.encode("utf-8"))

        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # =====================
    # Cleanup Handlers
    # =====================

    def handle_cleanup(self) -> None:
        """Clean up old events based on POST body."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                data = json.loads(body)
            else:
                data = {}

            days = data.get("days", 30)
            if days not in [7, 30, 90, 365]:
                self.send_json({"error": "Invalid days value: " + str(days)}, 400)
                return

            result = delete_events_before_days(days)
            self.send_json(result)

        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON body"}, 400)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_clear_all(self) -> None:
        """Clear all events."""
        try:
            deleted = delete_all_events()
            self.send_json({"deleted": deleted})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)


class ReuseAddrServer:
    """TCP Server with SO_REUSEADDR."""
    allow_reuse_address = True

    def __init__(self, host: str, port: int, handler: type) -> None:
        import socketserver

        class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True

        self.server = ReusableThreadingTCPServer((host, port), handler)
        self.server.daemon_threads = True

    def serve_forever(self) -> None:
        self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()

    def server_close(self) -> None:
        self.server.server_close()


_server: ReuseAddrServer | None = None
_server_thread: threading.Thread | None = None


def is_port_in_use(port: int) -> bool:
    """Check if port has a listening server."""
    result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True,
        text=True,
    )
    return f":{port}" in result.stdout


def get_server_url(port: int = 18865) -> str:
    """Get server URL."""
    return f"http://localhost:{port}"


def build_identity() -> dict:
    """Expose the runtime paths used by this server instance."""
    return {
        "app": "agent-notify",
        "root": str(ROOT),
        "web_dir": str(WEB_DIR),
        "state_dir": str(STATE_DIR),
        "db_path": str(DB_PATH),
    }


def start_server(port: int = 18865, daemon: bool = True) -> ReuseAddrServer | None:
    """Start HTTP server."""
    global _server, _server_thread

    if is_port_in_use(port):
        return None

    if _server is not None:
        return _server

    try:
        _server = ReuseAddrServer("localhost", port, APIHandler)
        _server_thread = threading.Thread(target=_server.serve_forever, daemon=daemon)
        _server_thread.start()
        return _server
    except OSError:
        return None


def stop_server() -> None:
    """Stop HTTP server."""
    global _server, _server_thread

    if _server is not None:
        _server.shutdown()
        _server.server_close()
        _server = None
        _server_thread = None


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18865
    print(f"Starting server on http://localhost:{port}")
    print(f"Web UI: http://localhost:{port}/")
    print(f"API: http://localhost:{port}/api/latest")
    print(f"API: http://localhost:{port}/api/history?page=1&per_page=20")
    print("Press Ctrl+C to stop")

    try:
        server = ReuseAddrServer("localhost", port, APIHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    except OSError as e:
        print(f"Error: {e}")
