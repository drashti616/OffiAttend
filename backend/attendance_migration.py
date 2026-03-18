"""
Database migration for hybrid attendance system
"""
import mysql.connector
from attendance_config import DB_CFG


def create_attendance_tables():
    """
    Check if attendance tables exist and add any missing columns.
    Safe to run on every startup — uses IF NOT EXISTS and duplicate-column guards.
    Does NOT add a 'reason' column — it is not needed.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CFG)
        cursor = conn.cursor()

        print("[MIGRATION] Checking attendance tables...")

        # ── attendance table ────────────────────────────────────────────────────
        cursor.execute("SHOW TABLES LIKE 'attendance'")
        attendance_exists = cursor.fetchone()

        if attendance_exists:
            print("[MIGRATION] ✓ attendance table exists")
            cursor.execute("DESCRIBE attendance")
            columns = cursor.fetchall()
            column_names = [col[0] for col in columns]

            # Add attendance_locked if missing
            if 'attendance_locked' not in column_names:
                print("[MIGRATION] Adding attendance_locked column...")
                cursor.execute(
                    "ALTER TABLE attendance ADD COLUMN attendance_locked TINYINT(1) DEFAULT 0"
                )
                conn.commit()
                print("[MIGRATION] attendance_locked column added")
            else:
                print("[MIGRATION] ✓ attendance_locked column already exists")
        else:
            print("[MIGRATION] ✗ attendance table missing — run init_db.py first")

        # ── attendance_logs table ───────────────────────────────────────────────
        # Lean schema: only columns that are actually used.
        # 'reason' is intentionally excluded.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                emp_id      VARCHAR(30)  NOT NULL,
                att_date    DATETIME     NOT NULL,
                action      VARCHAR(10)  NOT NULL  COMMENT 'ENTRY or EXIT',
                scan_method VARCHAR(20)  DEFAULT 'face_recognition',
                created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                KEY idx_log_emp_date (emp_id),
                KEY idx_log_datetime (att_date)
            )
        """)
        conn.commit()
        print("[MIGRATION] ✓ attendance_logs table verified/created")

        # Ensure scan_method exists on older tables
        cursor.execute("DESCRIBE attendance_logs")
        log_columns = [col[0] for col in cursor.fetchall()]

        def _safe_add(col_def):
            try:
                cursor.execute(f"ALTER TABLE attendance_logs ADD COLUMN {col_def}")
                conn.commit()
                print(f"[MIGRATION] Added column to attendance_logs: {col_def.split()[0]}")
            except mysql.connector.Error as e:
                if e.errno == 1060:  # 1060 = duplicate column, already exists
                    pass
                else:
                    raise

        if 'scan_method' not in log_columns:
            _safe_add("scan_method VARCHAR(20) DEFAULT 'face_recognition'")
        else:
            print("[MIGRATION] ✓ attendance_logs.scan_method exists")

        print("[MIGRATION] Migration check completed successfully")

    except Exception as e:
        print(f"[MIGRATION] Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_attendance_tables()
