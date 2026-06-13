import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from src.models.email import Email, EmailAnalysis, DailyBriefing, EmailCategory, Priority

DB_PATH = Path("stafy.db")


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                thread_id TEXT,
                subject TEXT,
                sender TEXT,
                sender_email TEXT,
                recipient TEXT,
                date TEXT,
                body TEXT,
                snippet TEXT,
                is_read INTEGER DEFAULT 0,
                labels TEXT DEFAULT '[]',
                fetched_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS email_analyses (
                email_id TEXT PRIMARY KEY,
                category TEXT,
                priority INTEGER,
                sentiment TEXT,
                summary TEXT,
                key_points TEXT,
                action_required INTEGER DEFAULT 0,
                action_description TEXT,
                deadline TEXT,
                draft_reply TEXT,
                analyzed_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(email_id) REFERENCES emails(id)
            );

            CREATE TABLE IF NOT EXISTS daily_briefings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                total_emails INTEGER,
                urgent_count INTEGER,
                important_count INTEGER,
                action_required_count INTEGER,
                executive_summary TEXT,
                priority_list TEXT,
                alerts TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_email(email: Email):
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO emails
               (id, thread_id, subject, sender, sender_email, recipient, date, body, snippet, is_read, labels)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email.id,
                email.thread_id,
                email.subject,
                email.sender,
                email.sender_email,
                email.recipient,
                email.date.isoformat(),
                email.body,
                email.snippet,
                int(email.is_read),
                json.dumps(email.labels),
            ),
        )


def save_analysis(analysis: EmailAnalysis):
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO email_analyses
               (email_id, category, priority, sentiment, summary, key_points,
                action_required, action_description, deadline, draft_reply, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                analysis.email_id,
                analysis.category.value,
                analysis.priority.value,
                analysis.sentiment,
                analysis.summary,
                json.dumps(analysis.key_points),
                int(analysis.action_required),
                analysis.action_description,
                analysis.deadline,
                analysis.draft_reply,
                analysis.analyzed_at.isoformat(),
            ),
        )


def get_emails_with_analysis(limit: int = 50, category: str = None) -> list[dict]:
    with get_conn() as conn:
        query = """
            SELECT e.*, a.category, a.priority, a.sentiment, a.summary,
                   a.key_points, a.action_required, a.action_description,
                   a.deadline, a.draft_reply, a.analyzed_at
            FROM emails e
            LEFT JOIN email_analyses a ON e.id = a.email_id
        """
        params = []
        if category:
            query += " WHERE a.category = ?"
            params.append(category)
        query += " ORDER BY COALESCE(a.priority, 0) DESC, e.date DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_email_by_id(email_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT e.*, a.category, a.priority, a.sentiment, a.summary,
                      a.key_points, a.action_required, a.action_description,
                      a.deadline, a.draft_reply, a.analyzed_at
               FROM emails e
               LEFT JOIN email_analyses a ON e.id = a.email_id
               WHERE e.id = ?""",
            (email_id,),
        ).fetchone()
        return dict(row) if row else None


def save_briefing(briefing: DailyBriefing):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO daily_briefings
               (date, total_emails, urgent_count, important_count, action_required_count,
                executive_summary, priority_list, alerts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                briefing.date.date().isoformat(),
                briefing.total_emails,
                briefing.urgent_count,
                briefing.important_count,
                briefing.action_required_count,
                briefing.executive_summary,
                json.dumps(briefing.priority_list),
                json.dumps(briefing.alerts),
            ),
        )


def get_latest_briefing() -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM daily_briefings ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_dashboard_stats() -> dict:
    with get_conn() as conn:
        today = date.today().isoformat()
        stats = conn.execute("""
            SELECT
                COUNT(CASE WHEN e.is_read = 0 THEN 1 END) as total_unread,
                COUNT(CASE WHEN a.category = 'urgent' THEN 1 END) as urgent,
                COUNT(CASE WHEN a.category = 'important' THEN 1 END) as important,
                COUNT(CASE WHEN a.draft_reply IS NOT NULL THEN 1 END) as with_drafts,
                COUNT(CASE WHEN date(e.fetched_at) = ? THEN 1 END) as processed_today
            FROM emails e
            LEFT JOIN email_analyses a ON e.id = a.email_id
        """, (today,)).fetchone()
        return dict(stats) if stats else {}
