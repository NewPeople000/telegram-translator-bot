"""
Database layer — SQLite via aiosqlite (async-safe).

Tables:
  users        — registered users & their preferences
  vocabulary   — saved words / phrases per user
  quiz_history — quiz attempt results
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Tuple

import aiosqlite

from config import DATABASE_PATH, DEFAULT_SOURCE_LANG, DEFAULT_TARGET_LANG

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Schema
# ──────────────────────────────────────────────────────────────────────────────
_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY,
    username       TEXT,
    full_name      TEXT,
    source_lang    TEXT    NOT NULL DEFAULT 'auto',
    target_lang    TEXT    NOT NULL DEFAULT 'en',
    created_at     TEXT    NOT NULL,
    last_active    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    original       TEXT    NOT NULL,
    translation    TEXT    NOT NULL,
    src_lang       TEXT    NOT NULL,
    tgt_lang       TEXT    NOT NULL,
    created_at     TEXT    NOT NULL,
    next_review    TEXT,
    review_count   INTEGER NOT NULL DEFAULT 0,
    correct_count  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, original, tgt_lang)
);

CREATE TABLE IF NOT EXISTS quiz_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id       INTEGER REFERENCES vocabulary(id) ON DELETE SET NULL,
    answered_at    TEXT    NOT NULL,
    is_correct     INTEGER NOT NULL   -- 0 / 1
);

CREATE INDEX IF NOT EXISTS idx_vocab_user   ON vocabulary(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_user    ON quiz_history(user_id);
"""


# ──────────────────────────────────────────────────────────────────────────────
# Connection helper
# ──────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def _conn():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


# ──────────────────────────────────────────────────────────────────────────────
# Initialisation
# ──────────────────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Create tables (idempotent) and migrate schema if needed."""
    async with _conn() as db:
        await db.executescript(_SCHEMA)
        # Check if quiz_history.vocab_id has NOT NULL constraint and alter if necessary
        async with db.execute("PRAGMA table_info(quiz_history)") as cur:
            columns = await cur.fetchall()
            vocab_col = next((c for c in columns if c[1] == "vocab_id"), None)
            # If vocab_id is NOT NULL (c[3] == 1), migrate table
            if vocab_col and vocab_col[3] == 1:
                logger.info("Migrating quiz_history table to allow NULL vocab_id...")
                await db.executescript("""
                    CREATE TABLE IF NOT EXISTS quiz_history_new (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id        INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        vocab_id       INTEGER REFERENCES vocabulary(id) ON DELETE SET NULL,
                        answered_at    TEXT    NOT NULL,
                        is_correct     INTEGER NOT NULL
                    );
                    INSERT INTO quiz_history_new (id, user_id, vocab_id, answered_at, is_correct)
                    SELECT id, user_id, vocab_id, answered_at, is_correct FROM quiz_history;
                    DROP TABLE quiz_history;
                    ALTER TABLE quiz_history_new RENAME TO quiz_history;
                    CREATE INDEX IF NOT EXISTS idx_quiz_user ON quiz_history(user_id);
                """)
        await db.commit()
    logger.info("Database initialised at %s", DATABASE_PATH)


# ──────────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────────
async def upsert_user(
    user_id: int,
    username: Optional[str],
    full_name: str,
) -> None:
    now = datetime.utcnow().isoformat()
    async with _conn() as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name, source_lang, target_lang, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username    = excluded.username,
                full_name   = excluded.full_name,
                last_active = excluded.last_active
            """,
            (user_id, username, full_name, DEFAULT_SOURCE_LANG, DEFAULT_TARGET_LANG, now, now),
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[aiosqlite.Row]:
    async with _conn() as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            return await cur.fetchone()


async def update_languages(user_id: int, source: str, target: str) -> None:
    now = datetime.utcnow().isoformat()
    async with _conn() as db:
        await db.execute(
            "UPDATE users SET source_lang = ?, target_lang = ?, last_active = ? WHERE user_id = ?",
            (source, target, now, user_id),
        )
        await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Vocabulary
# ──────────────────────────────────────────────────────────────────────────────
async def save_word(
    user_id: int,
    original: str,
    translation: str,
    src_lang: str,
    tgt_lang: str,
) -> bool:
    """Returns True if newly inserted, False if duplicate."""
    now = datetime.utcnow().isoformat()
    async with _conn() as db:
        try:
            await db.execute(
                """
                INSERT INTO vocabulary
                    (user_id, original, translation, src_lang, tgt_lang, created_at, review_count, correct_count)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
                """,
                (user_id, original.strip(), translation.strip(), src_lang, tgt_lang, now),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_vocab_list(user_id: int, limit: int = 20, offset: int = 0) -> List[aiosqlite.Row]:
    async with _conn() as db:
        async with db.execute(
            """
            SELECT * FROM vocabulary
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        ) as cur:
            return await cur.fetchall()


async def count_vocab(user_id: int) -> int:
    async with _conn() as db:
        async with db.execute(
            "SELECT COUNT(*) FROM vocabulary WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def delete_word(user_id: int, vocab_id: int) -> bool:
    async with _conn() as db:
        cur = await db.execute(
            "DELETE FROM vocabulary WHERE id = ? AND user_id = ?", (vocab_id, user_id)
        )
        await db.commit()
        return cur.rowcount > 0


async def get_quiz_words(user_id: int, batch: int = 5) -> List[aiosqlite.Row]:
    """Fetch words ordered by least-reviewed first (spaced-repetition light)."""
    async with _conn() as db:
        async with db.execute(
            """
            SELECT * FROM vocabulary
            WHERE user_id = ?
            ORDER BY review_count ASC, RANDOM()
            LIMIT ?
            """,
            (user_id, batch),
        ) as cur:
            return await cur.fetchall()


async def record_quiz_result(
    user_id: int, is_correct: bool, vocab_id: Optional[int] = None
) -> None:
    now = datetime.utcnow().isoformat()
    async with _conn() as db:
        await db.execute(
            "INSERT INTO quiz_history (user_id, vocab_id, answered_at, is_correct) VALUES (?, ?, ?, ?)",
            (user_id, vocab_id, now, int(is_correct)),
        )
        if vocab_id is not None:
            if is_correct:
                await db.execute(
                    "UPDATE vocabulary SET review_count = review_count + 1, correct_count = correct_count + 1 WHERE id = ?",
                    (vocab_id,),
                )
            else:
                await db.execute(
                    "UPDATE vocabulary SET review_count = review_count + 1 WHERE id = ?",
                    (vocab_id,),
                )
        await db.commit()


async def get_user_stats(user_id: int) -> dict:
    async with _conn() as db:
        async with db.execute(
            "SELECT COUNT(*) FROM vocabulary WHERE user_id = ?", (user_id,)
        ) as cur:
            total_words = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*), SUM(is_correct) FROM quiz_history WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
            total_quizzes = row[0] or 0
            correct_quizzes = row[1] or 0

    accuracy = round((correct_quizzes / total_quizzes) * 100) if total_quizzes else 0
    return {
        "total_words": total_words,
        "total_quizzes": total_quizzes,
        "correct_quizzes": correct_quizzes,
        "accuracy": accuracy,
    }
