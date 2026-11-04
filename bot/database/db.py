"""Asynchronous SQLite database operations."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiosqlite
from bot.config import config


def _utcnow_iso() -> str:
    """Return ISO format string of current UTC time."""
    return datetime.now(timezone.utc).isoformat()


@asynccontextmanager
async def get_connection(
    db_path: Optional[str] = None,
) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Provide an async context manager for database connection."""
    path = db_path or config.database_path
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables and schema."""
    async with get_connection(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS emotions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                category_key TEXT NOT NULL,
                emotion_key TEXT NOT NULL,
                emotion_label TEXT NOT NULL,
                need_key TEXT NOT NULL,
                need_label TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged_at TIMESTAMP,
                reaction_key TEXT,
                reaction_label TEXT,
                reply_note TEXT,
                recipient_message_id INTEGER
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_feelings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                feeling_name TEXT NOT NULL,
                emoji TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def log_emotion(
    sender_id: int,
    recipient_id: int,
    category_key: str,
    emotion_key: str,
    emotion_label: str,
    need_key: str,
    need_label: str,
    note: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Insert a new emotion record and return its row ID."""
    async with get_connection(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO emotions_log (
                sender_id, recipient_id, category_key, emotion_key, emotion_label,
                need_key, need_label, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sender_id,
                recipient_id,
                category_key,
                emotion_key,
                emotion_label,
                need_key,
                need_label,
                note,
                _utcnow_iso(),
            ),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def set_recipient_message_id(
    log_id: int, message_id: int, db_path: Optional[str] = None
) -> None:
    """Store the Telegram message ID sent to the recipient."""
    async with get_connection(db_path) as db:
        await db.execute(
            "UPDATE emotions_log SET recipient_message_id = ? WHERE id = ?",
            (message_id, log_id),
        )
        await db.commit()


async def record_reaction(
    log_id: int, reaction_key: str, reaction_label: str, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Record partner's acknowledgment reaction to an emotion."""
    async with get_connection(db_path) as db:
        now_str = _utcnow_iso()
        await db.execute(
            """
            UPDATE emotions_log
            SET acknowledged_at = ?, reaction_key = ?, reaction_label = ?
            WHERE id = ?
            """,
            (now_str, reaction_key, reaction_label, log_id),
        )
        await db.commit()
        async with db.execute("SELECT * FROM emotions_log WHERE id = ?", (log_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def record_reply_note(
    log_id: int, reply_note: str, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Record partner's gentle follow-up note."""
    async with get_connection(db_path) as db:
        await db.execute(
            "UPDATE emotions_log SET reply_note = ? WHERE id = ?",
            (reply_note, log_id),
        )
        await db.commit()
        async with db.execute("SELECT * FROM emotions_log WHERE id = ?", (log_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_emotion_by_id(
    log_id: int, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Fetch an emotion log by its ID."""
    async with get_connection(db_path) as db:
        async with db.execute("SELECT * FROM emotions_log WHERE id = ?", (log_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_history(
    limit: int = 10, db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch the latest emotion entries."""
    async with get_connection(db_path) as db:
        async with db.execute(
            """
            SELECT * FROM emotions_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculate emotional statistics and trends."""
    async with get_connection(db_path) as db:
        async with db.execute("SELECT COUNT(*) as total FROM emotions_log") as cursor:
            total_row = await cursor.fetchone()
            total = total_row["total"] if total_row else 0

        async with db.execute(
            "SELECT COUNT(*) as acked FROM emotions_log WHERE acknowledged_at IS NOT NULL"
        ) as cursor:
            acked_row = await cursor.fetchone()
            acknowledged = acked_row["acked"] if acked_row else 0

        async with db.execute(
            """
            SELECT category_key, COUNT(*) as cnt
            FROM emotions_log
            GROUP BY category_key
            ORDER BY cnt DESC
            """
        ) as cursor:
            cat_rows = await cursor.fetchall()
            categories = {r["category_key"]: r["cnt"] for r in cat_rows}

        return {
            "total_sent": total,
            "acknowledged": acknowledged,
            "categories": categories,
        }


async def add_custom_feeling(
    user_id: int, feeling_name: str, emoji: str, db_path: Optional[str] = None
) -> int:
    """Save a couple's custom feeling to the database."""
    async with get_connection(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO custom_feelings (user_id, feeling_name, emoji, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, feeling_name.strip(), emoji.strip(), _utcnow_iso()),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_custom_feelings(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all custom feelings."""
    async with get_connection(db_path) as db:
        async with db.execute(
            "SELECT * FROM custom_feelings ORDER BY id ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def delete_custom_feeling(
    feeling_id: int, db_path: Optional[str] = None
) -> bool:
    """Delete a custom feeling by ID."""
    async with get_connection(db_path) as db:
        cursor = await db.execute("DELETE FROM custom_feelings WHERE id = ?", (feeling_id,))
        await db.commit()
        return cursor.rowcount > 0
