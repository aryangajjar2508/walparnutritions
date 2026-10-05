import os
import sqlite3
import hashlib
import hmac
import json
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).parent / "data" / "walpar_users.db"
SECRET_KEY = os.environ.get("WALPAR_SECRET_KEY", "walpar-super-secret-key-2026-secure-session")
MASTER_BMR_PASSWORD = "Walpar@123"

def get_current_ist_str() -> str:
    """Returns formatted current Indian Standard Time (IST)"""
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d/%m/%Y, %I:%M:%S %p IST")

def hash_password(password: str) -> str:
    """Hashes a password with salt using SHA-256 PBKDF2"""
    salt = secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{h.hex()}"

def verify_password(stored_hash: str, password: str) -> bool:
    """Verifies a password against the stored salt:hash or fallback plain master pass"""
    if not stored_hash:
        return False
    # Backward compatibility with seed passwords
    if stored_hash == password:
        return True
    try:
        if ":" in stored_hash:
            salt, h_hex = stored_hash.split(":", 1)
            h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return h.hex() == h_hex
    except Exception:
        pass
    return False

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    """Initializes tables and seeds default admin account"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at_ist TEXT
            )
        """)

        # 2. Login Tracking Table (Time in IST)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                login_time_ist TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'SUCCESS'
            )
        """)

        # 3. Formula Upload Tracking Table (Who uploaded what photo & which rates given)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upload_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                upload_time_ist TEXT NOT NULL,
                image_url TEXT NOT NULL,
                original_filename TEXT,
                engine_used TEXT,
                ingredients_count INTEGER,
                detected_ingredients_json TEXT,
                software_rates_json TEXT,
                ocr_summary TEXT
            )
        """)

        # 4. Batch Card Generation & Download Tracking (with commercial rates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_download_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                timestamp_ist TEXT NOT NULL,
                product_type TEXT,
                batch_qty INTEGER,
                total_batch_kg REAL,
                status TEXT,
                password_used TEXT,
                pack_type TEXT,
                rate_per_pack REAL,
                rate_per_unit REAL,
                total_batch_val REAL
            )
        """)

        # Migration for existing databases
        for col, col_type in [
            ("pack_type", "TEXT"),
            ("rate_per_pack", "REAL"),
            ("rate_per_unit", "REAL"),
            ("total_batch_val", "REAL"),
            ("missing_items_json", "TEXT DEFAULT '[]'"),
            ("raw_payload_json", "TEXT DEFAULT ''"),
            ("updated_rate_per_pack", "REAL DEFAULT 0.0"),
            ("updated_rate_per_unit", "REAL DEFAULT 0.0"),
            ("updated_total_val", "REAL DEFAULT 0.0"),
            ("rate_status", "TEXT DEFAULT 'NORMAL'"),
            ("admin_notes", "TEXT DEFAULT ''")
        ]:
            try:
                cursor.execute(f"ALTER TABLE batch_download_logs ADD COLUMN {col} {col_type}")
            except Exception:
                pass

        # 5. Missing Ingredient Rate Requests Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missing_rate_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER,
                username TEXT NOT NULL,
                timestamp_ist TEXT NOT NULL,
                product_type TEXT,
                ingredient_name TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                resolved_rate REAL DEFAULT 0.0,
                resolved_at_ist TEXT,
                resolved_by TEXT,
                user_estimated_rate REAL DEFAULT 0.0,
                notes TEXT DEFAULT ''
            )
        """)

        for col, col_type in [
            ("user_estimated_rate", "REAL DEFAULT 0.0"),
            ("notes", "TEXT DEFAULT ''")
        ]:
            try:
                cursor.execute(f"ALTER TABLE missing_rate_requests ADD COLUMN {col} {col_type}")
            except Exception:
                pass

        # 6. Model Training Rules Table (Autonomous Subagent Memory Bank)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_training_rules (
                id TEXT PRIMARY KEY,
                raw_directive TEXT NOT NULL,
                source_term TEXT NOT NULL,
                source_term_clean TEXT NOT NULL,
                target_term TEXT NOT NULL,
                target_rate REAL DEFAULT 0.0,
                rule_type TEXT DEFAULT 'synonym',
                trainer TEXT DEFAULT 'tanmay',
                created_at_ist TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                validation_note TEXT DEFAULT ''
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rule_source ON model_training_rules(source_term_clean)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rule_status ON model_training_rules(status)")

        # Check if default admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            default_admin_pass = hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_at_ist)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("admin", default_admin_pass, "Walpar Chief Administrator", "admin", 1, get_current_ist_str()))
            print("[Auth] Created default administrator: admin / admin123")

        # Check if dedicated model training specialist tanmay exists
        cursor.execute("SELECT id FROM users WHERE username = 'tanmay'")
        tanmay_row = cursor.fetchone()
        tanmay_pass = hash_password("Tanmay@123")
        if not tanmay_row:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_at_ist)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("tanmay", tanmay_pass, "Tanmay (AI Model Trainer)", "model_trainer", 1, get_current_ist_str()))
            print("[Auth] Created dedicated model trainer: tanmay / Tanmay@123")
        else:
            cursor.execute("UPDATE users SET password_hash = ?, is_active = 1 WHERE username = 'tanmay'", (tanmay_pass,))

        conn.commit()

# Run initialization
init_auth_db()

# ── Session Token Helpers ──
def create_session_token(username: str, role: str) -> str:
    """Creates HMAC-signed cookie value"""
    exp = (datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(days=14)).isoformat()
    payload = f"{username}|{role}|{exp}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}|{signature}"

def verify_session_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validates session token and returns user payload"""
    if not token or "|" not in token:
        return None
    try:
        parts = token.split("|")
        if len(parts) != 4:
            return None
        username, role, exp_str, signature = parts
        payload = f"{username}|{role}|{exp_str}"
        expected_sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        exp = datetime.fromisoformat(exp_str)
        if datetime.now(ZoneInfo("Asia/Kolkata")) > exp:
            return None
        
        # Verify user still exists and is active
        with get_db() as conn:
            row = conn.cursor().execute("SELECT is_active, full_name FROM users WHERE username = ?", (username,)).fetchone()
            if not row or row["is_active"] != 1:
                return None
            full_name = row["full_name"]

        return {"username": username, "role": role, "full_name": full_name}
    except Exception:
        return None

# ── User Operations ──
def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verifies credentials; returns user dict if valid and active"""
    username = username.strip().lower()
    with get_db() as conn:
        row = conn.cursor().execute("SELECT * FROM users WHERE LOWER(username) = ?", (username,)).fetchone()
        if not row:
            return None
        # Allow either hashed password, or Walpar@123 for admin, or password 'admin' if unhashed
        if not verify_password(row["password_hash"], password):
            if row["username"] == "admin" and password in ("Walpar@123", "admin"):
                pass
            else:
                return None
        if row["is_active"] != 1:
            return None
        return dict(row)

def create_user(username: str, password: str, full_name: str, role: str = "user") -> Dict[str, Any]:
    """Admin creates a new user"""
    username = username.strip().lower()
    if not username or not password:
        return {"success": False, "error": "Username and password are required"}
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,))
            if cursor.fetchone():
                return {"success": False, "error": f"Username '{username}' already exists"}
            
            p_hash = hash_password(password)
            ist_now = get_current_ist_str()
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_at_ist)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, p_hash, full_name or username.title(), role, 1, ist_now))
            conn.commit()
            return {"success": True, "username": username}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_user_password(username: str, new_password: str) -> Dict[str, Any]:
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            p_hash = hash_password(new_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (p_hash, username))
            conn.commit()
            return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def toggle_user_active(username: str) -> Dict[str, Any]:
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE username = ?", (username,))
            conn.commit()
            return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_user(username: str) -> Dict[str, Any]:
    if username.lower() == "admin":
        return {"success": False, "error": "Cannot delete primary admin account"}
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_all_users() -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT id, username, full_name, role, is_active, created_at_ist FROM users ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]

# ── Activity & Audit Logging (IST) ──
def log_login_event(username: str, ip_address: str, user_agent: str, status: str = "SUCCESS"):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO login_logs (username, login_time_ist, ip_address, user_agent, status)
                VALUES (?, ?, ?, ?, ?)
            """, (username, get_current_ist_str(), ip_address, user_agent, status))
            conn.commit()
    except Exception as e:
        print(f"[Auth] Log login error: {e}")

def log_upload_event(
    username: str,
    image_url: str,
    original_filename: str,
    engine_used: str,
    ingredients: List[Dict[str, Any]],
    software_rates: List[Dict[str, Any]]
):
    """
    Logs every uploaded formulation photo, along with what OCR detected and
    what rate the software matched/evaluated for audit review by admin.
    """
    try:
        summary_items = [f"{i.get('name')} ({i.get('dosage')} {i.get('unit')})" for i in ingredients[:5]]
        ocr_summary = ", ".join(summary_items)
        if len(ingredients) > 5:
            ocr_summary += f" +{len(ingredients) - 5} more"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO upload_logs (
                    username, upload_time_ist, image_url, original_filename,
                    engine_used, ingredients_count, detected_ingredients_json,
                    software_rates_json, ocr_summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                get_current_ist_str(),
                image_url,
                original_filename,
                engine_used,
                len(ingredients),
                json.dumps(ingredients),
                json.dumps(software_rates),
                ocr_summary
            ))
            conn.commit()
    except Exception as e:
        print(f"[Auth] Log upload error: {e}")

def log_batch_download_event(
    username: str,
    product_type: str,
    batch_qty: int,
    total_batch_kg: float,
    status: str,
    password_used: str = "",
    pack_type: str = "STRIP",
    rate_per_pack: float = 0.0,
    rate_per_unit: float = 0.0,
    total_batch_val: float = 0.0
):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO batch_download_logs (
                    username, timestamp_ist, product_type, batch_qty,
                    total_batch_kg, status, password_used,
                    pack_type, rate_per_pack, rate_per_unit, total_batch_val
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                get_current_ist_str(),
                product_type,
                batch_qty,
                total_batch_kg,
                status,
                password_used,
                pack_type,
                rate_per_pack,
                rate_per_unit,
                total_batch_val
            ))
            conn.commit()
    except Exception as e:
        print(f"[Auth] Log batch error: {e}")

def get_upload_logs(limit: int = 200, user_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if user_filter:
            rows = cursor.execute("""
                SELECT * FROM upload_logs WHERE username = ? ORDER BY id DESC LIMIT ?
            """, (user_filter, limit)).fetchall()
        else:
            rows = cursor.execute("""
                SELECT * FROM upload_logs ORDER BY id DESC LIMIT ?
            """, (limit,)).fetchall()
        
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["detected_ingredients"] = json.loads(d.get("detected_ingredients_json") or "[]")
            except Exception:
                d["detected_ingredients"] = []
            try:
                d["software_rates"] = json.loads(d.get("software_rates_json") or "[]")
            except Exception:
                d["software_rates"] = []
            result.append(d)
        return result

def get_login_logs(limit: int = 200, user_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if user_filter:
            rows = cursor.execute("SELECT * FROM login_logs WHERE username = ? ORDER BY id DESC LIMIT ?", (user_filter, limit)).fetchall()
        else:
            rows = cursor.execute("SELECT * FROM login_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_batch_logs(limit: int = 200, user_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if user_filter:
            rows = cursor.execute("SELECT * FROM batch_download_logs WHERE username = ? ORDER BY id DESC LIMIT ?", (user_filter, limit)).fetchall()
        else:
            rows = cursor.execute("SELECT * FROM batch_download_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["missing_items"] = json.loads(d.get("missing_items_json") or "[]")
            except Exception:
                d["missing_items"] = []
            result.append(d)
        return result

def log_quotation_event(
    username: str,
    product_type: str,
    batch_qty: int,
    total_batch_kg: float,
    status: str,
    pack_type: str = "STRIP",
    rate_per_pack: float = 0.0,
    rate_per_unit: float = 0.0,
    total_batch_val: float = 0.0,
    missing_items: Optional[List[str]] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
    user_estimated_rates: Optional[Dict[str, float]] = None
) -> int:
    """
    Log quotation with full payload & track missing / user-estimated ingredient rate requests
    """
    try:
        missing_items = missing_items or []
        user_estimated_rates = user_estimated_rates or {}
        rate_status = "PENDING_ADMIN_RATE" if missing_items else "NORMAL"
        if user_estimated_rates and not missing_items:
            rate_status = "USER_ESTIMATED"
        if missing_items and status == "QUOTATION_CALCULATED":
            status = "PENDING_ADMIN_RATE"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO batch_download_logs (
                    username, timestamp_ist, product_type, batch_qty,
                    total_batch_kg, status, password_used,
                    pack_type, rate_per_pack, rate_per_unit, total_batch_val,
                    missing_items_json, raw_payload_json, rate_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                get_current_ist_str(),
                product_type,
                batch_qty,
                total_batch_kg,
                status,
                "",
                pack_type,
                rate_per_pack,
                rate_per_unit,
                total_batch_val,
                json.dumps(missing_items),
                json.dumps(raw_payload) if raw_payload else "",
                rate_status
            ))
            quote_id = cursor.lastrowid

            # Insert rate tracking records
            now_ist = get_current_ist_str()
            for ing in missing_items:
                clean_ing = str(ing).strip()
                if not clean_ing:
                    continue
                est_rate = float(user_estimated_rates.get(clean_ing, 0.0))
                req_status = "USER_ESTIMATED" if est_rate > 0 else "PENDING"
                cursor.execute("""
                    INSERT INTO missing_rate_requests (
                        quotation_id, username, timestamp_ist, product_type, ingredient_name, status, user_estimated_rate
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (quote_id, username, now_ist, product_type, clean_ing, req_status, est_rate))

            # Also log any user-estimated rates that were provided even if not in missing_items
            for ing_name, est_rate in user_estimated_rates.items():
                if ing_name not in missing_items and float(est_rate) > 0:
                    cursor.execute("""
                        INSERT INTO missing_rate_requests (
                            quotation_id, username, timestamp_ist, product_type, ingredient_name, status, user_estimated_rate
                        )
                        VALUES (?, ?, ?, ?, ?, 'USER_ESTIMATED', ?)
                    """, (quote_id, username, now_ist, product_type, str(ing_name).strip(), float(est_rate)))

            conn.commit()
            return quote_id
    except Exception as e:
        print(f"[Auth] Log quotation error: {e}")
        return 0

def log_user_estimated_rate(
    username: str,
    ingredient_name: str,
    estimated_rate: float,
    product_type: str = "Tablet",
    quotation_id: Optional[int] = None,
    notes: str = ""
) -> int:
    """Records an estimated rate filled by a user for Admin auditing without touching rate avg.xlsx"""
    clean_ing = str(ingredient_name).strip()
    if not clean_ing or float(estimated_rate) <= 0:
        return 0
    now_ist = get_current_ist_str()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO missing_rate_requests (
                quotation_id, username, timestamp_ist, product_type, ingredient_name, status, user_estimated_rate, notes
            )
            VALUES (?, ?, ?, ?, ?, 'USER_ESTIMATED', ?, ?)
        """, (quotation_id, username, now_ist, product_type, clean_ing, float(estimated_rate), notes))
        conn.commit()
        return cursor.lastrowid

def get_user_estimated_rates(limit: int = 200) -> List[Dict[str, Any]]:
    """Returns list of rates estimated and filled by users for admin audit"""
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT m.*, b.batch_qty, b.pack_type, b.rate_per_pack, b.total_batch_val
            FROM missing_rate_requests m
            LEFT JOIN batch_download_logs b ON m.quotation_id = b.id
            WHERE m.status = 'USER_ESTIMATED' OR m.user_estimated_rate > 0
            ORDER BY m.id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_pending_missing_rates() -> List[Dict[str, Any]]:
    """Returns all unresolved ingredient rate requests across users"""
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT m.*, b.batch_qty, b.pack_type, b.rate_per_pack, b.total_batch_val
            FROM missing_rate_requests m
            LEFT JOIN batch_download_logs b ON m.quotation_id = b.id
            WHERE m.status = 'PENDING'
            ORDER BY m.id DESC
        """).fetchall()
        return [dict(r) for r in rows]

def get_all_missing_rate_requests(limit: int = 200) -> List[Dict[str, Any]]:
    """Returns history of all missing rate requests (pending and resolved)"""
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT m.*, b.batch_qty, b.pack_type, b.rate_per_pack, b.total_batch_val
            FROM missing_rate_requests m
            LEFT JOIN batch_download_logs b ON m.quotation_id = b.id
            ORDER BY m.id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

def resolve_missing_rate_requests(ingredient_name: str, resolved_rate: float, resolved_by: str) -> List[int]:
    """
    Marks all pending requests for this ingredient as RESOLVED.
    Returns list of distinct quotation IDs that were affected.
    """
    now_ist = get_current_ist_str()
    clean_target = str(ingredient_name).strip().lower()
    affected_quote_ids = []

    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, quotation_id, ingredient_name FROM missing_rate_requests WHERE status = 'PENDING'").fetchall()
        matching_req_ids = []
        for r in rows:
            r_name = r["ingredient_name"].lower().strip()
            if clean_target == r_name or clean_target in r_name or r_name in clean_target:
                matching_req_ids.append(r["id"])
                if r["quotation_id"]:
                    affected_quote_ids.append(r["quotation_id"])

        if matching_req_ids:
            placeholders = ",".join("?" for _ in matching_req_ids)
            cursor.execute(f"""
                UPDATE missing_rate_requests
                SET status = 'RESOLVED', resolved_rate = ?, resolved_at_ist = ?, resolved_by = ?
                WHERE id IN ({placeholders})
            """, [resolved_rate, now_ist, resolved_by] + matching_req_ids)
            conn.commit()

    return list(set(affected_quote_ids))

def get_quotation_by_id(quote_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM batch_download_logs WHERE id = ?", (quote_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["missing_items"] = json.loads(d.get("missing_items_json") or "[]")
        except Exception:
            d["missing_items"] = []
        try:
            d["raw_payload"] = json.loads(d.get("raw_payload_json") or "{}")
        except Exception:
            d["raw_payload"] = {}
        return d

def update_quotation_revised_rates(
    quotation_id: int,
    new_rate_pack: float,
    new_rate_unit: float,
    new_total_val: float,
    remaining_missing: List[str],
    note: str = ""
):
    with get_db() as conn:
        cursor = conn.cursor()
        new_status = "PENDING_ADMIN_RATE" if remaining_missing else "RATE_UPDATED_BY_ADMIN"
        new_rate_status = "PENDING_ADMIN_RATE" if remaining_missing else "RESOLVED_BY_ADMIN"
        cursor.execute("""
            UPDATE batch_download_logs
            SET updated_rate_per_pack = ?,
                updated_rate_per_unit = ?,
                updated_total_val = ?,
                status = ?,
                rate_status = ?,
                missing_items_json = ?,
                admin_notes = ?
            WHERE id = ?
        """, (
            new_rate_pack,
            new_rate_unit,
            new_total_val,
            new_status,
            new_rate_status,
            json.dumps(remaining_missing),
            note,
            quotation_id
        ))
        conn.commit()

def get_per_user_quotation_stats() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT 
                u.username,
                u.full_name,
                u.role,
                u.is_active,
                COUNT(b.id) as total_quotes,
                COALESCE(SUM(CASE WHEN b.updated_total_val > 0 THEN b.updated_total_val ELSE b.total_batch_val END), 0.0) as total_portfolio_val,
                MAX(b.timestamp_ist) as last_quote_time,
                COUNT(CASE WHEN b.status = 'PENDING_ADMIN_RATE' OR b.rate_status = 'PENDING_ADMIN_RATE' THEN 1 END) as pending_quotes,
                COUNT(CASE WHEN b.status = 'RATE_UPDATED_BY_ADMIN' OR b.rate_status = 'RESOLVED_BY_ADMIN' THEN 1 END) as resolved_quotes
            FROM users u
            LEFT JOIN batch_download_logs b ON u.username = b.username
            GROUP BY u.username
            ORDER BY total_quotes DESC, u.username ASC
        """).fetchall()
        return [dict(r) for r in rows]

# ══════════════════════════════════════════════════════════════════
# MODEL TRAINING RULES PERSISTENCE (SQLITE DATABASE)
# ══════════════════════════════════════════════════════════════════

def db_get_all_training_rules() -> List[Dict[str, Any]]:
    """Returns all active model training rules from SQLite database"""
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT id, raw_directive, source_term, source_term_clean, target_term,
                   target_rate, rule_type, trainer, created_at_ist, status, validation_note
            FROM model_training_rules
            WHERE status = 'active'
            ORDER BY rowid ASC
        """).fetchall()
        return [dict(r) for r in rows]

def db_insert_training_rule(rule: Dict[str, Any]) -> bool:
    """Inserts or updates a model training rule in SQLite database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO model_training_rules (
                id, raw_directive, source_term, source_term_clean, target_term,
                target_rate, rule_type, trainer, created_at_ist, status, validation_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule.get("id"),
            rule.get("raw_directive", ""),
            rule.get("source_term", ""),
            rule.get("source_term_clean", ""),
            rule.get("target_term", ""),
            float(rule.get("target_rate") or 0.0),
            rule.get("rule_type", "synonym"),
            rule.get("trainer", "tanmay"),
            rule.get("created_at_ist", get_current_ist_str()),
            rule.get("status", "active"),
            rule.get("validation_note", "")
        ))
        conn.commit()
        return True

def db_delete_training_rule(rule_id: str) -> bool:
    """Deletes/revokes a model training rule from SQLite database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM model_training_rules WHERE id = ?", (rule_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted


