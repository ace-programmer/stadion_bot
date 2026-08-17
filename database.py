import sqlite3
import math
from datetime import datetime
from config import DB_PATH

_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row


def init_db():
    cur = _conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            latitude REAL,
            longitude REAL,
            region TEXT,
            district TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS stadiums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT,
            region TEXT,
            district TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            phone TEXT,
            price INTEGER,
            status TEXT DEFAULT 'pending',  -- pending / approved / rejected
            created_at TEXT,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS stadium_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stadium_id INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (stadium_id) REFERENCES stadiums(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS stadium_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stadium_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            is_busy INTEGER DEFAULT 0,
            FOREIGN KEY (stadium_id) REFERENCES stadiums(id) ON DELETE CASCADE,
            UNIQUE(stadium_id, date, time)
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            stadium_id INTEGER NOT NULL,
            created_at TEXT,
            UNIQUE(telegram_id, stadium_id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    _conn.commit()
    # Eski bazalarda region/district ustunlari bo'lmasligi mumkin - migratsiya
    cur.execute("PRAGMA table_info(users)")
    existing_cols = {row["name"] for row in cur.fetchall()}
    if "region" not in existing_cols:
        cur.execute("ALTER TABLE users ADD COLUMN region TEXT")
    if "district" not in existing_cols:
        cur.execute("ALTER TABLE users ADD COLUMN district TEXT")

    cur.execute("PRAGMA table_info(stadiums)")
    stadium_cols = {row["name"] for row in cur.fetchall()}
    if "reject_reason" not in stadium_cols:
        cur.execute("ALTER TABLE stadiums ADD COLUMN reject_reason TEXT")
    if "reminder_sent" not in stadium_cols:
        cur.execute("ALTER TABLE stadiums ADD COLUMN reminder_sent INTEGER DEFAULT 0")
    _conn.commit()


# ---------------- USERS ----------------

def get_or_create_user(telegram_id: int, username: str, full_name: str):
    cur = _conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    if row:
        return row
    cur.execute(
        "INSERT INTO users (telegram_id, username, full_name, created_at) VALUES (?,?,?,?)",
        (telegram_id, username, full_name, datetime.now().isoformat()),
    )
    _conn.commit()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    return cur.fetchone()


def get_user_by_tg(telegram_id: int):
    cur = _conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    return cur.fetchone()


def update_user_phone(telegram_id: int, phone: str):
    _conn.execute("UPDATE users SET phone=? WHERE telegram_id=?", (phone, telegram_id))
    _conn.commit()


def update_user_location(telegram_id: int, lat: float, lon: float):
    _conn.execute(
        "UPDATE users SET latitude=?, longitude=? WHERE telegram_id=?",
        (lat, lon, telegram_id),
    )
    _conn.commit()


def update_user_region_district(telegram_id: int, region: str, district: str):
    _conn.execute(
        "UPDATE users SET region=?, district=? WHERE telegram_id=?",
        (region, district, telegram_id),
    )
    _conn.commit()


def get_all_users():
    cur = _conn.cursor()
    cur.execute("SELECT * FROM users")
    return cur.fetchall()


# ---------------- STADIUMS ----------------

def create_stadium(owner_id: int, data: dict) -> int:
    cur = _conn.cursor()
    cur.execute(
        """INSERT INTO stadiums (owner_id, name, region, district, address, latitude, longitude, phone, price, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?, 'pending', ?)""",
        (
            owner_id,
            data.get("name"),
            data.get("region"),
            data.get("district"),
            data.get("address"),
            data.get("latitude"),
            data.get("longitude"),
            data.get("phone"),
            data.get("price"),
            datetime.now().isoformat(),
        ),
    )
    _conn.commit()
    return cur.lastrowid


def add_stadium_photo(stadium_id: int, file_id: str, sort_order: int = 0):
    _conn.execute(
        "INSERT INTO stadium_photos (stadium_id, file_id, sort_order) VALUES (?,?,?)",
        (stadium_id, file_id, sort_order),
    )
    _conn.commit()


def get_stadium_photos(stadium_id: int):
    cur = _conn.cursor()
    cur.execute(
        "SELECT * FROM stadium_photos WHERE stadium_id=? ORDER BY sort_order", (stadium_id,)
    )
    return cur.fetchall()


def delete_stadium_photo(photo_id: int):
    _conn.execute("DELETE FROM stadium_photos WHERE id=?", (photo_id,))
    _conn.commit()


def get_stadium(stadium_id: int):
    cur = _conn.cursor()
    cur.execute("SELECT * FROM stadiums WHERE id=?", (stadium_id,))
    return cur.fetchone()


def update_stadium_field(stadium_id: int, field: str, value):
    allowed = {"name", "phone", "price", "address", "latitude", "longitude", "region", "district", "status"}
    if field not in allowed:
        raise ValueError("Ruxsat etilmagan maydon")
    _conn.execute(f"UPDATE stadiums SET {field}=? WHERE id=?", (value, stadium_id))
    _conn.commit()


def set_stadium_status(stadium_id: int, status: str):
    _conn.execute("UPDATE stadiums SET status=? WHERE id=?", (status, stadium_id))
    _conn.commit()


def set_stadium_reject_reason(stadium_id: int, reason: str):
    _conn.execute("UPDATE stadiums SET reject_reason=? WHERE id=?", (reason, stadium_id))
    _conn.commit()


def get_stadiums_by_status(status: str):
    cur = _conn.cursor()
    cur.execute("SELECT * FROM stadiums WHERE status=? ORDER BY created_at DESC", (status,))
    return cur.fetchall()


def delete_stadium(stadium_id: int):
    _conn.execute("DELETE FROM stadium_photos WHERE stadium_id=?", (stadium_id,))
    _conn.execute("DELETE FROM stadium_times WHERE stadium_id=?", (stadium_id,))
    _conn.execute("DELETE FROM stadiums WHERE id=?", (stadium_id,))
    _conn.commit()


def get_user_stadiums(owner_id: int, status: str = None):
    cur = _conn.cursor()
    if status:
        cur.execute(
            "SELECT * FROM stadiums WHERE owner_id=? AND status=? ORDER BY created_at DESC",
            (owner_id, status),
        )
    else:
        cur.execute(
            "SELECT * FROM stadiums WHERE owner_id=? ORDER BY created_at DESC", (owner_id,)
        )
    return cur.fetchall()


def get_pending_stadiums():
    cur = _conn.cursor()
    cur.execute("SELECT * FROM stadiums WHERE status='pending' ORDER BY created_at ASC")
    return cur.fetchall()


def search_stadiums(query: str):
    cur = _conn.cursor()
    like = f"%{query}%"
    cur.execute(
        """SELECT * FROM stadiums WHERE status='approved' AND
           (name LIKE ? OR address LIKE ? OR phone LIKE ? OR district LIKE ?)""",
        (like, like, like, like),
    )
    return cur.fetchall()


def filter_stadiums(region=None, district=None, max_price=None):
    q = "SELECT * FROM stadiums WHERE status='approved'"
    params = []
    if region:
        q += " AND region=?"
        params.append(region)
    if district:
        q += " AND district=?"
        params.append(district)
    if max_price:
        q += " AND price<=?"
        params.append(max_price)
    q += " ORDER BY created_at DESC"
    cur = _conn.cursor()
    cur.execute(q, params)
    return cur.fetchall()


def get_all_approved_stadiums():
    cur = _conn.cursor()
    cur.execute("SELECT * FROM stadiums WHERE status='approved'")
    return cur.fetchall()


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def get_nearest_stadiums(lat, lon, limit=10):
    stadiums = get_all_approved_stadiums()
    result = []
    for s in stadiums:
        if s["latitude"] is None or s["longitude"] is None:
            continue
        dist = haversine(lat, lon, s["latitude"], s["longitude"])
        result.append((dist, s))
    result.sort(key=lambda x: x[0])
    return result[:limit]


def find_nearby_stadium(lat, lon, max_km: float = 0.05, exclude_id: int = None):
    """Berilgan koordinataga juda yaqin (odatda bir xil) stadion bor-yo'qligini tekshiradi.
    Faqat 'pending' va 'approved' statusdagilar hisobga olinadi (rad etilganlar emas)."""
    cur = _conn.cursor()
    cur.execute(
        "SELECT * FROM stadiums WHERE status IN ('pending','approved') "
        "AND latitude IS NOT NULL AND longitude IS NOT NULL"
    )
    for r in cur.fetchall():
        if exclude_id and r["id"] == exclude_id:
            continue
        if haversine(lat, lon, r["latitude"], r["longitude"]) <= max_km:
            return r
    return None


# ---------------- ADMIN: QIDIRUV VA STATISTIKA ----------------

def search_all_stadiums_admin(query: str):
    """Admin uchun - statusidan qat'i nazar barcha stadionlar orasidan qidiradi."""
    cur = _conn.cursor()
    like = f"%{query}%"
    cur.execute(
        "SELECT * FROM stadiums WHERE name LIKE ? OR address LIKE ? OR phone LIKE ? ORDER BY created_at DESC",
        (like, like, like),
    )
    return cur.fetchall()


def count_users() -> int:
    cur = _conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    return cur.fetchone()["c"]


def count_stadiums_by_status(status: str) -> int:
    cur = _conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM stadiums WHERE status=?", (status,))
    return cur.fetchone()["c"]


def count_all_stadiums() -> int:
    cur = _conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM stadiums")
    return cur.fetchone()["c"]


# ---------------- JADVAL ESLATMASI (egaga) ----------------

def get_approved_stadiums_needing_reminder():
    """Tasdiqlangan, hali hech qanday vaqt jadvali kiritilmagan va eslatma
    yuborilmagan stadionlar ro'yxati."""
    cur = _conn.cursor()
    cur.execute(
        """
        SELECT s.* FROM stadiums s
        WHERE s.status='approved' AND s.reminder_sent=0
        AND NOT EXISTS (SELECT 1 FROM stadium_times t WHERE t.stadium_id = s.id)
        """
    )
    return cur.fetchall()


def mark_reminder_sent(stadium_id: int):
    _conn.execute("UPDATE stadiums SET reminder_sent=1 WHERE id=?", (stadium_id,))
    _conn.commit()


# ---------------- SEVIMLI STADIONLAR ----------------

def toggle_favorite(telegram_id: int, stadium_id: int) -> bool:
    """Qo'shadi yoki olib tashlaydi. Natija: True = endi sevimlida, False = olib tashlandi."""
    cur = _conn.cursor()
    cur.execute(
        "SELECT 1 FROM favorites WHERE telegram_id=? AND stadium_id=?", (telegram_id, stadium_id)
    )
    if cur.fetchone():
        _conn.execute(
            "DELETE FROM favorites WHERE telegram_id=? AND stadium_id=?",
            (telegram_id, stadium_id),
        )
        _conn.commit()
        return False
    _conn.execute(
        "INSERT INTO favorites (telegram_id, stadium_id, created_at) VALUES (?,?,?)",
        (telegram_id, stadium_id, datetime.now().isoformat()),
    )
    _conn.commit()
    return True


def is_favorite(telegram_id: int, stadium_id: int) -> bool:
    cur = _conn.cursor()
    cur.execute(
        "SELECT 1 FROM favorites WHERE telegram_id=? AND stadium_id=?", (telegram_id, stadium_id)
    )
    return cur.fetchone() is not None


def get_user_favorite_stadiums(telegram_id: int):
    cur = _conn.cursor()
    cur.execute(
        """
        SELECT s.* FROM stadiums s
        JOIN favorites f ON f.stadium_id = s.id
        WHERE f.telegram_id=? AND s.status='approved'
        ORDER BY f.created_at DESC
        """,
        (telegram_id,),
    )
    return cur.fetchall()


# ---------------- SOZLAMALAR (backup vaqti va h.k.) ----------------

def get_setting(key: str):
    cur = _conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    return row["value"] if row else None


def set_setting(key: str, value: str):
    _conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    _conn.commit()


# ---------------- STADIUM TIMES ----------------

def get_times_for_date(stadium_id: int, date: str):
    cur = _conn.cursor()
    cur.execute(
        "SELECT * FROM stadium_times WHERE stadium_id=? AND date=? ORDER BY time",
        (stadium_id, date),
    )
    return cur.fetchall()


def ensure_time_slot(stadium_id: int, date: str, time: str):
    _conn.execute(
        "INSERT OR IGNORE INTO stadium_times (stadium_id, date, time, is_busy) VALUES (?,?,?,0)",
        (stadium_id, date, time),
    )
    _conn.commit()


def toggle_time_slot(stadium_id: int, date: str, time: str):
    ensure_time_slot(stadium_id, date, time)
    cur = _conn.cursor()
    cur.execute(
        "SELECT is_busy FROM stadium_times WHERE stadium_id=? AND date=? AND time=?",
        (stadium_id, date, time),
    )
    row = cur.fetchone()
    new_val = 0 if row["is_busy"] else 1
    _conn.execute(
        "UPDATE stadium_times SET is_busy=? WHERE stadium_id=? AND date=? AND time=?",
        (new_val, stadium_id, date, time),
    )
    _conn.commit()
    return new_val


def get_free_times(stadium_id: int, date: str = None):
    cur = _conn.cursor()
    if date:
        cur.execute(
            "SELECT * FROM stadium_times WHERE stadium_id=? AND date=? AND is_busy=0 ORDER BY time",
            (stadium_id, date),
        )
    else:
        cur.execute(
            "SELECT * FROM stadium_times WHERE stadium_id=? AND is_busy=0 ORDER BY date, time",
            (stadium_id,),
        )
    return cur.fetchall()
