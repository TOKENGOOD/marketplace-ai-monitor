import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _safe_alter(c, sql):
    try:
        c.execute(sql)
    except Exception:
        # Column may already exist; ignore
        pass

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # ---- Profiles table (as in earlier version) ----
    c.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        keywords TEXT DEFAULT '',
        price_min_cents INTEGER,
        price_max_cents INTEGER,
        min_score REAL DEFAULT 0.6,
        chat_id TEXT
    );
    """)

    # ---- Listings table + new columns ----
    c.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile TEXT,
        title TEXT,
        price_cents INTEGER,
        url TEXT,
        created_at TEXT,
        score REAL DEFAULT 0.0,
        reason TEXT,
        UNIQUE(url, profile)
    );
    """)
    _safe_alter(c, "ALTER TABLE listings ADD COLUMN status TEXT")
    _safe_alter(c, "ALTER TABLE listings ADD COLUMN security_score INTEGER")
    _safe_alter(c, "ALTER TABLE listings ADD COLUMN ai_model TEXT")
    _safe_alter(c, "ALTER TABLE listings ADD COLUMN ai_reasons TEXT")

    conn.commit()
    conn.close()

# ---------- Profile helpers (backward compatible) ----------
def list_profiles():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM profiles ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_profile(pid: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM profiles WHERE id = ?", (pid,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_profile(data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO profiles (name, keywords, price_min_cents, price_max_cents, min_score, chat_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data.get('name'),
            data.get('keywords', ''),
            data.get('price_min_cents'),
            data.get('price_max_cents'),
            data.get('min_score', 0.6),
            data.get('chat_id')
        )
    )
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid

def update_profile(pid: int, data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """UPDATE profiles
               SET name=?, keywords=?, price_min_cents=?, price_max_cents=?, min_score=?, chat_id=?
               WHERE id = ?""",
        (
            data.get('name'),
            data.get('keywords', ''),
            data.get('price_min_cents'),
            data.get('price_max_cents'),
            data.get('min_score', 0.6),
            data.get('chat_id'),
            pid
        )
    )
    conn.commit()
    conn.close()

def delete_profile(pid: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM profiles WHERE id = ?", (pid,))
    conn.commit()
    conn.close()

# ---------- Listings helpers (with security fields) ----------
def upsert_listing(item, profile):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT OR IGNORE INTO listings
              (profile, title, price_cents, url, created_at, score, reason, status, security_score, ai_model, ai_reasons)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            profile,
            item.get("title"),
            item.get("price_cents"),
            item.get("url"),
            item.get("created_at"),
            item.get("score", 0.0),
            item.get("reason", ""),
            item.get("status"),
            item.get("security_score"),
            item.get("ai_model"),
            item.get("ai_reasons"),
        )
    )
    c.execute(
        """UPDATE listings
               SET title=?, price_cents=?, created_at=?, score=?, reason=?, status=?, security_score=?, ai_model=?, ai_reasons=?
               WHERE url=? AND profile=?""", 
        (
            item.get("title"),
            item.get("price_cents"),
            item.get("created_at"),
            item.get("score", 0.0),
            item.get("reason", ""),
            item.get("status"),
            item.get("security_score"),
            item.get("ai_model"),
            item.get("ai_reasons"),
            item.get("url"),
            profile,
        )
    )
    conn.commit()
    # Return row id for linking to /item/{id}
    c.execute("SELECT id FROM listings WHERE url=? AND profile=?", (item.get("url"), profile))
    row = c.fetchone()
    conn.close()
    return row["id"] if row else None

def list_listings(min_score: float = 0.0, profile: str | None = None, status: str | None = None, security_min: int | None = None):
    conn = get_conn()
    c = conn.cursor()
    q = "SELECT * FROM listings WHERE score >= ?"
    args = [min_score]
    if profile:
        q += " AND profile = ?"; args.append(profile)
    if status:
        q += " AND status = ?"; args.append(status)
    if security_min is not None:
        q += " AND security_score >= ?"; args.append(security_min)
    q += " ORDER BY created_at DESC, id DESC LIMIT 500"
    c.execute(q, tuple(args))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_listing(item_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM listings WHERE id = ?", (item_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None
