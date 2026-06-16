"""SQLite-based state storage for agent-notify."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "state"
DB_PATH = STATE_DIR / "agent_notify.db"

# Default category rules
DEFAULT_CATEGORY_RULES = [
    {
        "id": "cat-debug",
        "category": "调试",
        "keywords": ["bug", "fix", "error", "exception", "debug", "修复", "错误", "问题"],
        "tools": [],
        "priority": 1,
        "color": "#ff6b6b",
    },
    {
        "id": "cat-code",
        "category": "代码",
        "keywords": ["refactor", "implement", "add", "create", "write", "code", "代码", "实现", "添加"],
        "tools": ["Write", "Edit"],
        "priority": 2,
        "color": "#00ffa3",
    },
    {
        "id": "cat-docs",
        "category": "文档",
        "keywords": ["document", "readme", "doc", "explain", "说明", "文档", "注释"],
        "tools": [],
        "priority": 3,
        "color": "#00d4ff",
    },
    {
        "id": "cat-read",
        "category": "阅读",
        "keywords": ["read", "check", "understand", "查看", "理解", "分析", "了解"],
        "tools": ["Read"],
        "priority": 4,
        "color": "#7b61ff",
    },
    {
        "id": "cat-exec",
        "category": "执行",
        "keywords": ["run", "test", "build", "deploy", "运行", "测试", "构建", "部署"],
        "tools": ["Bash", "TaskCreate"],
        "priority": 5,
        "color": "#ffd700",
    },
    {
        "id": "cat-explore",
        "category": "探索",
        "keywords": ["search", "find", "explore", "搜索", "查找", "探索", "定位"],
        "tools": ["Glob", "Grep"],
        "priority": 6,
        "color": "#00ced1",
    },
]


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            agent TEXT NOT NULL,
            title TEXT,
            project_name TEXT,
            cwd TEXT,
            session_id TEXT,
            timestamp TEXT NOT NULL,
            summary TEXT,
            status TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            bookmarked BOOLEAN DEFAULT FALSE,
            source_event TEXT,
            raw_excerpt TEXT,
            user_input TEXT,
            detail_path TEXT,
            auto_category TEXT,
            highlight_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: Add new columns if they don't exist
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN auto_category TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN highlight_data TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN input_tokens INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN output_tokens INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN bookmarked BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#7b61ff',
            usage_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create event_tags table (association)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_tags (
            event_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (event_id, tag_id),
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    """)

    # Create category_rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_rules (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            keywords TEXT,
            tools TEXT,
            priority INTEGER DEFAULT 0,
            color TEXT DEFAULT '#7b61ff',
            enabled BOOLEAN DEFAULT TRUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Initialize default category rules if not exist
    cursor.execute("SELECT COUNT(*) FROM category_rules")
    if cursor.fetchone()[0] == 0:
        for rule in DEFAULT_CATEGORY_RULES:
            cursor.execute("""
                INSERT INTO category_rules (id, category, keywords, tools, priority, color, enabled)
                VALUES (?, ?, ?, ?, ?, ?, TRUE)
            """, (
                rule["id"],
                rule["category"],
                json.dumps(rule["keywords"]),
                json.dumps(rule["tools"]),
                rule["priority"],
                rule["color"],
            ))

    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_timestamp
        ON events(timestamp DESC)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_agent
        ON events(agent)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_session
        ON events(session_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_category
        ON events(auto_category)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tags_name
        ON tags(name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_tags_event
        ON event_tags(event_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_tags_tag
        ON event_tags(tag_id)
    """)

    conn.commit()
    conn.close()


def insert_event(event: dict) -> None:
    """Insert a new event into the database."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO events (
            id, agent, title, project_name, cwd, session_id,
            timestamp, summary, status, model, input_tokens, output_tokens,
            source_event, raw_excerpt, user_input, detail_path, auto_category, highlight_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event.get("id"),
        event.get("agent"),
        event.get("title"),
        event.get("project_name"),
        event.get("cwd"),
        event.get("session_id"),
        event.get("timestamp"),
        event.get("summary"),
        event.get("status"),
        event.get("model"),
        event.get("input_tokens"),
        event.get("output_tokens"),
        event.get("source_event"),
        event.get("raw_excerpt"),
        event.get("user_input"),
        event.get("detail_path"),
        event.get("auto_category"),
        event.get("highlight_data"),
    ))

    conn.commit()
    conn.close()


def get_latest() -> dict | None:
    """Get the most recent event."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM events
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_history(
    page: int = 1,
    per_page: int = 20,
    agent: str | None = None,
    project: str | None = None,
    time_days: str | None = None,
    category: str | None = None,
    search: str | None = None,
    search_mode: str = "normal",
    bookmarked: bool = False,
    date_start: str | None = None,
    date_end: str | None = None,
    sort_column: str = "timestamp",
    sort_direction: str = "desc",
) -> tuple[list[dict], int]:
    """Get paginated history with filtering and sorting.

    Returns:
        Tuple of (events list, total count)
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Build query
    where_clauses = []
    params = []

    if agent and agent != "all":
        where_clauses.append("agent = ?")
        params.append(agent)

    if project and project != "all":
        where_clauses.append("project_name = ?")
        params.append(project)

    if category and category != "all":
        where_clauses.append("auto_category = ?")
        params.append(category)

    if bookmarked:
        where_clauses.append("bookmarked = ?")
        params.append(True)

    if time_days and time_days != "all":
        if time_days == "today":
            where_clauses.append("date(timestamp) = date('now')")
        else:
            days = int(time_days)
            where_clauses.append("timestamp >= datetime('now', ?)")
            params.append(f'-{days} days')

    if date_start:
        where_clauses.append("date(timestamp) >= date(?)")
        params.append(date_start)

    if date_end:
        where_clauses.append("date(timestamp) <= date(?)")
        params.append(date_end)

    if search:
        # Both normal and regex use LIKE (regex mode allows SQL wildcards % and _)
        where_clauses.append("""
            (LOWER(summary) LIKE ? OR
             LOWER(user_input) LIKE ? OR
             LOWER(project_name) LIKE ? OR
             LOWER(agent) LIKE ?)
        """)
        # In regex mode, user can use % and _ wildcards directly
        if search_mode == "regex":
            search_param = search.lower()
        else:
            search_param = f"%{search.lower()}%"
        params.extend([search_param, search_param, search_param, search_param])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Validate sort column
    valid_columns = ["timestamp", "agent", "project_name", "user_input", "summary", "auto_category"]
    if sort_column not in valid_columns:
        sort_column = "timestamp"

    sort_direction = "DESC" if sort_direction.lower() == "desc" else "ASC"

    # Get total count
    count_sql = f"SELECT COUNT(*) FROM events WHERE {where_sql}"
    cursor.execute(count_sql, params.copy())
    total = cursor.fetchone()[0]

    # Get paginated results
    offset = (page - 1) * per_page
    data_sql = f"""
        SELECT * FROM events
        WHERE {where_sql}
        ORDER BY {sort_column} {sort_direction}
        LIMIT ? OFFSET ?
    """
    query_params = params.copy()
    query_params.extend([per_page, offset])
    cursor.execute(data_sql, query_params)

    rows = cursor.fetchall()

    # Get unique projects for filter dropdown
    cursor.execute("SELECT DISTINCT project_name FROM events ORDER BY project_name")
    projects = [row[0] for row in cursor.fetchall() if row[0]]

    # Get unique categories for filter dropdown
    cursor.execute("SELECT DISTINCT auto_category FROM events WHERE auto_category IS NOT NULL ORDER BY auto_category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]

    conn.close()

    events = [dict(row) for row in rows]
    return events, total, projects, categories


def get_stats() -> dict:
    """Get database statistics."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT agent, COUNT(*) as count FROM events GROUP BY agent")
    agent_counts = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT project_name, COUNT(*) as count
        FROM events
        GROUP BY project_name
        ORDER BY count DESC
        LIMIT 5
    """)
    top_projects = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]

    # Get date-based stats
    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE timestamp >= datetime('now', '-7 days')
    """)
    last_7_days = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE timestamp >= datetime('now', '-30 days')
    """)
    last_30_days = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE timestamp >= datetime('now', '-90 days')
    """)
    last_90_days = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE timestamp >= datetime('now', '-365 days')
    """)
    last_365_days = cursor.fetchone()[0]

    conn.close()

    return {
        "total_events": total_events,
        "agent_counts": agent_counts,
        "top_projects": top_projects,
        "date_stats": {
            "last_7_days": last_7_days,
            "last_30_days": last_30_days,
            "last_90_days": last_90_days,
            "last_365_days": last_365_days,
        },
    }


def delete_events_before_days(days: int) -> dict:
    """Delete events older than specified days.

    Returns:
        Dict with deleted count and remaining count.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Get count before deletion
    cursor.execute("SELECT COUNT(*) FROM events")
    total_before = cursor.fetchone()[0]

    # Delete old events
    cursor.execute("""
        DELETE FROM events
        WHERE timestamp < datetime('now', ?)
    """, (f'-{days} days',))

    deleted_count = cursor.rowcount

    # Get count after deletion
    cursor.execute("SELECT COUNT(*) FROM events")
    total_after = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return {
        "deleted": deleted_count,
        "remaining": total_after,
        "before": total_before,
    }


def delete_all_events() -> int:
    """Delete all events."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM events")
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted


# =====================
# Tag Functions
# =====================

def get_tags() -> list[dict]:
    """Get all tags."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tags ORDER BY usage_count DESC, name")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def create_tag(name: str, color: str = "#7b61ff") -> dict:
    """Create a new tag."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    tag_id = f"tag-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        INSERT INTO tags (id, name, color, usage_count, created_at)
        VALUES (?, ?, ?, 0, ?)
    """, (tag_id, name, color, timestamp))

    conn.commit()
    conn.close()

    return {"id": tag_id, "name": name, "color": color, "usage_count": 0}


def update_tag(tag_id: str, name: str | None = None, color: str | None = None) -> dict | None:
    """Update a tag."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if name:
        updates.append("name = ?")
        params.append(name)

    if color:
        updates.append("color = ?")
        params.append(color)

    if not updates:
        conn.close()
        return None

    params.append(tag_id)
    cursor.execute(f"UPDATE tags SET {', '.join(updates)} WHERE id = ?", params)

    conn.commit()

    cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def delete_tag(tag_id: str) -> bool:
    """Delete a tag."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Remove all event associations
    cursor.execute("DELETE FROM event_tags WHERE tag_id = ?", (tag_id,))

    # Delete tag
    cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


def get_event_tags(event_id: str) -> list[dict]:
    """Get tags for an event."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.* FROM tags t
        JOIN event_tags et ON t.id = et.tag_id
        WHERE et.event_id = ?
        ORDER BY t.name
    """, (event_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def add_event_tag(event_id: str, tag_id: str) -> bool:
    """Add a tag to an event."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        cursor.execute("""
            INSERT INTO event_tags (event_id, tag_id, created_at)
            VALUES (?, ?, ?)
        """, (event_id, tag_id, timestamp))

        # Update usage count
        cursor.execute("UPDATE tags SET usage_count = usage_count + 1 WHERE id = ?", (tag_id,))

        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Already exists


def remove_event_tag(event_id: str, tag_id: str) -> bool:
    """Remove a tag from an event."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM event_tags WHERE event_id = ? AND tag_id = ?", (event_id, tag_id))
    removed = cursor.rowcount > 0

    if removed:
        cursor.execute("UPDATE tags SET usage_count = usage_count - 1 WHERE id = ?", (tag_id,))

    conn.commit()
    conn.close()

    return removed


def set_event_tags(event_id: str, tag_ids: list[str]) -> None:
    """Set all tags for an event (replace existing)."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Get current tags
    cursor.execute("SELECT tag_id FROM event_tags WHERE event_id = ?", (event_id,))
    current_tags = [row[0] for row in cursor.fetchall()]

    # Remove old tags
    for tag_id in current_tags:
        if tag_id not in tag_ids:
            cursor.execute("DELETE FROM event_tags WHERE event_id = ? AND tag_id = ?", (event_id, tag_id))
            cursor.execute("UPDATE tags SET usage_count = usage_count - 1 WHERE id = ?", (tag_id,))

    # Add new tags
    timestamp = datetime.now(timezone.utc).isoformat()
    for tag_id in tag_ids:
        if tag_id not in current_tags:
            try:
                cursor.execute("""
                    INSERT INTO event_tags (event_id, tag_id, created_at)
                    VALUES (?, ?, ?)
                """, (event_id, tag_id, timestamp))
                cursor.execute("UPDATE tags SET usage_count = usage_count + 1 WHERE id = ?", (tag_id,))
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()


# =====================
# Category Functions
# =====================

def get_category_rules() -> list[dict]:
    """Get all category rules."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM category_rules ORDER BY priority")
    rows = cursor.fetchall()
    conn.close()

    rules = []
    for row in rows:
        rule = dict(row)
        rule["keywords"] = json.loads(rule["keywords"] or "[]")
        rule["tools"] = json.loads(rule["tools"] or "[]")
        rules.append(rule)

    return rules


def update_category_rule(rule_id: str, **kwargs) -> dict | None:
    """Update a category rule."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    for key, value in kwargs.items():
        if key in ["keywords", "tools"]:
            updates.append(f"{key} = ?")
            params.append(json.dumps(value))
        elif key in ["category", "priority", "color", "enabled"]:
            updates.append(f"{key} = ?")
            params.append(value)

    if not updates:
        conn.close()
        return None

    params.append(rule_id)
    cursor.execute(f"UPDATE category_rules SET {', '.join(updates)} WHERE id = ?", params)

    conn.commit()

    cursor.execute("SELECT * FROM category_rules WHERE id = ?", (rule_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


# =====================
# Export Functions
# =====================

def get_events_for_export(
    agent: str | None = None,
    project: str | None = None,
    category: str | None = None,
    time_days: str | None = None,
) -> list[dict]:
    """Get events for export (all matching, no pagination)."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if agent and agent != "all":
        where_clauses.append("agent = ?")
        params.append(agent)

    if project and project != "all":
        where_clauses.append("project_name = ?")
        params.append(project)

    if category and category != "all":
        where_clauses.append("auto_category = ?")
        params.append(category)

    if time_days and time_days != "all":
        if time_days == "today":
            where_clauses.append("date(timestamp) = date('now')")
        else:
            days = int(time_days)
            where_clauses.append("timestamp >= datetime('now', ?)")
            params.append(f'-{days} days')

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    cursor.execute(f"SELECT * FROM events WHERE {where_sql} ORDER BY timestamp DESC", params)
    rows = cursor.fetchall()

    # Get tags for each event
    events = []
    for row in rows:
        event = dict(row)
        event_id = event["id"]
        cursor.execute("""
            SELECT t.name FROM tags t
            JOIN event_tags et ON t.id = et.tag_id
            WHERE et.event_id = ?
            ORDER BY t.name
        """, (event_id,))
        event["tags"] = [row[0] for row in cursor.fetchall()]
        events.append(event)

    conn.close()
    return events