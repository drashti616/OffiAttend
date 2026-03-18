"""
Flask API Server — AI Enabled Face Recognition Attendance Management System
• Images stored on disk, only paths in DB (no blobs)
• InsightFace for face recognition (no OpenCV)
• Hybrid Attendance: Multiple logs per day, one final status
• Attendance rules:
    10:00–11:00 → Present (is_late = false)
    After 11:00 → Present (is_late = true)
    Leave day + scan-in → overwrite to Present/Late
    No exit by 19:00 → auto_exit_scheduler sets 19:00
    7:00 PM → attendance finalizer sets final status
• Auto Slot Generation:
    09:45 AM → Create pending slots for all active employees
    07:05 PM → Auto lock pending → absent
"""

import os
import re
import random
import string
import base64
import threading
import time
from datetime import datetime, time as dt_time, date as dt_date
from apscheduler.schedulers.background import BackgroundScheduler

import bcrypt
import mysql.connector
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# Import hybrid attendance system
from attendance_config import DB_CFG, STATUS_PENDING, STATUS_PRESENT, STATUS_LATE, STATUS_LEAVE, STATUS_ABSENT, LATE_TIME, OFFICE_START, FINALIZE_TIME
print(f"[DEBUG] DB_CFG imported: {DB_CFG}")
# from attendance_api import AttendanceAPI
# from attendance_scheduler import start_attendance_scheduler
from attendance_migration import create_attendance_tables
# from attendance_finalizer import start_attendance_finalizer

# Import enhanced attendance system
from attendance_engine_enhanced_fixed import EnhancedAttendanceEngine
from attendance_scheduler_enhanced import start_enhanced_attendance_scheduler

# ── Directory layout ──────────────────────────────────────────────────────────
PROJECT_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FACES_DIR     = os.path.join(PROJECT_ROOT, "faces")          # faces/
IMAGES_DIR    = os.path.join(FACES_DIR, "images")            # faces/images/  — recognition
UPLOADS_DIR   = os.path.join(FACES_DIR, "uploads")           # faces/uploads/ — profiles

for d in [FACES_DIR, IMAGES_DIR, UPLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=PROJECT_ROOT, static_url_path="")
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024    # 50 MB

@app.route("/")
def index():
    return send_file(os.path.join(PROJECT_ROOT, "index.html"))

@app.route("/favicon.ico")
def favicon():
    return "", 204  # No content - avoids 404 in console

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(PROJECT_ROOT, path)

# ── MySQL ─────────────────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(**DB_CFG)

# ── Auto Slot Generation Functions ───────────────────────────────────────
# ── Auto Slot Generation Functions (Fixed to match 7.15 PM Rule Prompt) ──
def generate_daily_slots():
    """
    IMPROVED DAILY SLOT GENERATION
    - Only generates slots for employees without existing records
    - Respects current time and business logic
    - Prevents duplicate records
    - Sets leave_status based on leave_applications
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        today = datetime.now().date()
        now = datetime.now()
        current_time = now.time()
        
        print(f"[SLOTS] Generating attendance slots for {today} at {current_time}")
        
        # Only generate slots for employees who don't have records
        cursor.execute("""
            SELECT e.emp_id, e.full_name, e.joining_date
            FROM employees e
            WHERE e.status = 'Active'
            AND (e.joining_date IS NULL OR e.joining_date <= %s)
            AND e.emp_id NOT IN (
                SELECT emp_id FROM attendance WHERE att_date = %s
            )
        """, (today, today))
        
        employees = cursor.fetchall()
        print(f"[SLOTS] Found {len(employees)} employees without attendance records")
        
        slots_created = 0
        
        # Only create pending slots if it's AT or AFTER 9:45 AM (office start time)
        if current_time >= OFFICE_START:
            for emp in employees:
                # Fetch leave_status for this employee and date
                cursor.execute("""
                    SELECT status FROM leave_applications
                    WHERE emp_id=%s AND %s BETWEEN from_date AND to_date
                    ORDER BY created_at DESC LIMIT 1
                """, (emp['emp_id'], today))
                
                leave_app = cursor.fetchone()
                leave_status = leave_app['status'] if leave_app else 'Not Applied'
                
                cursor.execute("""
                    INSERT INTO attendance (emp_id, att_date, status, leave_status, attendance_locked, source, created_at)
                    VALUES (%s, %s, %s, %s, 0, 'System_Morning', NOW())
                """, (emp['emp_id'], today, STATUS_PENDING, leave_status))
                slots_created += 1
                print(f"[SLOTS] Created pending slot for {emp['emp_id']} with leave_status={leave_status}")
        else:
            print(f"[SLOTS] Before {OFFICE_START}, not creating pending slots yet")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "date": today.strftime('%Y-%m-%d'),
            "slots_created": slots_created,
            "total_employees": len(employees),
            "current_time": current_time.strftime('%H:%M:%S')
        }
        
    except Exception as e:
        print(f"[SLOTS] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "slots_created": 0
        }
        return {"success": False, "error": str(e)}

def update_attendance_status():
    """
    Update attendance status based on scan times
    - Present: scanned before 11:00 AM
    - Late: scanned after 11:00 AM
    - Pending: no scan yet
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        today = datetime.now().date()
        
        # Update status for all scanned employees based on their in_time
        cursor.execute("""
            UPDATE attendance 
            SET status = CASE 
                WHEN in_time IS NULL THEN %s
                WHEN TIME(in_time) <= %s THEN %s
                WHEN TIME(in_time) > %s THEN %s
                ELSE status
            END
            WHERE att_date = %s AND attendance_locked = 0
        """, (STATUS_PENDING, LATE_TIME, STATUS_PRESENT, LATE_TIME, STATUS_LATE, today))
        
        updated = cursor.rowcount
        print(f"[STATUS] Updated status for {updated} attendance records")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"success": True, "updated": updated}
        
    except Exception as e:
        print(f"[STATUS] Error: {e}")
        return {"success": False, "error": str(e)}

def cleanup_duplicate_attendance():
    """
    Clean up duplicate attendance records on startup
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        today = datetime.now().date()
        
        # Find and remove duplicate records (keep the latest one)
        cursor.execute("""
            SELECT emp_id, COUNT(*) as count
            FROM attendance 
            WHERE att_date = %s
            GROUP BY emp_id 
            HAVING count > 1
        """, (today,))
        
        duplicates = cursor.fetchall()
        cleaned = 0
        
        for dup in duplicates:
            emp_id = dup['emp_id']
            
            # Get all records for this employee, ordered by creation time
            cursor.execute("""
                SELECT id, created_at 
                FROM attendance 
                WHERE emp_id = %s AND att_date = %s
                ORDER BY created_at DESC
            """, (emp_id, today))
            
            records = cursor.fetchall()
            
            # Keep the first (latest) record, delete the rest
            for record in records[1:]:
                cursor.execute("DELETE FROM attendance WHERE id = %s", (record['id'],))
                cleaned += 1
                print(f"[CLEANUP] Removed duplicate record for {emp_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if cleaned > 0:
            print(f"[CLEANUP] Removed {cleaned} duplicate attendance records")
        else:
            print("[CLEANUP] No duplicate records found")
        
        return {"success": True, "cleaned": cleaned}
        
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")
        return {"success": False, "error": str(e)}

def auto_lock_pending():
    """
    AUTO LOCK PROCESS exactly at 07:15 PM
    Step 1: Select Employees Where scan_flag = FALSE (in_time IS NULL) and attendance_locked = FALSE
    Step 2: Apply Final Rules
    Step 3: Lock Attendance (attendance_locked = 1)
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        today = datetime.now().date()
        
        print(f"[AUTO_LOCK] Finalizing attendance for {today} (7:15 PM)")
        
        # Step 1: Get all Unlocked records without scans
        cursor.execute("""
            SELECT a.emp_id FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.att_date = %s 
            AND a.attendance_locked = 0
            AND a.in_time IS NULL
        """, (today,))
        
        records = cursor.fetchall()
        
        locked_absent = 0
        locked_present = 0
        
        for rec in records:
            emp_id = rec['emp_id']
            
            # Fetch Leave Status for Step 2
            cursor.execute("""
                SELECT status FROM leave_applications 
                WHERE emp_id = %s AND %s BETWEEN from_date AND to_date 
                ORDER BY created_at DESC LIMIT 1
            """, (emp_id, today))
            leave_row = cursor.fetchone()
            leave_status_text = leave_row['status'] if leave_row else 'Not Applied'
            
            # Step 2: Apply Final Rules Decision Matrix
            # Approved Leave + No Scan -> Leave (not Present)
            # Rejected / Not Applied + No Scan -> Absent
            final_status = STATUS_ABSENT
            leave_status_field = 'Not Applied'
            
            if leave_status_text == 'Approved':
                final_status = STATUS_LEAVE
                leave_status_field = 'Approved'
                locked_present += 1
            else:
                final_status = STATUS_ABSENT
                leave_status_field = leave_status_text
                locked_absent += 1
                
            # Step 3: Lock Attendance
            cursor.execute("""
                UPDATE attendance 
                SET status = %s, leave_status = %s, attendance_locked = 1, updated_at = NOW()
                WHERE emp_id = %s AND att_date = %s
            """, (final_status, leave_status_field, emp_id, today))

        # Also Lock records THAT HAVE SCANS (They are already Present/Late)
        cursor.execute("""
            UPDATE attendance 
            SET attendance_locked = 1, updated_at = NOW()
            WHERE att_date = %s AND attendance_locked = 0 AND in_time IS NOT NULL
        """, (today,))
        locked_scanned = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[AUTO_LOCK] Done. Locked {locked_absent} Absent, {locked_present} Present (Leave), {locked_scanned} Present (Scan)")
        return {
            "success": True,
            "locked_absent": locked_absent,
            "locked_present_leave": locked_present,
            "locked_scanned": locked_scanned,
            "total_processed": locked_absent + locked_present + locked_scanned
        }
    except Exception as e:
        print(f"[AUTO_LOCK] Error: {e}")
        return {"success": False, "error": str(e)}
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[AUTO_LOCK] Completed: {locked_count} Absent, {leave_count} Leave, {future_employees} future")
        return {
            "success": True,
            "date": today.strftime('%Y-%m-%d'),
            "absent_count": int(locked_count),
            "leave_count": int(leave_count),
            "future_employees": int(future_employees),
            "total_processed": int(locked_count + leave_count)
        }
        
    except Exception as e:
        print(f"[AUTO_LOCK] Error: {e}")
        return {"success": False, "error": str(e)}

# ── Initialize Enhanced Attendance System ───────────────────────────────────────
def initialize_enhanced_attendance(app):
    """Initialize enhanced attendance tables and API with status automation"""
    try:
        # Create attendance tables
        create_attendance_tables()
        print("[ENHANCED] Attendance tables created/verified")
        
        # Initialize enhanced attendance API
        db_connection = mysql.connector.connect(**DB_CFG)
        attendance_api = EnhancedAttendanceEngine(db_connection)
        print("[ENHANCED] Enhanced attendance API initialized")
        
        # PRE-LOAD FACE RECOGNITION MODEL AT STARTUP
        print("[FACE_MODEL] Pre-loading InsightFace model at startup...")
        try:
            from face_recognizer_insightface import _init_insightface, _load_known_faces
            _init_insightface()
            _load_known_faces(force=True)
            print("[FACE_MODEL] ✅ Face recognition model pre-loaded successfully")
        except Exception as model_error:
            print(f"[FACE_MODEL] ⚠️ Warning: Could not pre-load face model: {model_error}")
            print("[FACE_MODEL] Model will load on first request (slower)")
        
        # NOTE: Do NOT generate slots at startup
        # Slots are generated ONLY by scheduler at 9:45 AM
        print("[ENHANCED] Slots will be generated at 09:45 AM daily (not at startup)")
        
        db_connection.close()
        
        # Start enhanced attendance scheduler
        start_enhanced_attendance_scheduler()
        print("[ENHANCED] Enhanced attendance scheduler started")
        
    except Exception as e:
        print(f"[ENHANCED] Initialization error: {e}")
        raise Exception("[HYBRID] Continuing without hybrid system...")
        return None

# ── bcrypt helpers ────────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False

# ── password generator / validator ───────────────────────────────────────────
def generate_password() -> str:
    chars = string.ascii_letters + string.digits + "@$#."
    pwd = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("@$#."),
        *[random.choice(chars) for _ in range(4)],
    ]
    random.shuffle(pwd)
    return "".join(pwd)

def validate_password(pw: str) -> tuple[bool, str]:
    if len(pw) < 8:
        return False, "Password must be at least 8 characters"
    if len(pw) > 20:
        return False, "Password must be max 20 characters"
    if not any(c.isupper() for c in pw):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in pw):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in pw):
        return False, "Password must contain at least one digit"
    if not any(c in "@$#." for c in pw):
        return False, "Password must contain at least one special character"
    return True, ""

# ── image save helper ─────────────────────────────────────────────────────────
def save_b64_image(b64_str: str, dest_path: str) -> bool:
    """Decode a base64 image string and save to dest_path. Returns True on success."""
    try:
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(b64_str)
        with open(dest_path, "wb") as f:
            f.write(img_bytes)
        return True
    except Exception as e:
        print(f"[IMG] Error saving {dest_path}: {e}")
        return False

# ── startup migrations (safe — won't crash if column exists) ──────────────────
def _safe_alter(cursor, sql):
    try:
        cursor.execute(sql)
    except mysql.connector.Error as e:
        if e.errno != 1060:  # 1060 = duplicate column
            print(f"[MIGRATE] {e}")

def run_migrations():
    try:
        conn = get_db(); cursor = conn.cursor()
        _safe_alter(cursor, "ALTER TABLE employee_credentials ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 1")
        _safe_alter(cursor, "ALTER TABLE admins ADD COLUMN email VARCHAR(120) NULL")
        _safe_alter(cursor, "ALTER TABLE face_profiles ADD COLUMN face_image_path VARCHAR(500) NULL")
        _safe_alter(cursor, "ALTER TABLE face_profiles ADD COLUMN profile_pic_path VARCHAR(500) NULL")
        _safe_alter(cursor, "ALTER TABLE attendance ADD COLUMN is_late TINYINT(1) NOT NULL DEFAULT 0")
        _safe_alter(cursor, "ALTER TABLE attendance ADD COLUMN updated_at DATETIME NULL")
        conn.commit(); cursor.close(); conn.close()
    except Exception as e:
        print(f"[MIGRATE] Skipped (DB may not be ready yet): {e}")

# ── auto-exit scheduler ───────────────────────────────────────────────────────
try:
    from auto_exit_scheduler import start_auto_exit_scheduler
    _auto_exit_available = True
except ImportError:
    _auto_exit_available = False

# ── attendance finalizer scheduler ───────────────────────────────────────────
try:
    from attendance_finalizer import start_attendance_finalizer
    _attendance_finalizer_available = True
except ImportError:
    _attendance_finalizer_available = False

# ── Enhanced Attendance API Routes ───────────────────────────────────────
@app.route("/api/attendance/process-daily", methods=["POST"])
def process_daily_attendance():
    """Process daily attendance status for all employees"""
    try:
        data = request.get_json()
        target_date_str = data.get("date")
        
        if not target_date_str:
            return jsonify({"success": False, "error": "date required (YYYY-MM-DD format)"}), 400
        
        # Parse date
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        conn = get_db()
        engine = EnhancedAttendanceEngine(conn)
        
        # Process daily attendance status
        result = engine.process_daily_attendance_status(target_date)
        
        conn.close()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/finalize-daily", methods=["POST"])
def finalize_daily_attendance():
    """Finalize daily attendance status at 19:00"""
    try:
        data = request.get_json()
        target_date_str = data.get("date")
        
        if not target_date_str:
            return jsonify({"success": False, "error": "date required (YYYY-MM-DD format)"}), 400
        
        # Parse date
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        conn = get_db()
        engine = EnhancedAttendanceEngine(conn)
        
        # Finalize attendance status
        result = engine.finalize_daily_attendance(target_date)
        
        conn.close()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/auto-generate", methods=["POST"])
def auto_generate_missing_records():
    """Auto-generate missing attendance records for today and yesterday"""
    try:
        data = request.get_json()
        include_yesterday = data.get("include_yesterday", True)
        
        if not isinstance(include_yesterday, bool):
            return jsonify({"success": False, "error": "include_yesterday must be boolean"}), 400
        
        conn = get_db()
        engine = EnhancedAttendanceEngine(conn)
        
        # Auto-generate missing records
        result = engine.auto_generate_missing_records(include_yesterday=include_yesterday)
        
        conn.close()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/generate-daily-slots", methods=["POST"])
def api_generate_daily_slots():
    """API endpoint to manually generate pending attendance slots"""
    try:
        # Call the actual slot generation function
        from attendance_engine_enhanced_fixed import EnhancedAttendanceEngine
        conn = get_db()
        engine = EnhancedAttendanceEngine(conn)
        result = engine.auto_generate_missing_records(datetime.now().date(), include_yesterday=False)
        conn.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/auto-lock-pending", methods=["POST"])
def api_auto_lock_pending():
    """API endpoint to manually trigger auto-lock pending attendance"""
    try:
        result = auto_lock_pending()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ═════════════════════════════════════════════════════════════════════════════
# API ROUTES
# ═════════════════════════════════════════════════════════════════════════════

# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    ok = False
    try:
        c = get_db(); c.close(); ok = True
    except Exception as e:
        return jsonify({"status": "ok", "db_ok": False, "db_error": str(e)}), 200
    return jsonify({"status": "ok", "db_ok": ok}), 200

# ── Login ─────────────────────────────────────────────────────────────────────
@app.route("/api/check-password-change", methods=["GET"])
def check_password_change():
    """Check if employee must change password on first login"""
    try:
        emp_id = request.args.get("emp_id")
        
        if not emp_id:
            return jsonify({"success": False, "error": "emp_id required"}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT must_change_password FROM employee_credentials 
            WHERE emp_id = %s
        """, (emp_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        return jsonify({
            "success": True,
            "must_change_password": bool(result['must_change_password']),
            "message": "Password change required" if result['must_change_password'] else "Password change not required"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data     = request.get_json()
        user_id  = (data.get("emp_id") or "").strip()
        password = (data.get("password") or "").strip()
        if not user_id or not password:
            return jsonify({"success": False, "error": "ID and password required"}), 400

        conn   = get_db()
        cursor = conn.cursor(dictionary=True)

        # Try admin first
        cursor.execute("SELECT * FROM admins WHERE username = %s", (user_id,))
        admin = cursor.fetchone()
        if admin and verify_password(password, admin["password_hash"]):
            cursor.execute("UPDATE admins SET last_login_at=%s WHERE id=%s", (datetime.now(), admin["id"]))
            conn.commit(); cursor.close(); conn.close()
            return jsonify({"success": True, "user": {"emp_id": admin["username"], "name": admin["full_name"], "role": "Admin"}}), 200

        # Try employee
        cursor.execute("""
            SELECT ec.*, e.full_name, e.role
            FROM employee_credentials ec
            JOIN employees e ON ec.emp_id = e.emp_id
            WHERE ec.emp_id = %s AND ec.is_active = 1
        """, (user_id,))
        emp = cursor.fetchone()
        if emp and verify_password(password, emp["password_hash"]):
            cursor.execute("UPDATE employee_credentials SET last_login_at=%s WHERE id=%s", (datetime.now(), emp["id"]))
            conn.commit(); cursor.close(); conn.close()
            resp = {"success": True, "user": {"emp_id": emp["emp_id"], "name": emp["full_name"], "role": "Employee"}}
            if emp.get("must_change_password"):
                resp["redirect_to"] = "change_password.html"
            return jsonify(resp), 200

        cursor.close(); conn.close()
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Next employee ID ──────────────────────────────────────────────────────────
@app.route("/api/employees/next-id")
def next_emp_id():
    try:
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("SELECT emp_id FROM employees WHERE emp_id LIKE 'emp%' ORDER BY CAST(SUBSTRING(emp_id,4) AS UNSIGNED) DESC LIMIT 1")
        row = cursor.fetchone()
        cursor.close(); conn.close()
        n = int(row[0][3:]) + 1 if row else 1
        return jsonify({"success": True, "emp_id": f"emp{n:03d}"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Register employee (admin captures face via camera) ────────────────────────
@app.route("/api/employees", methods=["POST"])
def register_employee():
    try:
        data     = request.get_json()
        password = (data.get("password") or "").strip()
        if not password:
            password = generate_password()
        ok, err = validate_password(password)
        if not ok:
            return jsonify({"success": False, "error": err}), 400

        conn   = get_db()
        cursor = conn.cursor()

        # Auto-generate emp_id
        cursor.execute("SELECT emp_id FROM employees WHERE emp_id LIKE 'emp%' ORDER BY CAST(SUBSTRING(emp_id,4) AS UNSIGNED) DESC LIMIT 1")
        row    = cursor.fetchone()
        n      = int(row[0][3:]) + 1 if row else 1
        emp_id = f"emp{n:03d}"

        cursor.execute("""
            INSERT INTO employees (emp_id, full_name, mobile, email, designation, joining_date, address, role, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            emp_id,
            (data.get("full_name") or "").strip(),
            (data.get("mobile") or "").strip(),
            (data.get("email") or "").strip(),
            (data.get("designation") or "").strip(),
            data.get("joining_date") or None,
            (data.get("address") or "").strip(),
            data.get("role", "Employee"),
            data.get("status", "Active"),
        ))

        # ── Save face image from camera capture (base64) ──
        face_b64    = data.get("face_image") or ""
        face_path   = None

        if face_b64:
            filename  = f"{emp_id}.jpg"
            dest_path = os.path.join(IMAGES_DIR, filename)
            if save_b64_image(face_b64, dest_path):
                face_path = f"faces/images/{filename}"   # relative path stored in DB
                print(f"[REGISTER] Face image saved: {dest_path}")

        # Insert face_profiles row (path only)
        cursor.execute("""
            INSERT INTO face_profiles (emp_id, face_image_path, profile_pic_path)
            VALUES (%s, %s, NULL)
        """, (emp_id, face_path))

        # Insert credentials
        cursor.execute("""
            INSERT INTO employee_credentials (emp_id, password_hash, is_active, must_change_password)
            VALUES (%s,%s,1,1)
        """, (emp_id, hash_password(password)))

        conn.commit(); cursor.close(); conn.close()

        # Reload face recognition model
        try:
            from face_recognizer_insightface import reload_faces
            threading.Thread(target=reload_faces, daemon=True).start()
        except Exception as re_err:
            print(f"[REGISTER] reload_faces error: {re_err}")

        return jsonify({
            "success": True,
            "emp_id": emp_id,
            "temp_password": password,
            "message": f"Employee {emp_id} registered. Temp password: {password}",
        }), 200

    except mysql.connector.IntegrityError:
        return jsonify({"success": False, "error": "Employee ID already exists"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Upload profile picture (employee-only action) ─────────────────────────────
@app.route("/api/employees/<emp_id>/upload-profile", methods=["POST"])
def upload_profile(emp_id):
    """Employee uploads their own profile photo → faces/uploads/<emp_id>.jpg"""
    try:
        data   = request.get_json()
        b64    = (data.get("image") or data.get("photo") or "").strip()
        if not b64:
            return jsonify({"success": False, "error": "No image provided"}), 400

        filename  = f"{emp_id}.jpg"
        dest_path = os.path.join(UPLOADS_DIR, filename)
        if not save_b64_image(b64, dest_path):
            return jsonify({"success": False, "error": "Failed to save image"}), 500

        rel_path = f"faces/uploads/{filename}"

        conn = get_db(); cursor = conn.cursor()
        # Upsert face_profiles row
        cursor.execute("SELECT id FROM face_profiles WHERE emp_id=%s", (emp_id,))
        if cursor.fetchone():
            cursor.execute("UPDATE face_profiles SET profile_pic_path=%s, updated_at=%s WHERE emp_id=%s",
                           (rel_path, datetime.now(), emp_id))
        else:
            cursor.execute("INSERT INTO face_profiles (emp_id, face_image_path, profile_pic_path) VALUES (%s,NULL,%s)",
                           (emp_id, rel_path))
        conn.commit(); cursor.close(); conn.close()
        return jsonify({"success": True, "path": rel_path}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Delete profile picture (employee-only action) ─────────────────────────────
@app.route("/api/employees/<emp_id>/delete-profile", methods=["DELETE"])
def delete_profile(emp_id):
    """Employee deletes their own profile photo"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current profile path
        cursor.execute("SELECT profile_pic_path FROM face_profiles WHERE emp_id=%s", (emp_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "No profile photo to delete"}), 404
        
        profile_path = result[0]
        
        # Delete file from disk
        if profile_path:
            abs_path = os.path.join(PROJECT_ROOT, profile_path.replace("/", os.sep))
            if os.path.exists(abs_path):
                os.remove(abs_path)
                print(f"[DELETE] Removed profile photo: {abs_path}")
        
        # Update database to remove profile path
        cursor.execute("UPDATE face_profiles SET profile_pic_path=NULL, updated_at=%s WHERE emp_id=%s",
                     (datetime.now(), emp_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Profile photo deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Get employee list (admin) ─────────────────────────────────────────────────
@app.route("/api/employees", methods=["GET"])
def get_employees():
    try:
        month = (request.args.get("month") or "").strip()
        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, fp.face_image_path, fp.profile_pic_path
            FROM employees e
            LEFT JOIN face_profiles fp ON e.emp_id = fp.emp_id
            ORDER BY e.created_at DESC
        """)
        employees = cursor.fetchall()

        for emp in employees:
            # Remove password hash field if present
            emp.pop("password_hash", None)
            # Standardise path separators
            for key in ("face_image_path", "profile_pic_path"):
                if emp.get(key):
                    emp[key] = emp[key].replace("\\", "/")

            # Monthly stats
            if month:
                # Get joining date to use as start date for counting
                joining_date = emp.get('joining_date')
                
                # Extract year and month from the requested month
                year, month_num = month.split('-')
                
                # Default to full month
                start_date = f"{year}-{month_num}-01"
                end_date = f"{year}-{month_num}-31"
                
                # If joining date exists, adjust start date to be later of joining date or month start
                if joining_date:
                    joining_date_str = joining_date.strftime('%Y-%m-%d') if hasattr(joining_date, 'strftime') else str(joining_date)
                    
                    # If joining date is after the requested month, set all counts to 0
                    if joining_date_str > end_date:
                        emp["total_present"] = 0
                        emp["total_leave"] = 0
                        emp["total_absent"] = 0
                    else:
                        # Adjust start date to be later of joining date or month start
                        if joining_date_str > start_date:
                            start_date = joining_date_str
                        
                        # Count present and late employees (both are considered present)
                        cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status IN ('Present', 'Late')",
                                       (emp["emp_id"], start_date, end_date))
                        emp["total_present"] = cursor.fetchone()["COUNT(*)"]
                        
                        # Count leave entries instead of late entries
                        cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Leave'",
                                       (emp["emp_id"], start_date, end_date))
                        emp["total_leave"] = cursor.fetchone()["COUNT(*)"]
                        
                        cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Absent'",
                                       (emp["emp_id"], start_date, end_date))
                        emp["total_absent"] = cursor.fetchone()["COUNT(*)"]
                else:
                    # No joining date, use full month
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status IN ('Present', 'Late')",
                                   (emp["emp_id"], start_date, end_date))
                    emp["total_present"] = cursor.fetchone()["COUNT(*)"]
                    
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Leave'",
                                   (emp["emp_id"], start_date, end_date))
                    emp["total_leave"] = cursor.fetchone()["COUNT(*)"]
                    
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Absent'",
                                   (emp["emp_id"], start_date, end_date))
                    emp["total_absent"] = cursor.fetchone()["COUNT(*)"]
            else:
                emp["total_present"] = emp["total_leave"] = emp["total_absent"] = 0

        cursor.close(); conn.close()
        return jsonify({"success": True, "employees": employees}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Get single employee profile ───────────────────────────────────────────────
@app.route("/api/profile/<emp_id>")
def get_profile(emp_id):
    try:
        month  = (request.args.get("month") or "").strip()
        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, fp.face_image_path, fp.profile_pic_path
            FROM employees e
            LEFT JOIN face_profiles fp ON e.emp_id = fp.emp_id
            WHERE e.emp_id = %s
        """, (emp_id,))
        emp = cursor.fetchone()
        if not emp:
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "Employee not found"}), 404

        # Monthly stats if requested
        if month:
            # Get joining date to use as start date for counting
            joining_date = emp.get('joining_date')
            
            # Extract year and month from the requested month
            year, month_num = month.split('-')
            
            # Default to full month
            start_date = f"{year}-{month_num}-01"
            end_date = f"{year}-{month_num}-31"
            
            # If joining date exists, adjust start date to be later of joining date or month start
            if joining_date:
                joining_date_str = joining_date.strftime('%Y-%m-%d') if hasattr(joining_date, 'strftime') else str(joining_date)
                
                # If joining date is after the requested month, set all counts to 0
                if joining_date_str > end_date:
                    emp["total_present"] = 0
                    emp["total_leave"] = 0
                    emp["total_absent"] = 0
                    emp["leave_dates"] = []
                else:
                    # Adjust start date to be later of joining date or month start
                    if joining_date_str > start_date:
                        start_date = joining_date_str
                    
                    # Count present and late employees (both are considered present)
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status IN ('Present', 'Late')",
                                   (emp_id, start_date, end_date))
                    result = cursor.fetchone()
                    emp["total_present"] = result["COUNT(*)"] if result else 0
                    
                    # Count leave entries
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Leave'",
                                   (emp_id, start_date, end_date))
                    result = cursor.fetchone()
                    emp["total_leave"] = result["COUNT(*)"] if result else 0
                    
                    # Count absent entries (only after joining date)
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Absent'",
                                   (emp_id, start_date, end_date))
                    result = cursor.fetchone()
                    emp["total_absent"] = result["COUNT(*)"] if result else 0
                    
                    # Leave dates with times (from attendance table)
                    cursor.execute("""SELECT att_date, in_time FROM attendance
                                   WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Leave'
                                   ORDER BY att_date""", (emp_id, start_date, end_date))
                    leave_records = cursor.fetchall()
                    emp["leave_dates"] = [{"date": str(r["att_date"]), "time": str(r["in_time"])} for r in leave_records]
            else:
                # No joining date, use full month
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status IN ('Present', 'Late')",
                               (emp_id, start_date, end_date))
                result = cursor.fetchone()
                emp["total_present"] = result["COUNT(*)"] if result else 0
                
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Leave'",
                               (emp_id, start_date, end_date))
                result = cursor.fetchone()
                emp["total_leave"] = result["COUNT(*)"] if result else 0
                
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE emp_id=%s AND att_date BETWEEN %s AND %s AND status='Absent'",
                               (emp_id, start_date, end_date))
                result = cursor.fetchone()
                emp["total_absent"] = result["COUNT(*)"] if result else 0

        cursor.close(); conn.close()
        return jsonify({"success": True, "profile": emp}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Delete employee (admin) ───────────────────────────────────────────────────
@app.route("/api/employees/<emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    try:
        conn   = get_db()
        cursor = conn.cursor(dictionary=True)

        # Get face paths before deleting
        cursor.execute("SELECT face_image_path, profile_pic_path FROM face_profiles WHERE emp_id=%s", (emp_id,))
        fp = cursor.fetchone()

        # Delete from DB (cascades to credentials, face_profiles, attendance, leaves)
        cursor.execute("DELETE FROM employees WHERE emp_id=%s", (emp_id,))
        if cursor.rowcount == 0:
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "Employee not found"}), 404

        conn.commit(); cursor.close(); conn.close()

        # Remove image files from disk
        if fp:
            for path_key in ("face_image_path", "profile_pic_path"):
                rel = fp.get(path_key)
                if rel:
                    abs_path = os.path.join(PROJECT_ROOT, rel.replace("/", os.sep))
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                        print(f"[DELETE] Removed file: {abs_path}")

        # Reload face model
        try:
            from face_recognizer_insightface import reload_faces
            threading.Thread(target=reload_faces, daemon=True).start()
        except Exception as re_err:
            print(f"[DELETE] reload_faces error: {re_err}")

        return jsonify({"success": True, "message": f"Employee {emp_id} deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Change password (employee) ────────────────────────────────────────────────
@app.route("/api/employees/change-password", methods=["POST"])
def change_password():
    try:
        data        = request.get_json()
        emp_id      = (data.get("emp_id") or "").strip()
        current_pw  = (data.get("current_password") or "").strip()
        new_pw      = (data.get("new_password") or "").strip()
        if not all([emp_id, current_pw, new_pw]):
            return jsonify({"success": False, "error": "All fields required"}), 400
        ok, err = validate_password(new_pw)
        if not ok:
            return jsonify({"success": False, "error": err}), 400

        conn   = get_db(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employee_credentials WHERE emp_id=%s AND is_active=1", (emp_id,))
        rec = cursor.fetchone()
        if not rec:
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "Employee not found"}), 404
        if not verify_password(current_pw, rec["password_hash"]):
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "Current password incorrect"}), 401

        cursor.execute("UPDATE employee_credentials SET password_hash=%s, must_change_password=0 WHERE emp_id=%s",
                       (hash_password(new_pw), emp_id))
        conn.commit(); cursor.close(); conn.close()
        return jsonify({"success": True, "message": "Password updated"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Face recognition ──────────────────────────────────────────────────────────
def check_scan_cooldown(emp_id, cooldown_minutes=10):
    """
    Check if employee has scanned recently (within cooldown period)
    Returns: (is_in_cooldown, last_scan_time)
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check last scan in the last N minutes
        cursor.execute("""
            SELECT MAX(created_at) as last_scan 
            FROM attendance_logs 
            WHERE emp_id = %s 
            AND created_at > DATE_SUB(NOW(), INTERVAL %s MINUTE)
        """, (emp_id, cooldown_minutes))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['last_scan']:
            return True, result['last_scan']
        return False, None
    except Exception as e:
        print(f"[COOLDOWN] Error checking cooldown: {e}")
        return False, None

@app.route("/api/attendance/finalize-now", methods=["POST"])
def finalize_now():
    """Manual finalization endpoint for testing - can finalize any date"""
    try:
        from datetime import date as dt_date
        request_data = request.get_json() or {}
        target_date = request_data.get("date")
        
        if target_date:
            target_date = dt_date.fromisoformat(target_date)
        else:
            target_date = datetime.now().date()
        
        print(f"[FINALIZE_NOW] 🔧 Manual finalization requested for {target_date}")
        
        conn = get_db()
        from attendance_engine_enhanced_fixed import EnhancedAttendanceEngine
        engine = EnhancedAttendanceEngine(conn)
        
        result = engine.finalize_daily_attendance(target_date)
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Finalization completed for {target_date}",
            "result": result
        }), 200
    except Exception as e:
        print(f"[FINALIZE] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/finalize-all-pending", methods=["POST"])
def finalize_all_pending():
    """Finalize all pending records from past dates only (not future dates)"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        today = datetime.now().date()
        current_time = datetime.now().time()
        
        # Get all dates with pending records that are in the past
        # OR today if it's past 7:15 PM
        cursor.execute("""
            SELECT DISTINCT att_date FROM attendance 
            WHERE status = 'Pending' AND attendance_locked = 0
            AND att_date < %s
            ORDER BY att_date ASC
        """, (today,))
        
        pending_dates = [row['att_date'] for row in cursor.fetchall()]
        
        # Also include today if it's past 7:15 PM
        if current_time >= FINALIZE_TIME:
            cursor.execute("""
                SELECT DISTINCT att_date FROM attendance 
                WHERE status = 'Pending' AND attendance_locked = 0
                AND att_date = %s
            """, (today,))
            today_pending = [row['att_date'] for row in cursor.fetchall()]
            pending_dates.extend(today_pending)
        
        cursor.close()
        
        print(f"[FINALIZE_ALL] 🔧 Found {len(pending_dates)} dates with pending records to finalize: {pending_dates}")
        
        if not pending_dates:
            return jsonify({
                "success": True,
                "message": "No pending records to finalize (future dates are not finalized)",
                "dates_finalized": []
            }), 200
        
        from attendance_engine_enhanced_fixed import EnhancedAttendanceEngine
        engine = EnhancedAttendanceEngine(conn)
        
        results = []
        for date_to_finalize in pending_dates:
            print(f"[FINALIZE_ALL] 🔄 Finalizing {date_to_finalize}...")
            result = engine.finalize_daily_attendance(date_to_finalize)
            results.append({
                "date": str(date_to_finalize),
                "result": result
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Finalized {len(pending_dates)} past dates",
            "dates_finalized": [str(d) for d in pending_dates],
            "results": results
        }), 200
    except Exception as e:
        print(f"[FINALIZE_ALL] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/revert-to-pending", methods=["POST"])
def revert_to_pending():
    """Revert finalized records back to PENDING for a specific date"""
    try:
        request_data = request.get_json() or {}
        target_date = request_data.get("date")
        
        if not target_date:
            return jsonify({"success": False, "error": "Date is required"}), 400
        
        from datetime import date as dt_date
        target_date = dt_date.fromisoformat(target_date)
        today = datetime.now().date()
        
        # Allow reverting today or future dates, but not past dates
        if target_date < today:
            return jsonify({
                "success": False, 
                "error": f"Cannot revert past dates (before {today})"
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Revert all records for this date back to PENDING (except those with scans)
        cursor.execute("""
            UPDATE attendance 
            SET status = 'Pending', attendance_locked = 0, updated_at = NOW()
            WHERE att_date = %s AND in_time IS NULL
        """, (target_date,))
        
        reverted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[REVERT] ✅ Reverted {reverted_count} records for {target_date} back to PENDING")
        
        return jsonify({
            "success": True,
            "message": f"Reverted {reverted_count} records for {target_date} back to PENDING",
            "date": str(target_date),
            "reverted_count": reverted_count
        }), 200
    except Exception as e:
        print(f"[REVERT] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


def check_pending():
    """Check how many pending records exist"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        today = datetime.now().date()
        cursor.execute("""
            SELECT emp_id, status, attendance_locked, in_time, leave_status
            FROM attendance 
            WHERE att_date = %s
            ORDER BY emp_id
        """, (today,))
        
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        pending_count = sum(1 for r in records if r['status'] == 'Pending')
        locked_count = sum(1 for r in records if r['attendance_locked'] == 1)
        
        return jsonify({
            "success": True,
            "date": str(today),
            "total_records": len(records),
            "pending_count": pending_count,
            "locked_count": locked_count,
            "records": records
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/attendance/recognize", methods=["POST"])
def recognize():
    """
    Face recognition with automatic attendance logging
    Uses hybrid attendance system for multiple entries per day
    Includes scan cooldown to prevent duplicate scans
    """
    try:
        # Debug: Check request content type and size
        print(f"[RECOG] Content-Type: {request.content_type}")
        print(f"[RECOG] Content-Length: {request.content_length}")
        
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            print(f"[RECOG] ❌ JSON parsing error: {json_error}")
            return jsonify({"success": False, "error": f"Invalid JSON: {str(json_error)}"}), 400
        
        print(f"[RECOG] Received request with keys: {data.keys() if data else 'None'}")
        
        if not data:
            print("[RECOG] ❌ Request body is empty")
            return jsonify({"success": False, "error": "Request body is empty"}), 400
        
        b64  = data.get("image") or data.get("image_data") or ""
        print(f"[RECOG] Image data length: {len(b64) if b64 else 0}")
        
        if not b64:
            print("[RECOG] ❌ No image provided in request")
            return jsonify({"success": False, "error": "No image provided"}), 400
        
        if "," in b64:
            b64 = b64.split(",", 1)[1]
            print(f"[RECOG] Stripped data URL prefix, new length: {len(b64)}")
        
        try:
            img_bytes = base64.b64decode(b64)
            print(f"[RECOG] Decoded image bytes: {len(img_bytes)} bytes")
        except Exception as decode_error:
            print(f"[RECOG] ❌ Failed to decode base64: {decode_error}")
            return jsonify({"success": False, "error": f"Invalid image format: {str(decode_error)}"}), 400

        from face_recognizer_insightface import recognize_face
        print("[RECOG] 🎯 Using InsightFace with ArcFace embeddings")
        
        emp_id, sim = recognize_face(img_bytes)
        
        if emp_id is None:
            print("[RECOG] ❌ Face not recognised - similarity below threshold or no face detected")
            return jsonify({"success": False, "error": "❌ Face not recognised. Please look directly at the camera and try again."}), 200
        
        print(f"[RECOG] ✅ Recognized: {emp_id} (confidence: {sim})")
        
        # ── VALIDATE that the recognised emp_id actually exists in the DB ──
        val_conn = get_db()
        val_cursor = val_conn.cursor(dictionary=True)
        val_cursor.execute("SELECT emp_id, full_name FROM employees WHERE emp_id = %s AND status = 'Active'", (emp_id,))
        validated_emp = val_cursor.fetchone()
        val_cursor.close()
        val_conn.close()
        
        if not validated_emp:
            print(f"[RECOG] ❌ Recognised emp_id '{emp_id}' not found or inactive in DB — rejecting & purging stale embedding")
            # Auto-purge the stale embedding so it won't cause false matches again
            try:
                from face_recognizer_insightface import remove_embedding
                threading.Thread(target=remove_embedding, args=(emp_id,), daemon=True).start()
            except Exception as purge_err:
                print(f"[RECOG] ⚠️ Could not purge embedding: {purge_err}")
            return jsonify({"success": False, "error": "❌ Face not recognised. Please register with the admin first."}), 200
        
        # CHECK SCAN COOLDOWN (10 minutes)
        is_in_cooldown, last_scan_time = check_scan_cooldown(emp_id, cooldown_minutes=10)
        if is_in_cooldown:
            print(f"[RECOG] ⏱️ Scan cooldown active for {emp_id}, last scan: {last_scan_time}")
            return jsonify({
                "success": False, 
                "error": "⏱️ Please wait 10 minutes before scanning again",
                "last_scan": str(last_scan_time),
                "message": "Duplicate scan prevented - cooldown active"
            }), 429  # 429 = Too Many Requests
        
        if emp_id:
            # Create attendance log AND update attendance table for dashboard
            try:
                conn = get_db()
                cursor = conn.cursor(dictionary=True)
                
                # Get employee name
                cursor.execute("SELECT full_name FROM employees WHERE emp_id = %s", (emp_id,))
                employee = cursor.fetchone()
                
                today = datetime.now().date()
                now_dt = datetime.now()
                now_time = now_dt.time()
                
                # Determine ENTRY vs EXIT: check last scan today
                cursor.execute("""
                    SELECT action FROM attendance_logs 
                    WHERE emp_id = %s AND DATE(att_date) = %s 
                    ORDER BY created_at DESC LIMIT 1
                """, (emp_id, today))
                last_log = cursor.fetchone()
                action = 'EXIT' if (last_log and last_log.get('action') == 'ENTRY') else 'ENTRY'
                
                # Insert into attendance_logs (att_date = exact scan datetime, created_at auto-set)
                cursor.execute("""
                    INSERT INTO attendance_logs (emp_id, att_date, action)
                    VALUES (%s, %s, %s)
                """, (emp_id, now_dt, action))
                log_id = cursor.lastrowid
                
                # Create or update attendance table (this is what dashboards read!)
                cursor.execute("SELECT id, in_time, out_time FROM attendance WHERE emp_id=%s AND att_date=%s", (emp_id, today))
                att_rec = cursor.fetchone()
                
                is_late = 1 if now_time > LATE_TIME else 0
                new_status = STATUS_LATE if is_late else STATUS_PRESENT
                now_time_str = now_time.strftime("%H:%M:%S")
                
                # Fetch leave_status for this employee and date
                cursor.execute("""
                    SELECT status FROM leave_applications
                    WHERE emp_id = %s AND %s BETWEEN from_date AND to_date
                    ORDER BY created_at DESC LIMIT 1
                """, (emp_id, today))
                leave_app = cursor.fetchone()
                leave_status = leave_app['status'] if leave_app else 'Not Applied'
                
                if action == 'ENTRY':
                    if not att_rec:
                        # Create new attendance record with first entry time
                        cursor.execute("""
                            INSERT INTO attendance (emp_id, att_date, in_time, status, is_late, leave_status, source, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, 'Camera', NOW())
                        """, (emp_id, today, now_time_str, new_status, is_late, leave_status))
                    elif att_rec.get('in_time') is None:
                        # First entry - set in_time only
                        cursor.execute("""
                            UPDATE attendance SET in_time=%s, status=%s, is_late=%s, leave_status=%s
                            WHERE emp_id=%s AND att_date=%s
                        """, (now_time_str, new_status, is_late, leave_status, emp_id, today))
                    # else: in_time already set, don't update it (ignore re-entry)
                else:
                    # EXIT: always update out_time to the latest exit time
                    cursor.execute("""
                        UPDATE attendance SET out_time=%s
                        WHERE emp_id=%s AND att_date=%s
                    """, (now_time_str, emp_id, today))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                emp_name = employee["full_name"] if employee else "Unknown"
                scan_label = "ENTRY" if action == 'ENTRY' else "EXIT"
                return jsonify({
                    "success": True, 
                    "emp_id": emp_id, 
                    "confidence": round(float(sim) * 100, 1),
                    "employee_name": emp_name,
                    "message": f"✅ {'Check-in' if action == 'ENTRY' else 'Check-out'} recorded for {emp_name} (ID: {emp_id}) at {now_time.strftime('%H:%M:%S')}",
                    "log_id": log_id,
                    "scan_time": now_time.strftime("%H:%M:%S"),
                    "scan_type": action
                }), 200
                
            except Exception as attendance_error:
                print(f"[ATTENDANCE] Error creating log: {attendance_error}")
                import traceback
                traceback.print_exc()
                # Return face recognition result even if attendance logging fails
                return jsonify({
                    "success": True, 
                    "emp_id": emp_id, 
                    "confidence": float(sim),
                    "message": "Face recognized (attendance logging failed)"
                }), 200
        
        return jsonify({"success": False, "error": "Face not recognised"}), 404
        
    except Exception as e:
        print(f"[RECOG] ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ── Mark attendance ───────────────────────────────────────────────────────────
@app.route("/api/attendance/mark", methods=["POST"])
def mark_attendance():
    """
    NEW Attendance Rules:
      • Only record attendance on face recognition entry event
      • Status is ALWAYS "Present" when face is detected
      • is_late flag determines if entry was after 11:00 AM
      • Leave and Absent are ONLY set by 7 PM finalizer
      • Leave can be overridden if employee scans in
      • ATTENDANCE MARKING WINDOW: 10:00 AM to 7:15 PM ONLY
    """
    try:
        data   = request.get_json()
        emp_id = (data.get("emp_id") or "").strip()
        action = (data.get("action") or "in").lower()   # 'in' or 'out'
        if not emp_id:
            return jsonify({"success": False, "error": "emp_id required"}), 400

        # Block admin accounts
        conn   = get_db(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username FROM admins WHERE username=%s", (emp_id,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "Admin accounts cannot mark attendance"}), 403

        cursor.execute("SELECT emp_id, full_name FROM employees WHERE emp_id=%s", (emp_id,))
        emp = cursor.fetchone()
        if not emp:
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "Employee not found"}), 404

        today    = datetime.now().date()
        now_time = datetime.now().time()
        now_str  = now_time.strftime("%H:%M:%S")

        # ── CHECK ATTENDANCE MARKING WINDOW ────────────────────────────────────
        from attendance_config import ATTENDANCE_MARKING_START, ATTENDANCE_MARKING_END
        if not (ATTENDANCE_MARKING_START <= now_time < ATTENDANCE_MARKING_END):
            cursor.close(); conn.close()
            return jsonify({
                "success": False, 
                "error": f"❌ ATTENDANCE MARKING CLOSED\nAttendance can only be marked between 10:00 AM and 7:15 PM\nCurrent time: {now_str}"
            }), 403

        # Existing attendance record for today
        cursor.execute("SELECT * FROM attendance WHERE emp_id=%s AND att_date=%s", (emp_id, today))
        rec = cursor.fetchone()

        # ── OUT action ────────────────────────────────────────────────────────
        if action == "out":
            if not rec:
                cursor.close(); conn.close()
                return jsonify({"success": False, "error": "No entry record for today — scan IN first"}), 400
            if rec.get("out_time"):
                cursor.close(); conn.close()
                return jsonify({
                    "success": True,
                    "message": f"✅ CHECK-OUT ALREADY RECORDED\nEmployee ID: {emp_id}\nTime: {rec['out_time']}",
                    "emp_id": emp_id, "name": emp["full_name"],
                    "out_time": str(rec["out_time"]),
                }), 200
            
            # Record EXIT in attendance_logs
            cursor.execute("""
                INSERT INTO attendance_logs (emp_id, att_date, action, created_at)
                VALUES (%s, %s, 'EXIT', NOW())
            """, (emp_id, today))
            
            cursor.execute("UPDATE attendance SET out_time=%s WHERE emp_id=%s AND att_date=%s",
                           (now_str, emp_id, today))
            conn.commit(); cursor.close(); conn.close()
            return jsonify({
                "success": True,
                "message": f"✅ CHECK-OUT SUCCESSFUL\nEmployee ID: {emp_id}\nName: {emp['full_name']}\nTime: {now_str}",
                "emp_id": emp_id, "name": emp["full_name"],
                "out_time": now_str
            }), 200

        # ── IN action (Face Recognition Entry) ─────────────────────────────────
        # Determine late flag: after 11:00 AM = late
        in_hour   = now_time.hour
        in_minute = now_time.minute
        is_late   = False
        
        if in_hour > 11 or (in_hour == 11 and in_minute > 0):
            is_late = True
            status = "Late"
        else:
            status = "Present"
        
        if rec:
            # Already has an entry - just update exit time if needed
            if rec.get("in_time"):
                cursor.close(); conn.close()
                return jsonify({
                    "success": True,
                    "message": f"✅ CHECK-IN ALREADY RECORDED\nEmployee ID: {emp_id}\nName: {emp['full_name']}\nTime: {rec['in_time']}\nStatus: {rec['status']}",
                    "emp_id": emp_id, "name": emp["full_name"],
                    "status": rec["status"], "is_late": bool(rec.get("is_late", 0)), 
                    "in_time": str(rec["in_time"]),
                }), 200

            # Record exists but no in_time (e.g. leave/absent row added by finalizer)
            # Override Leave/Absent → Present
            old_status = rec.get("status")
            
            # Fetch leave_status for this employee and date
            cursor.execute("""
                SELECT status FROM leave_applications
                WHERE emp_id=%s AND %s BETWEEN from_date AND to_date
                ORDER BY created_at DESC LIMIT 1
            """, (emp_id, today))
            
            leave_app = cursor.fetchone()
            leave_status = leave_app['status'] if leave_app else 'Not Applied'
            
            cursor.execute("""
                UPDATE attendance
                SET in_time=%s, status=%s, is_late=%s, leave_status=%s, source='Camera'
                WHERE emp_id=%s AND att_date=%s
            """, (now_str, status, int(is_late), leave_status, emp_id, today))

            if old_status == "Leave":
                # Mark leave as auto-overridden
                cursor.execute("""
                    UPDATE leave_applications
                    SET auto_overridden=1
                    WHERE emp_id=%s AND %s BETWEEN from_date AND to_date AND status='Approved'
                """, (emp_id, today))

            conn.commit(); cursor.close(); conn.close()
            return jsonify({
                "success": True,
                "message": f"✅ CHECK-IN SUCCESSFUL\nEmployee ID: {emp_id}\nName: {emp['full_name']}\nTime: {now_str}\nStatus: {status}" + (f"\n(Override: {old_status})" if old_status=="Leave" else ""),
                "emp_id": emp_id, "name": emp["full_name"],
                "status": status, "is_late": is_late, "in_time": now_str,
            }), 200

        # ── No record yet — create new attendance record ───────────────────────────────────────────────────────
        # Fetch leave_status for this employee and date
        cursor.execute("""
            SELECT status FROM leave_applications
            WHERE emp_id=%s AND %s BETWEEN from_date AND to_date
            ORDER BY created_at DESC LIMIT 1
        """, (emp_id, today))
        
        leave_app = cursor.fetchone()
        leave_status = leave_app['status'] if leave_app else 'Not Applied'
        
        cursor.execute("""
            INSERT INTO attendance (emp_id, att_date, in_time, status, leave_status, source, created_at)
            VALUES (%s,%s,%s,%s,%s,'Camera',NOW())
        """, (emp_id, today, now_str, status, leave_status))

        conn.commit()
        cursor.close(); conn.close()
        return jsonify({
            "success": True,
            "message": f"✅ CHECK-IN SUCCESSFUL\nEmployee ID: {emp_id}\nName: {emp['full_name']}\nTime: {now_str}\nStatus: {status}",
            "emp_id": emp_id, "name": emp["full_name"],
            "status": status, "is_late": is_late, "in_time": now_str,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/today", methods=["GET"])
def get_today_attendance():
    """
    Get today's attendance records
    Slots are created at 9:45 AM only, not before
    Records stay PENDING until 7:15 PM when they are finalized
    """
    try:
        from datetime import datetime, date, time as dt_time

        today = date.today()
        now = datetime.now()
        current_time = now.time()

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        print(f"\n[TODAY_ATT] ===== LOADING ATTENDANCE FOR {today} =====")
        print(f"[TODAY_ATT] Current time: {current_time}")

        # AUTO-FINALIZE if past 7:15 PM (for today only)
        if current_time >= FINALIZE_TIME:
            print(f"[TODAY_ATT] ⏰ It's past {FINALIZE_TIME}, auto-finalizing pending records for today...")
            try:
                from attendance_engine_enhanced_fixed import EnhancedAttendanceEngine
                engine = EnhancedAttendanceEngine(conn)
                finalize_result = engine.finalize_daily_attendance(today)
                print(f"[TODAY_ATT] ✅ Auto-finalization result: {finalize_result}")
            except Exception as finalize_error:
                print(f"[TODAY_ATT] ⚠️ Auto-finalization error: {finalize_error}")

        # NOTE: Slots are created by the scheduler at 9:45 AM, not here
        # This endpoint only QUERIES existing slots, doesn't create them
        print(f"[TODAY_ATT] Querying existing attendance records for {today}...")
        
        # CHECK: If no slots exist yet and it's past 9:45 AM, generate them now
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE att_date = %s", (today,))
        slot_count = cursor.fetchone()['count']
        print(f"[TODAY_ATT] Found {slot_count} existing slots for {today}")
        
        if slot_count == 0 and current_time >= OFFICE_START:
            print(f"[TODAY_ATT] ⚠️ No slots found for today and it's past {OFFICE_START}")
            print(f"[TODAY_ATT] Generating missing slots now...")
            try:
                result = generate_daily_slots()
                print(f"[TODAY_ATT] ✅ Generated {result.get('slots_created', 0)} slots")
            except Exception as gen_error:
                print(f"[TODAY_ATT] ❌ Error generating slots: {gen_error}")
                import traceback
                traceback.print_exc()
        elif slot_count == 0:
            print(f"[TODAY_ATT] ⏳ No slots yet and before {OFFICE_START}, waiting for scheduler")

        # Now get all attendance records for today
        cursor.execute("""
            SELECT
                a.emp_id,
                a.att_date,
                a.in_time,
                a.out_time,
                a.status,
                a.source,
                e.full_name as emp_name,
                (SELECT l.status FROM leave_applications l
                 WHERE l.emp_id = a.emp_id
                 AND %s BETWEEN l.from_date AND l.to_date
                 ORDER BY l.created_at DESC LIMIT 1) as leave_status
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.att_date = %s
            ORDER BY e.full_name ASC
        """, (today, today))

        attendance_records = cursor.fetchall()
        print(f"[TODAY_ATT] Queried {len(attendance_records)} records from database")

        # Format the response
        formatted_records = []
        for record in attendance_records:
            status_value = record['status'] or 'pending'
            leave_status = record['leave_status']

            # DO NOT override status - keep it as is (PENDING, PRESENT, LATE, ABSENT)
            # Leave status is shown separately in the leave_status column
            
            print(f"[TODAY_ATT] Record {record['emp_id']}: status={record['status']}, leave_status={leave_status}")
            formatted_records.append({
                "emp_id": record['emp_id'],
                "emp_name": record['emp_name'],
                "att_date": record['att_date'].strftime('%Y-%m-%d'),
                "in_time": str(record['in_time']) if record['in_time'] else None,
                "out_time": str(record['out_time']) if record['out_time'] else None,
                "status": status_value,
                "leave_status": leave_status if leave_status else 'Not Applied',
                "source": record['source'] or 'system'
            })

        cursor.close()
        conn.close()

        print(f"[TODAY_ATT] Returning {len(formatted_records)} attendance records")
        print(f"[TODAY_ATT] ===== END LOADING =====\n")

        return jsonify({
            "success": True,
            "date": today.strftime('%Y-%m-%d'),
            "attendance": formatted_records,
            "summary": {
                "total": len(formatted_records),
                "pending": len([r for r in formatted_records if r['status'].lower() == 'pending']),
                "present": len([r for r in formatted_records if r['status'].lower() == 'present']),
                "late": len([r for r in formatted_records if r['status'].lower() == 'late']),
                "absent": len([r for r in formatted_records if r['status'].lower() == 'absent']),
                "leave": len([r for r in formatted_records if r['status'].lower() == 'leave'])
            }
        }), 200

    except Exception as e:
        print(f"[TODAY_ATT] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/attendance")
def get_attendance():
    try:
        emp_id = request.args.get("emp_id")
        date   = request.args.get("date")
        month  = request.args.get("month")
        conn   = get_db(); cursor = conn.cursor(dictionary=True)

        sql  = """SELECT a.*, e.full_name as name, e.joining_date,
                  (SELECT l.status FROM leave_applications l 
                   WHERE l.emp_id = a.emp_id 
                   AND a.att_date BETWEEN l.from_date AND l.to_date 
                   ORDER BY l.created_at DESC LIMIT 1) as leave_status
                  FROM attendance a JOIN employees e ON a.emp_id=e.emp_id 
                  WHERE 1=1 AND (e.joining_date IS NULL OR a.att_date >= e.joining_date)"""
        args = []
        
        if emp_id:
            sql += " AND a.emp_id=%s"; args.append(emp_id)
        if date:
            sql += " AND a.att_date=%s"; args.append(date)
        elif month:
            sql += " AND a.att_date LIKE %s"; args.append(month+"%")
        sql += " ORDER BY a.att_date DESC, a.in_time DESC"

        cursor.execute(sql, args)
        rows = cursor.fetchall()
        
        # Debug: Print row data and types
        print("DEBUG: Attendance rows returned:")
        for i, row in enumerate(rows):
            print(f"  Row {i}: {row}")
            for key, value in row.items():
                print(f"    {key}: {value} (type: {type(value)})")
        
        # Format att_date as string to avoid timezone issues in JSON
        for row in rows:
            if row.get('att_date'):
                row['att_date'] = row['att_date'].strftime('%Y-%m-%d')
            # Set leave_status to 'Not Applied' if None
            if not row.get('leave_status'):
                row['leave_status'] = 'Not Applied'
            # Convert all time/datetime objects to strings for JSON serialization
            for key in ['in_time', 'out_time', 'created_at', 'updated_at']:
                if row.get(key) and hasattr(row[key], 'seconds'):
                    row[key] = str(row[key])
                elif row.get(key) and hasattr(row[key], 'year'):
                    # Handle datetime objects
                    row[key] = row[key].strftime('%H:%M:%S') if key in ['in_time', 'out_time'] else row[key].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close(); conn.close()
        return jsonify({"success": True, "attendance": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attendance/logs", methods=["GET"])
def get_attendance_logs():
    """
    Get detailed logs and metadata for View Button Behavior
    Includes: Name, Dept, Leave Status, Locked Status, Scan Logs
    """
    try:
        emp_id = request.args.get("emp_id")
        date = request.args.get("date")
        
        if not emp_id or not date:
            return jsonify({"success": False, "error": "Employee ID and date are required"}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Fetch Employee & Attendance Metadata
        cursor.execute("""
            SELECT 
                e.full_name, e.designation,
                a.id, a.attendance_locked, a.status as attendance_status
            FROM employees e
            LEFT JOIN attendance a ON e.emp_id = a.emp_id AND a.att_date = %s
            WHERE e.emp_id = %s
        """, (date, emp_id))
        meta = cursor.fetchone()
        
        if not meta:
            cursor.close(); conn.close()
            return jsonify({"success": False, "error": "Employee not found"}), 404

        # 2. Fetch Leave Status
        cursor.execute("""
            SELECT status FROM leave_applications 
            WHERE emp_id = %s AND %s BETWEEN from_date AND to_date 
            ORDER BY created_at DESC LIMIT 1
        """, (emp_id, date))
        leave_row = cursor.fetchone()
        leave_status = leave_row['status'] if leave_row else 'Not Applied'
        
        # 3. Fetch Scan Logs
        cursor.execute("""
            SELECT action, scan_method, created_at, att_date
            FROM attendance_logs 
            WHERE emp_id = %s AND DATE(att_date) = %s
            ORDER BY created_at ASC
        """, (emp_id, date))
        logs = cursor.fetchall()
        
        # Format for JSON - use att_date which has the exact timestamp
        formatted_logs = []
        for log in logs:
            formatted_log = {
                'action': log.get('action'),
                'scan_method': log.get('scan_method'),
                'created_at': None
            }
            # Try att_date first (has exact timestamp), then created_at
            time_val = log.get('att_date') or log.get('created_at')
            if time_val and hasattr(time_val, 'strftime'):
                formatted_log['created_at'] = time_val.strftime('%H:%M:%S')
            elif time_val:
                formatted_log['created_at'] = str(time_val)
            formatted_logs.append(formatted_log)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "metadata": {
                "name": meta['full_name'],
                "department": meta['designation'],
                "leave_status": leave_status,
                "attendance_locked": bool(meta['attendance_locked']),
                "attendance_status": meta['attendance_status']
            },
            "logs": formatted_logs
        }), 200
        
    except Exception as e:
        print(f"[LOG_API] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ── Monthly Average Times ───────────────────────────────────────────────────────
@app.route("/api/attendance/monthly-averages", methods=["GET"])
def get_monthly_averages():
    """
    Get monthly average check-in and check-out times for all employees
    Returns simple format for frontend display
    Only includes attendance records on or after employee's joining date
    """
    try:
        import mysql.connector
        
        # Get current month
        from datetime import datetime
        now = datetime.now()
        current_month = f"{now.year}-{now.month:02d}"
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                a.emp_id,
                AVG(EXTRACT(HOUR FROM a.in_time) * 60 + EXTRACT(MINUTE FROM a.in_time)) as avg_in_minutes,
                AVG(EXTRACT(HOUR FROM a.out_time) * 60 + EXTRACT(MINUTE FROM a.out_time)) as avg_out_minutes,
                COUNT(*) as total_days,
                COUNT(CASE WHEN a.in_time IS NOT NULL THEN 1 END) as days_with_in_time,
                COUNT(CASE WHEN a.out_time IS NOT NULL THEN 1 END) as days_with_out_time
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE DATE_FORMAT(a.att_date, '%Y-%m') = %s
            AND a.status IN ('present', 'late')
            AND (e.joining_date IS NULL OR a.att_date >= e.joining_date)
            GROUP BY a.emp_id
            ORDER BY a.emp_id
        """
        
        cursor.execute(query, (current_month,))
        results = cursor.fetchall()
        
        # Process results
        monthly_averages = []
        for result in results:
            avg_in_time = None
            avg_out_time = None
            
            if result['avg_in_minutes'] is not None:
                avg_in_minutes = int(result['avg_in_minutes'])
                avg_in_hour = avg_in_minutes // 60
                avg_in_min = avg_in_minutes % 60
                avg_in_time = f"{avg_in_hour:02d}:{avg_in_min:02d}"
            
            if result['avg_out_minutes'] is not None:
                avg_out_minutes = int(result['avg_out_minutes'])
                avg_out_hour = avg_out_minutes // 60
                avg_out_min = avg_out_minutes % 60
                avg_out_time = f"{avg_out_hour:02d}:{avg_out_min:02d}"
            
            monthly_averages.append({
                "emp_id": result['emp_id'],
                "avg_in_time": avg_in_time,
                "avg_out_time": avg_out_time,
                "total_days": result['total_days'],
                "days_present": result['days_with_in_time']
            })
        
        return jsonify({
            "success": True,
            "month": current_month,
            "data": monthly_averages
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Average Times Calculation ───────────────────────────────────────────────────────
@app.route("/api/attendance/average-times", methods=["GET"])
def get_average_times():
    """
    Calculate average check-in and check-out times for employees
    Returns average in_time and out_time for specified date range
    """
    try:
        from datetime import datetime, time, timedelta
        import mysql.connector
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        emp_id = request.args.get('emp_id')  # Optional: specific employee
        
        if not start_date or not end_date:
            return jsonify({"success": False, "error": "start_date and end_date are required"}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Build query based on whether specific employee is requested
        if emp_id:
            query = """
                SELECT 
                    a.emp_id,
                    AVG(EXTRACT(HOUR FROM a.in_time) * 60 + EXTRACT(MINUTE FROM a.in_time)) as avg_in_minutes,
                    AVG(EXTRACT(HOUR FROM a.out_time) * 60 + EXTRACT(MINUTE FROM a.out_time)) as avg_out_minutes,
                    COUNT(*) as total_days,
                    COUNT(CASE WHEN a.in_time IS NOT NULL THEN 1 END) as days_with_in_time,
                    COUNT(CASE WHEN a.out_time IS NOT NULL THEN 1 END) as days_with_out_time
                FROM attendance a
                JOIN employees e ON a.emp_id = e.emp_id
                WHERE a.att_date BETWEEN %s AND %s 
                AND a.emp_id = %s
                AND a.status IN ('present', 'late')
                AND (e.joining_date IS NULL OR a.att_date >= e.joining_date)
                GROUP BY a.emp_id
            """
            cursor.execute(query, (start_date, end_date, emp_id))
        else:
            query = """
                SELECT 
                    a.emp_id,
                    AVG(EXTRACT(HOUR FROM a.in_time) * 60 + EXTRACT(MINUTE FROM a.in_time)) as avg_in_minutes,
                    AVG(EXTRACT(HOUR FROM a.out_time) * 60 + EXTRACT(MINUTE FROM a.out_time)) as avg_out_minutes,
                    COUNT(*) as total_days,
                    COUNT(CASE WHEN a.in_time IS NOT NULL THEN 1 END) as days_with_in_time,
                    COUNT(CASE WHEN a.out_time IS NOT NULL THEN 1 END) as days_with_out_time
                FROM attendance a
                JOIN employees e ON a.emp_id = e.emp_id
                WHERE a.att_date BETWEEN %s AND %s 
                AND a.status IN ('present', 'late')
                AND (e.joining_date IS NULL OR a.att_date >= e.joining_date)
                GROUP BY a.emp_id
            """
            cursor.execute(query, (start_date, end_date))
        
        results = cursor.fetchall()
        
        # Process results and convert minutes to time format
        processed_results = []
        for result in results:
            avg_in_time = None
            avg_out_time = None
            
            if result['avg_in_minutes'] is not None:
                avg_in_minutes = int(result['avg_in_minutes'])
                avg_in_hour = avg_in_minutes // 60
                avg_in_min = avg_in_minutes % 60
                avg_in_time = f"{avg_in_hour:02d}:{avg_in_min:02d}"
            
            if result['avg_out_minutes'] is not None:
                avg_out_minutes = int(result['avg_out_minutes'])
                avg_out_hour = avg_out_minutes // 60
                avg_out_min = avg_out_minutes % 60
                avg_out_time = f"{avg_out_hour:02d}:{avg_out_min:02d}"
            
            processed_results.append({
                "emp_id": result['emp_id'],
                "avg_in_time": avg_in_time,
                "avg_out_time": avg_out_time,
                "total_days": result['total_days'],
                "days_with_in_time": result['days_with_in_time'],
                "days_with_out_time": result['days_with_out_time'],
                "in_time_coverage": round((result['days_with_in_time'] / result['total_days']) * 100, 1) if result['total_days'] > 0 else 0,
                "out_time_coverage": round((result['days_with_out_time'] / result['total_days']) * 100, 1) if result['total_days'] > 0 else 0
            })
        
        # Calculate overall averages if not specific employee
        overall_avg = None
        if not emp_id and processed_results:
            total_in_minutes = 0
            total_out_minutes = 0
            total_in_days = 0
            total_out_days = 0
            
            for result in processed_results:
                if result['avg_in_time']:
                    hour_min = result['avg_in_time'].split(':')
                    total_in_minutes += int(hour_min[0]) * 60 + int(hour_min[1])
                    total_in_days += 1
                
                if result['avg_out_time']:
                    hour_min = result['avg_out_time'].split(':')
                    total_out_minutes += int(hour_min[0]) * 60 + int(hour_min[1])
                    total_out_days += 1
            
            overall_avg = {
                "avg_in_time": f"{total_in_minutes // total_in_days // 60:02d}:{total_in_minutes // total_in_days % 60:02d}" if total_in_days > 0 else None,
                "avg_out_time": f"{total_out_minutes // total_out_days // 60:02d}:{total_out_minutes // total_out_days % 60:02d}" if total_out_days > 0 else None
            }
        
        return jsonify({
            "success": True,
            "data": processed_results,
            "overall_average": overall_avg,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_employees": len(processed_results),
                "employees_with_in_time": len([r for r in processed_results if r['avg_in_time']]),
                "employees_with_out_time": len([r for r in processed_results if r['avg_out_time']])
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Hybrid Attendance System ───────────────────────────────────────────────────────
@app.route("/api/attendance/hybrid", methods=["GET"])
def get_hybrid_attendance():
    """
    Comprehensive hybrid attendance system with smart logic
    Returns summarized attendance with calculated statuses and work hours
    """
    try:
        from datetime import datetime, time, timedelta
        import mysql.connector
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        emp_id = request.args.get('emp_id')
        
        print(f"Hybrid attendance request: start_date={start_date}, end_date={end_date}, emp_id={emp_id}")
        
        # Default to current month if no dates provided
        if not start_date or not end_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        
        conn = get_db()
        if not conn:
            return jsonify({"success": False, "error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Use attendance table instead of attendance_logs for more reliable data
        if emp_id:
            base_query = """
                SELECT 
                    a.emp_id,
                    a.att_date,
                    a.in_time,
                    a.out_time,
                    a.status,
                    a.is_late,
                    a.is_absent,
                    a.source
                FROM attendance a
                JOIN employees e ON a.emp_id = e.emp_id
                WHERE DATE(a.att_date) BETWEEN %s AND %s 
                AND a.emp_id = %s
                AND (e.joining_date IS NULL OR a.att_date >= e.joining_date)
                ORDER BY a.att_date DESC
            """
            params = [start_date, end_date, emp_id]
        else:
            base_query = """
                SELECT 
                    a.emp_id,
                    a.att_date,
                    a.in_time,
                    a.out_time,
                    a.status,
                    a.is_late,
                    a.is_absent,
                    a.source
                FROM attendance a
                JOIN employees e ON a.emp_id = e.emp_id
                WHERE DATE(a.att_date) BETWEEN %s AND %s
                AND (e.joining_date IS NULL OR a.att_date >= e.joining_date)
                ORDER BY a.att_date DESC, a.emp_id ASC
            """
            params = [start_date, end_date]
        
        try:
            cursor.execute(base_query, params)
            daily_logs = cursor.fetchall()
            print(f"Query executed successfully, fetched {len(daily_logs)} records")
        except Exception as e:
            print(f"SQL Error in main query: {e}")
            print(f"Query: {base_query}")
            print(f"Params: {params}")
            
            # Try a simpler query as fallback
            try:
                simple_query = """
                    SELECT emp_id, att_date, status, in_time, out_time 
                    FROM attendance 
                    WHERE DATE(att_date) BETWEEN %s AND %s
                    LIMIT 10
                """
                cursor.execute(simple_query, [start_date, end_date])
                daily_logs = cursor.fetchall()
                print(f"Fallback query executed, fetched {len(daily_logs)} records")
            except Exception as e2:
                print(f"Fallback query also failed: {e2}")
                return jsonify({"success": False, "error": f"SQL Error: {str(e)}"}), 500
        
        # Get employee information
        emp_query = "SELECT emp_id, full_name FROM employees"
        cursor.execute(emp_query)
        employees = {emp['emp_id']: emp['full_name'] for emp in cursor.fetchall()}
        
        # Process attendance data
        processed_data = []
        for log in daily_logs:
            try:
                emp_data = {
                    "emp_id": log['emp_id'],
                    "emp_name": employees.get(log['emp_id'], log['emp_id']),
                    "att_date": log['att_date'].strftime('%Y-%m-%d') if hasattr(log['att_date'], 'strftime') else str(log['att_date']),
                    "in_time": str(log['in_time']) if log['in_time'] else None,
                    "out_time": str(log['out_time']) if log['out_time'] else None,
                    "status": log['status'] or 'present',
                    "is_late": bool(log['is_late']),
                    "is_absent": bool(log['is_absent']),
                    "source": log['source'] or 'system'
                }
                processed_data.append(emp_data)
            except Exception as e:
                print(f"Error processing log {log}: {e}")
                continue
        
        cursor.close()
        conn.close()
        
        print(f"Returning {len(processed_data)} attendance records")
        
        return jsonify({
            "success": True,
            "attendance": processed_data,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_records": len(processed_data),
                "present": len([r for r in processed_data if r['status'] == 'present']),
                "late": len([r for r in processed_data if r['status'] == 'late']),
                "absent": len([r for r in processed_data if r['status'] == 'absent'])
            }
        }), 200
        
    except Exception as e:
        print(f"Error in get_hybrid_attendance: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ── Leave Applications ────────────────────────────────────────────────────────
@app.route("/api/leaves", methods=["GET", "POST"])
def get_leaves():
    """Get all leave applications (GET) or submit new leave (POST)"""
    try:
        if request.method == "POST":
            # Submit new leave application
            data = request.get_json()
            emp_id = data.get("emp_id")
            from_date = data.get("from_date")
            to_date = data.get("to_date")
            leave_type = data.get("leave_type")
            reason = data.get("reason", "")
            
            if not all([emp_id, from_date, to_date, leave_type]):
                return jsonify({"success": False, "error": "Missing required fields"}), 400
            
            # Parse dates
            try:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
                to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
            today = datetime.now().date()
            current_time = datetime.now().time()
            
            # VALIDATION 1: Cannot apply for past days
            if from_date_obj < today:
                return jsonify({
                    "success": False,
                    "error": "❌ Cannot apply leave for past dates. Leave start date must be today or later."
                }), 400
            
            # VALIDATION 2: If applying for today, must be before 5 PM
            if from_date_obj == today:
                cutoff_time = datetime.strptime("17:00:00", "%H:%M:%S").time()  # 5 PM
                if current_time >= cutoff_time:
                    return jsonify({
                        "success": False,
                        "error": f"❌ Too late to apply leave for today. Leave for today can only be applied before 5:00 PM. Current time: {current_time.strftime('%H:%M:%S')}"
                    }), 400
            
            # VALIDATION 3: to_date must be >= from_date
            if to_date_obj < from_date_obj:
                return jsonify({
                    "success": False,
                    "error": "❌ Leave end date must be on or after the start date."
                }), 400
            
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            try:
                # DEBUG: Check all leaves for this employee
                cursor.execute("""
                    SELECT id, from_date, to_date, status FROM leave_applications
                    WHERE emp_id = %s
                    ORDER BY from_date DESC
                """, (emp_id,))
                all_leaves = cursor.fetchall()
                print(f"[LEAVE] All leaves for {emp_id}: {all_leaves}")
                
                # CHECK FOR OVERLAPPING LEAVE APPLICATIONS
                cursor.execute("""
                    SELECT id, from_date, to_date, status FROM leave_applications
                    WHERE emp_id = %s 
                    AND status IN ('Pending', 'Approved')
                    AND (
                        (from_date <= %s AND to_date >= %s) OR
                        (from_date <= %s AND to_date >= %s) OR
                        (from_date >= %s AND to_date <= %s)
                    )
                """, (emp_id, to_date, from_date, to_date, from_date, from_date, to_date))
                
                overlapping = cursor.fetchall()
                print(f"[LEAVE] Overlapping leaves found: {overlapping}")
                
                if overlapping:
                    cursor.close()
                    conn.close()
                    overlap_info = ", ".join([f"{o['from_date']} to {o['to_date']} ({o['status']})" for o in overlapping])
                    print(f"[LEAVE] Overlap detected for {emp_id}: {overlap_info}")
                    return jsonify({
                        "success": False, 
                        "error": f"❌ Leave dates overlap with existing application(s): {overlap_info}"
                    }), 409  # 409 = Conflict
                
                print(f"[LEAVE] No overlap found for {emp_id} from {from_date} to {to_date}")
                
                # No overlap - proceed with insertion
                cursor.execute("""
                    INSERT INTO leave_applications (emp_id, from_date, to_date, leave_type, reason, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'Pending', NOW())
                """, (emp_id, from_date, to_date, leave_type, reason))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                return jsonify({"success": True, "message": "Leave application submitted successfully"}), 201
            except Exception as e:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"success": False, "error": str(e)}), 500
        
        else:
            # GET: Retrieve leave applications
            emp_id = request.args.get("emp_id")
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            if emp_id:
                cursor.execute("SELECT * FROM leave_applications WHERE emp_id=%s ORDER BY created_at DESC", (emp_id,))
            else:
                cursor.execute("""
                    SELECT l.*, e.full_name FROM leave_applications l
                    JOIN employees e ON l.emp_id=e.emp_id
                    ORDER BY l.created_at DESC """
                )
            
            leaves = cursor.fetchall()
            
            # Format created_at to only show date (YYYY-MM-DD)
            for leave in leaves:
                if leave.get('created_at'):
                    # Convert datetime to date string
                    created_at = leave['created_at']
                    if isinstance(created_at, str):
                        leave['created_at'] = created_at.split(' ')[0]  # Get only date part
                    else:
                        leave['created_at'] = created_at.strftime('%Y-%m-%d')
            
            cursor.close()
            conn.close()
            
            return jsonify({"success": True, "leaves": leaves}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/leaves/<int:leave_id>", methods=["PUT"])
def update_leave(leave_id):
    """Update leave application status (Approve/Reject)"""
    try:
        data = request.get_json()
        status = data.get("status")
        reviewed_by = data.get("reviewed_by", "admin")
        
        if not status or status not in ["Approved", "Rejected"]:
            return jsonify({"success": False, "error": "Invalid status"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE leave_applications 
                SET status=%s, reviewed_by=%s, reviewed_at=NOW()
                WHERE id=%s
            """, (status, reviewed_by, leave_id))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "error": "Leave application not found"}), 404
            
            cursor.close()
            conn.close()
            
            return jsonify({"success": True, "message": f"Leave {status.lower()} successfully"}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Attendance Correction (Admin Only) ────────────────────────────────────
@app.route("/api/attendance/correct", methods=["PUT"])
def correct_attendance():
    """
    Admin endpoint to correct locked attendance records
    Allows unlocking and modifying attendance after 7:15 PM
    """
    try:
        data = request.get_json()
        emp_id = data.get("emp_id")
        att_date = data.get("att_date")
        new_status = data.get("status")  # Present, Late, Absent, Leave
        in_time = data.get("in_time")
        out_time = data.get("out_time")
        notes = data.get("notes", "")
        admin_id = data.get("admin_id", "admin")
        
        if not all([emp_id, att_date, new_status]):
            return jsonify({"success": False, "error": "Missing required fields: emp_id, att_date, status"}), 400
        
        if new_status not in ["Present", "Late", "Absent", "Leave"]:
            return jsonify({"success": False, "error": "Invalid status. Must be: Present, Late, Absent, or Leave"}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check if record exists
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE emp_id = %s AND att_date = %s
            """, (emp_id, att_date))
            
            record = cursor.fetchone()
            
            if not record:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "error": "Attendance record not found"}), 404
            
            # Update attendance record
            cursor.execute("""
                UPDATE attendance 
                SET status = %s, 
                    in_time = %s,
                    out_time = %s,
                    notes = %s,
                    attendance_locked = 0,
                    updated_at = NOW()
                WHERE emp_id = %s AND att_date = %s
            """, (new_status, in_time, out_time, notes, emp_id, att_date))
            
            # Log the correction in notes
            correction_log = f"[CORRECTED by {admin_id}] Old: {record['status']}, New: {new_status}. {notes}"
            cursor.execute("""
                UPDATE attendance 
                SET notes = %s
                WHERE emp_id = %s AND att_date = %s
            """, (correction_log, emp_id, att_date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                "success": True, 
                "message": f"✅ Attendance corrected successfully",
                "emp_id": emp_id,
                "att_date": att_date,
                "old_status": record['status'],
                "new_status": new_status
            }), 200
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Daily Stats ───────────────────────────────────────────────────────────────
@app.route("/api/stats/daily", methods=["GET"])
def daily_stats():
    """Get daily attendance statistics"""
    try:
        date = request.args.get("date") or str(datetime.now().date())
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get total active employees
        cursor.execute("SELECT COUNT(*) FROM employees WHERE status='Active'")
        total = cursor.fetchone()[0]
        
        out = {"total": total, "present": 0, "late": 0, "absent": 0, "leave": 0, "pending": 0}
        
        # Get all attendance records with leave status
        cursor.execute("""
            SELECT a.*, 
                   (SELECT l.status FROM leave_applications l 
                    WHERE l.emp_id = a.emp_id 
                    AND %s BETWEEN l.from_date AND l.to_date 
                    ORDER BY l.created_at DESC LIMIT 1) as leave_status
            FROM attendance a 
            WHERE a.att_date = %s
        """, (date, date))
        
        records = cursor.fetchall()
        
        # Count statuses, considering leave applications
        for rec in records:
            status = rec['status']
            leave_status = rec['leave_status']
            
            # If employee has approved leave, override status to Leave
            if leave_status == 'Approved' and status in ['Absent', 'Pending']:
                status = 'Leave'
            
            if status == 'Present':
                out["present"] += 1
            elif status == 'Late':
                out["late"] += 1
            elif status == 'Absent':
                out["absent"] += 1
            elif status == 'Leave':
                out["leave"] += 1
            elif status == 'Pending':
                out["pending"] += 1
        
        cursor.close()
        conn.close()
        
        print(f"Daily stats for {date}: {out}")
        
        return jsonify({"success": True, **out}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Finalize Attendance (Manual Trigger) ──────────────────────────────────────
@app.route("/api/attendance/finalize", methods=["POST"])
def finalize_attendance():
    """
    Manual trigger to finalize attendance for a specific date
    Implements automatic absent record logic:
    - No approved leave + no entry → ABSENT
    - Approved leave + no entry → LEAVE
    - Approved leave + entry → overwrite LEAVE to PRESENT
    - Entry between 10:00-11:00 → on_time (is_late=0)
    - Entry after 11:00 → late (is_late=1)
    - Entry exists but no exit → mark "missing_exit"
    - Updates leave_status field based on leave_applications table
    """
    try:
        data = request.get_json()
        target_date_str = data.get("date") or str(datetime.now().date())
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get all active employees
        cursor.execute("SELECT emp_id, full_name FROM employees WHERE status='Active'")
        all_employees = cursor.fetchall()
        
        finalized_count = 0
        absent_count = 0
        leave_count = 0
        
        for emp in all_employees:
            emp_id = emp["emp_id"]
            
            # Check if attendance record exists for this date
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE emp_id=%s AND att_date=%s
            """, (emp_id, target_date))
            
            attendance_record = cursor.fetchone()
            
            # Check for any leave application (Approved, Rejected, or Pending)
            cursor.execute("""
                SELECT status FROM leave_applications
                WHERE emp_id=%s AND %s BETWEEN from_date AND to_date
                ORDER BY created_at DESC LIMIT 1
            """, (emp_id, target_date))
            
            leave_app = cursor.fetchone()
            leave_status = leave_app['status'] if leave_app else 'Not Applied'
            
            # Check specifically for approved leave
            cursor.execute("""
                SELECT id FROM leave_applications
                WHERE emp_id=%s AND status='Approved'
                AND %s BETWEEN from_date AND to_date
            """, (emp_id, target_date))
            
            has_approved_leave = cursor.fetchone()
            
            if attendance_record:
                # Attendance record exists
                if attendance_record.get("in_time"):
                    # Has entry - mark as present/late based on time
                    # Already handled by face recognition, just check missing exit
                    if not attendance_record.get("out_time"):
                        cursor.execute("""
                            UPDATE attendance 
                            SET missing_exit=1, updated_at=%s, leave_status=%s
                            WHERE emp_id=%s AND att_date=%s
                        """, (datetime.now(), leave_status, emp_id, target_date))
                        finalized_count += 1
                    if has_approved_leave:
                        # Update to LEAVE status
                        cursor.execute("""
                            UPDATE attendance 
                            SET status='Leave', leave_status=%s
                            WHERE emp_id=%s AND att_date=%s
                        """, (leave_status, emp_id, target_date))
                        leave_count += 1
                    else:
                        # Update to ABSENT status
                        cursor.execute("""
                            UPDATE attendance 
                            SET status='Absent', leave_status=%s
                            WHERE emp_id=%s AND att_date=%s
                        """, (leave_status, emp_id, target_date))
                        absent_count += 1
                    finalized_count += 1
            else:
                # No attendance record - create one
                if has_approved_leave:
                    # Create LEAVE record
                    cursor.execute("""
                        INSERT INTO attendance (emp_id, att_date, status, leave_status, source, created_at)
                        VALUES (%s, %s, 'Leave', %s, 'System', NOW())
                    """, (emp_id, target_date, leave_status))
                    leave_count += 1
                else:
                    # Create ABSENT record
                    cursor.execute("""
                        INSERT INTO attendance (emp_id, att_date, status, leave_status, source, created_at)
                        VALUES (%s, %s, 'Absent', %s, 'System', NOW())
                    """, (emp_id, target_date, leave_status))
                    absent_count += 1
                finalized_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Finalized attendance for {target_date}",
            "date": target_date_str,
            "total_finalized": finalized_count,
            "absent_marked": absent_count,
            "leave_marked": leave_count
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Admin Profile ───────────────────────────────────────────────────────────────────────
@app.route("/api/admin/profile", methods=["GET"])
def get_admin_profile():
    """Get admin profile information"""
    try:
        username = request.args.get("username")
        if not username:
            return jsonify({"success": False, "error": "Username parameter required"}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Query from admins table
        cursor.execute("""
            SELECT username, full_name, email, created_at, last_login_at
            FROM admins
            WHERE username=%s
        """, (username,))
        
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin:
            return jsonify({
                "success": True, 
                "profile": {
                    "emp_id": admin["username"],
                    "username": admin["username"],
                    "full_name": admin["full_name"],
                    "email": admin["email"],
                    "created_at": admin["created_at"].isoformat() if admin["created_at"] else None,
                    "last_login_at": admin["last_login_at"].isoformat() if admin["last_login_at"] else None
                }
            }), 200
        else:
            return jsonify({"success": False, "error": "Admin not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ── Initialize Scheduler ─────────────────────────────────────────────────────
def initialize_scheduler():
    """Initialize background scheduler for auto slot generation and lock"""
    try:
        scheduler = BackgroundScheduler()
        
        # NOTE: Do NOT generate slots at startup
        # Slots are generated ONLY by scheduler at 9:45 AM
        print("[SCHEDULER] Slots will be generated at 09:45 AM daily (not at startup)")
        
        # Auto slot generation at 09:45 AM every day
        scheduler.add_job(
            func=lambda: print(f"[SCHEDULER] Auto slot generation: {generate_daily_slots()}"),
            trigger='cron',
            hour=9,
            minute=45,
            id='auto_slot_generation'
        )
        
        # Auto lock pending at 07:15 PM every day - Final attendance status determination
        scheduler.add_job(
            func=lambda: print(f"[SCHEDULER] Auto lock pending: {auto_lock_pending()}"),
            trigger='cron',
            hour=19,
            minute=15,
            id='auto_lock_pending'
        )
        
        scheduler.start()
        print("[SCHEDULER] Background scheduler started")
        print("[SCHEDULER] Auto slot generation: At startup + 09:45 AM daily")
        print("[SCHEDULER] Auto lock pending: 07:15 PM daily")
        
        return scheduler
        
    except Exception as e:
        print(f"[SCHEDULER] Error starting scheduler: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting Face Recognition Attendance System...")
    
    # Clean up any duplicate attendance records on startup
    print("🧹 Cleaning up duplicate attendance records...")
    cleanup_result = cleanup_duplicate_attendance()
    
    # Update attendance status based on current scan times
    print("📊 Updating attendance status...")
    status_result = update_attendance_status()
    
    # Initialize enhanced attendance system with status automation
    initialize_enhanced_attendance(app)
    
    # The enhanced scheduler handles all slot generation and finalization
    # No need for the old scheduler
    
    print("✅ System ready! Starting server on port 5000...")
    app.run(debug=True, host='0.0.0.0', port=5000)
