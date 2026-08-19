import sqlite3
from contextlib import contextmanager

DB_PATH = "obuna_bot.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                coins INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                ig_link TEXT NOT NULL,
                remaining INTEGER NOT NULL,
                coin_cost INTEGER NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                worker_id INTEGER NOT NULL,
                photo_file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_or_create_user(user_id, username):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (user_id, username, coins) VALUES (?, ?, 0)",
                (user_id, username),
            )
            row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        else:
            conn.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
        return dict(row)


def get_balance(user_id):
    with get_conn() as conn:
        row = conn.execute("SELECT coins FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row["coins"] if row else 0


def add_coins(user_id, amount):
    with get_conn() as conn:
        conn.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))


def deduct_coins(user_id, amount):
    with get_conn() as conn:
        conn.execute("UPDATE users SET coins = coins - ? WHERE user_id=?", (amount, user_id))


def create_task(owner_id, ig_link, count, coin_cost):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (owner_id, ig_link, remaining, coin_cost) VALUES (?, ?, ?, ?)",
            (owner_id, ig_link, count, coin_cost),
        )
        return cur.lastrowid


def get_next_task(worker_id):
    """Find an active task not owned by worker, and not already pending/approved by worker."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM tasks
            WHERE active=1 AND remaining>0 AND owner_id != ?
            AND task_id NOT IN (
                SELECT task_id FROM submissions
                WHERE worker_id=? AND status IN ('pending','approved')
            )
            ORDER BY created_at ASC LIMIT 1
            """,
            (worker_id, worker_id),
        ).fetchone()
        return dict(row) if row else None


def create_submission(task_id, worker_id, photo_file_id):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO submissions (task_id, worker_id, photo_file_id) VALUES (?, ?, ?)",
            (task_id, worker_id, photo_file_id),
        )
        return cur.lastrowid


def get_submission(submission_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM submissions WHERE submission_id=?", (submission_id,)).fetchone()
        return dict(row) if row else None


def get_task(task_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        return dict(row) if row else None


def approve_submission(submission_id):
    with get_conn() as conn:
        sub = conn.execute("SELECT * FROM submissions WHERE submission_id=?", (submission_id,)).fetchone()
        if not sub or sub["status"] != "pending":
            return None
        task = conn.execute("SELECT * FROM tasks WHERE task_id=?", (sub["task_id"],)).fetchone()
        conn.execute("UPDATE submissions SET status='approved' WHERE submission_id=?", (submission_id,))
        conn.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (task["coin_cost"], sub["worker_id"]))
        new_remaining = task["remaining"] - 1
        conn.execute(
            "UPDATE tasks SET remaining=?, active=? WHERE task_id=?",
            (new_remaining, 1 if new_remaining > 0 else 0, task["task_id"]),
        )
        return {"worker_id": sub["worker_id"], "coin_cost": task["coin_cost"], "task_id": task["task_id"]}


def reject_submission(submission_id):
    with get_conn() as conn:
        sub = conn.execute("SELECT * FROM submissions WHERE submission_id=?", (submission_id,)).fetchone()
        if not sub or sub["status"] != "pending":
            return None
        conn.execute("UPDATE submissions SET status='rejected' WHERE submission_id=?", (submission_id,))
        return {"worker_id": sub["worker_id"]}


def get_stats():
    with get_conn() as conn:
        users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        tasks = conn.execute("SELECT COUNT(*) c FROM tasks WHERE active=1").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) c FROM submissions WHERE status='pending'").fetchone()["c"]
        approved = conn.execute("SELECT COUNT(*) c FROM submissions WHERE status='approved'").fetchone()["c"]
        return {"users": users, "active_tasks": tasks, "pending": pending, "approved": approved}


def get_top_users(limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, coins FROM users ORDER BY coins DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
