"""
db.py - Modulo per la persistenza dei libri scansionati in SQLite.
"""

import sqlite3
from datetime import datetime, timezone


def init_db(path: str = "books.db") -> sqlite3.Connection:
    """Crea la tabella books se non esiste e restituisce la connessione."""
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            isbn         TEXT PRIMARY KEY,
            title        TEXT,
            authors      TEXT,
            publish_date TEXT,
            publisher    TEXT,
            pages        INTEGER,
            scanned_at   TEXT,
            source       TEXT
        )
    """)
    conn.commit()
    return conn


def save_book(
    conn: sqlite3.Connection,
    isbn: str,
    title: str,
    authors: str,
    publish_date: str,
    publisher: str,
    pages: int | None,
    source: str,
) -> None:
    """Inserisce un libro nel database, ignora duplicati."""
    conn.execute(
        """
        INSERT OR IGNORE INTO books
            (isbn, title, authors, publish_date, publisher, pages, scanned_at, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            isbn,
            title,
            authors,
            publish_date,
            publisher,
            pages,
            datetime.now(timezone.utc).isoformat(),
            source,
        ),
    )
    conn.commit()
