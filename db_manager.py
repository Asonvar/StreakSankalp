"""
DatabaseManager — SQLite-backed persistence layer for StreakSankalp habit tracker.

Tables
------
habits : id (PK), name (UNIQUE), created_at (ISO-8601 default CURRENT_TIMESTAMP)
logs   : id (PK), habit_id (FK → habits.id), log_date (TEXT), status (TEXT)

No ORM is used; every query is raw SQL executed via the stdlib `sqlite3` module.
"""

import sqlite3
from datetime import date, datetime
from typing import Optional


class DatabaseManager:
    """Manages all database operations for the habit tracker."""

    # ------------------------------------------------------------------ #
    #  Initialisation & schema bootstrapping
    # ------------------------------------------------------------------ #

    def __init__(self, db_path: str = "tracker.db") -> None:
        """
        Open (or create) the SQLite database at *db_path* and ensure
        both core tables exist.

        Parameters
        ----------
        db_path : str
            Filesystem path to the SQLite file.  Defaults to ``tracker.db``
            in the current working directory.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)

        # Return rows as sqlite3.Row so we can access columns by name.
        self.conn.row_factory = sqlite3.Row

        # Enable foreign-key enforcement (off by default in SQLite).
        self.conn.execute("PRAGMA foreign_keys = ON")

        self._create_tables()

    def _create_tables(self) -> None:
        """Create the ``habits`` and ``logs`` tables if they do not already exist."""

        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL UNIQUE,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id  INTEGER NOT NULL,
                log_date  TEXT    NOT NULL,
                status    TEXT    NOT NULL DEFAULT 'done',
                FOREIGN KEY (habit_id) REFERENCES habits (id)
                    ON DELETE CASCADE,
                UNIQUE (habit_id, log_date)          -- prevent duplicate logs
            );
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------ #
    #  CRUD — Habits
    # ------------------------------------------------------------------ #

    def add_habit(self, name: str) -> int:
        """
        Insert a new habit and return its auto-generated ID.

        Parameters
        ----------
        name : str
            Human-readable habit name (e.g. "Meditate 10 min").

        Returns
        -------
        int
            The ``id`` of the newly created habit row.

        Raises
        ------
        sqlite3.IntegrityError
            If a habit with the same *name* already exists.
        """
        cursor = self.conn.execute(
            "INSERT INTO habits (name) VALUES (?)",
            (name,),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_all_habits(self) -> list[dict]:
        """
        Retrieve every habit, ordered by creation date (newest first).

        Returns
        -------
        list[dict]
            Each dict contains ``id``, ``name``, and ``created_at``.
        """
        cursor = self.conn.execute(
            "SELECT id, name, created_at FROM habits ORDER BY created_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------ #
    #  CRUD — Logs
    # ------------------------------------------------------------------ #

    def log_habit(
        self,
        habit_id: int,
        log_date: Optional[str] = None,
        status: str = "done",
    ) -> int:
        """
        Record a habit completion (or skip) for a specific date.

        Parameters
        ----------
        habit_id : int
            FK referencing ``habits.id``.
        log_date : str | None
            ISO-8601 date string (``YYYY-MM-DD``).  Defaults to today.
        status : str
            Free-text status label — typically ``"done"`` or ``"skipped"``.

        Returns
        -------
        int
            The ``id`` of the newly created log row.

        Raises
        ------
        sqlite3.IntegrityError
            If a log for this habit + date combination already exists,
            or if *habit_id* does not reference a valid habit.
        """
        if log_date is None:
            log_date = date.today().isoformat()

        cursor = self.conn.execute(
            "INSERT INTO logs (habit_id, log_date, status) VALUES (?, ?, ?)",
            (habit_id, log_date, status),
        )
        self.conn.commit()
        return cursor.lastrowid

    # ------------------------------------------------------------------ #
    #  Analytics
    # ------------------------------------------------------------------ #

    def get_completion_percentage(self, habit_id: int) -> float:
        """
        Calculate what percentage of days since the habit was created
        have a ``"done"`` log entry.

        Formula
        -------
        ``completion % = (days_with_done_status / total_days_since_creation) × 100``

        *total_days_since_creation* is computed as the number of calendar
        days from ``habits.created_at`` up to and including today.
        A minimum of **1** is used to avoid division-by-zero on the
        creation day itself.

        Parameters
        ----------
        habit_id : int
            The habit whose completion rate is requested.

        Returns
        -------
        float
            Completion percentage rounded to two decimal places,
            or ``0.0`` if the habit does not exist.
        """

        # 1. Fetch the habit's creation date.
        row = self.conn.execute(
            "SELECT created_at FROM habits WHERE id = ?",
            (habit_id,),
        ).fetchone()

        if row is None:
            return 0.0

        created_at = datetime.fromisoformat(row["created_at"]).date()
        total_days = max((date.today() - created_at).days + 1, 1)

        # 2. Count distinct dates where status = 'done'.
        done_row = self.conn.execute(
            """
            SELECT COUNT(DISTINCT log_date) AS done_days
              FROM logs
             WHERE habit_id = ?
               AND status    = 'done'
            """,
            (habit_id,),
        ).fetchone()

        done_days = done_row["done_days"] if done_row else 0

        # 3. Compute and return the percentage.
        return round((done_days / total_days) * 100, 2)

    # ------------------------------------------------------------------ #
    #  Cleanup
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """Close the underlying database connection."""
        self.conn.close()

    def __enter__(self):
        """Support usage as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure the connection is closed when leaving the ``with`` block."""
        self.close()


# ====================================================================== #
#  Quick smoke-test (runs only when the file is executed directly)
# ====================================================================== #
if __name__ == "__main__":
    with DatabaseManager("tracker.db") as db:
        # --- Add habits ---
        h1 = db.add_habit("Meditate 10 min")
        h2 = db.add_habit("Read 20 pages")
        print(f"✅ Created habits → ids: {h1}, {h2}")

        # --- Log completions ---
        db.log_habit(h1, "2026-03-20")
        db.log_habit(h1, "2026-03-21")
        db.log_habit(h1, "2026-03-22")
        db.log_habit(h2, "2026-03-21")
        print("✅ Logged completions")

        # --- List all habits ---
        print("\n📋 All habits:")
        for habit in db.get_all_habits():
            print(f"   {habit['id']}: {habit['name']} (created {habit['created_at']})")

        # --- Completion percentages ---
        print(f"\n📊 Completion for habit {h1}: {db.get_completion_percentage(h1)}%")
        print(f"📊 Completion for habit {h2}: {db.get_completion_percentage(h2)}%")
