"""
Enhanced Attendance Engine - Daily Status Automation
Implements attendance status rules with pending → final status transitions
"""
from datetime import datetime, date, time as dt_time, timedelta
from mysql.connector import Error
from attendance_config import (
    OFFICE_START, LATE_TIME, FINALIZE_TIME,
    STATUS_PRESENT, STATUS_LATE, STATUS_LEAVE, STATUS_ABSENT, STATUS_PENDING,
    LOG_ENTRY, LOG_EXIT, DB_CFG
)
import mysql.connector

class EnhancedAttendanceEngine:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_db_connection(self):
        """Get fresh database connection"""
        return mysql.connector.connect(**DB_CFG)
    
    def _create_attendance_record_if_missing(self, emp_id: str, target_date: date, status: str, source: str = 'System') -> bool:
        """Create attendance record if it doesn't exist, or update if exists"""
        try:
            cursor = self.db.cursor()
            # First check if record exists
            cursor.execute("""
                SELECT status FROM attendance 
                WHERE emp_id = %s AND att_date = %s
            """, (emp_id, target_date))
            
            result = cursor.fetchone()
            
            if result is None:
                # Record doesn't exist, create it
                cursor.execute("""
                    INSERT INTO attendance (emp_id, att_date, status, source, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (emp_id, target_date, status, source))
                self.db.commit()
                cursor.close()
                print(f"[ENHANCED] Created new {status} record for {emp_id} on {target_date}")
                return True
            else:
                # Record exists, only update if status is different
                existing_status = result[0]
                if existing_status != status:
                    cursor.execute("""
                        UPDATE attendance 
                        SET status = %s, source = %s
                        WHERE emp_id = %s AND att_date = %s
                    """, (status, source, emp_id, target_date))
                    self.db.commit()
                    cursor.close()
                    print(f"[ENHANCED] Updated {emp_id} status from {existing_status} to {status} on {target_date}")
                    return True
                else:
                    cursor.close()
                    print(f"[ENHANCED] Record for {emp_id} already has {status} status on {target_date}")
                    return False
        except Error as e:
            print(f"[ENHANCED] Error creating/updating attendance record for {emp_id}: {e}")
            return False
    
    def _update_attendance_status(self, emp_id: str, target_date: date, new_status: str) -> bool:
        """Update attendance status"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE attendance 
                SET status = %s
                WHERE emp_id = %s AND att_date = %s
            """, (new_status, emp_id, target_date))
            self.db.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"[ENHANCED] Error updating status for {emp_id}: {e}")
            return False
    
    def _has_attendance_today(self, emp_id: str, target_date: date) -> bool:
        """Check if employee has attendance logs for target_date"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM attendance_logs 
                WHERE emp_id = %s AND DATE(att_date) = %s
            """, (emp_id, target_date))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
        except Error as e:
            print(f"[ENHANCED] Error checking attendance for {emp_id}: {e}")
            return False
    
    def _get_approved_leave(self, emp_id: str, target_date: date) -> bool:
        """Check if employee has approved leave for target_date"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM leave_applications 
                WHERE emp_id = %s 
                AND %s BETWEEN from_date AND to_date 
                AND status = 'Approved'
            """, (emp_id, target_date))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
        except Error as e:
            print(f"[ENHANCED] Error checking leave for {emp_id}: {e}")
            return False
    
    def _get_detailed_leave_status(self, emp_id: str, target_date: date) -> str:
        """Helper to get text status of leave application: Approved, Rejected, or Not Applied"""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute("""
                SELECT status FROM leave_applications 
                WHERE emp_id = %s 
                AND %s BETWEEN from_date AND to_date 
                ORDER BY created_at DESC LIMIT 1
            """, (emp_id, target_date))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return result['status'] # 'Approved', 'Rejected', etc.
            return 'Not Applied'
        except Error as e:
            print(f"[ENHANCED] Error getting detailed leave for {emp_id}: {e}")
            return 'Not Applied'

    def process_daily_attendance_status(self, target_date: date = None) -> dict:
        """
        DAILY SLOT GENERATION at 09:45 AM
        1. Select all employees where status = 'Active' (Step 1)
        2. Insert Attendance Record for each (Step 2)
           - status = 'Pending'
           - attendance_locked = 0
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        cursor = self.db.cursor(dictionary=True)
        
        try:
            # Step 1: Fetch All Active Employees (joined on or before target date)
            cursor.execute("""
                SELECT emp_id, full_name 
                FROM employees 
                WHERE status = 'Active' 
                AND (joining_date IS NULL OR joining_date <= %s)
            """, (target_date,))
            all_employees = cursor.fetchall()
            cursor.close()
            
            pending_count = 0
            processed_count = 0
            errors = []
            
            print(f"[DAILY_SLOTS] Generating slots for {target_date}...")
            
            for employee in all_employees:
                emp_id = employee['emp_id']
                
                try:
                    # Step 2: Insert Attendance Record (Initialize as Pending and Unlocked)
                    # Every employee MUST start as Pending
                    # No one should be marked Absent during slot generation
                    cursor = self.db.cursor()
                    cursor.execute("""
                        INSERT INTO attendance (emp_id, att_date, status, attendance_locked, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        ON DUPLICATE KEY UPDATE 
                        status = IF(attendance_locked = 0, %s, status)
                    """, (emp_id, target_date, STATUS_PENDING, 0, STATUS_PENDING))
                    self.db.commit()
                    cursor.close()
                    
                    pending_count += 1
                    processed_count += 1
                except Exception as e:
                    errors.append(f"{emp_id}: {str(e)}")
            
            return {
                "success": True,
                "date": target_date.strftime('%Y-%m-%d'),
                "total_employees": len(all_employees),
                "slots_generated": processed_count,
                "status": "Pending",
                "errors": errors
            }
        except Exception as e:
            print(f"[DAILY_SLOTS] Error: {e}")
            return {"success": False, "error": str(e)}

    def finalize_daily_attendance(self, target_date: date = None) -> dict:
        """
        AUTO LOCK PROCESS at 7:15 PM
        Rule Case Matrix:
        - Approved + No Scan -> Leave
        - Rejected + No Scan -> Absent
        - Not Applied + No Scan -> Absent
        - Any + Scan Done -> Present/Late (already set)
        Sets attendance_locked = 1
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        cursor = self.db.cursor(dictionary=True)
        
        try:
            # Select Employees where no scan (in_time IS NULL) and not locked
            cursor.execute("""
                SELECT emp_id, status, leave_status FROM attendance 
                WHERE att_date = %s 
                AND attendance_locked = 0
                AND in_time IS NULL
            """, (target_date,))
            
            unlocked_records = cursor.fetchall()
            cursor.close()
            
            finalized_leave = 0
            finalized_absent = 0
            errors = []
            
            print(f"[AUTO_LOCK] 🔍 Processing {len(unlocked_records)} unlocked/no-scan records for {target_date}")
            
            for record in unlocked_records:
                emp_id = record['emp_id']
                current_status = record['status']
                current_leave_status = record['leave_status']
                
                print(f"[AUTO_LOCK] Processing {emp_id}: current_status={current_status}, leave_status={current_leave_status}")
                
                try:
                    # Get the actual leave status from leave_applications table
                    leave_status = self._get_detailed_leave_status(emp_id, target_date)
                    print(f"[AUTO_LOCK]   {emp_id}: Fetched leave_status from DB = {leave_status}")
                    
                    # FINAL RULES (Matrix)
                    if leave_status == 'Approved':
                        # Approved leave + no scan -> Leave
                        final_status = STATUS_LEAVE
                        finalized_leave += 1
                        print(f"[AUTO_LOCK]   {emp_id}: ✅ Setting to LEAVE (approved leave, no scan)")
                    else:
                        # Not Applied/Rejected + no scan -> Absent
                        final_status = STATUS_ABSENT
                        finalized_absent += 1
                        print(f"[AUTO_LOCK]   {emp_id}: ✅ Setting to ABSENT ({leave_status}, no scan)")
                    
                    # Step 3: Lock Attendance
                    cursor = self.db.cursor()
                    cursor.execute("""
                        UPDATE attendance 
                        SET status = %s, attendance_locked = 1, updated_at = NOW()
                        WHERE emp_id = %s AND att_date = %s
                    """, (final_status, emp_id, target_date))
                    self.db.commit()
                    cursor.close()
                    print(f"[AUTO_LOCK]   {emp_id}: ✅ Updated in database")
                    
                except Exception as e:
                    error_msg = f"{emp_id}: {str(e)}"
                    errors.append(error_msg)
                    print(f"[AUTO_LOCK]   ❌ Error: {error_msg}")
            
            # Also lock records that ALREADY have scans (they were already set to Present/Late during scan)
            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE attendance 
                SET attendance_locked = 1, updated_at = NOW()
                WHERE att_date = %s AND attendance_locked = 0 AND in_time IS NOT NULL
            """, (target_date,))
            locked_with_scans = cursor.rowcount
            self.db.commit()
            cursor.close()
            print(f"[AUTO_LOCK] 🔒 Locked {locked_with_scans} records with scans")
            
            total_finalized = finalized_leave + finalized_absent + locked_with_scans
            print(f"[AUTO_LOCK] ✅ Finalization complete for {target_date}:")
            print(f"[AUTO_LOCK]   - Marked LEAVE: {finalized_leave}")
            print(f"[AUTO_LOCK]   - Marked ABSENT: {finalized_absent}")
            print(f"[AUTO_LOCK]   - Locked with scans: {locked_with_scans}")
            print(f"[AUTO_LOCK]   - Total finalized: {total_finalized}")
            
            return {
                "success": True,
                "date": target_date.strftime('%Y-%m-%d'),
                "marked_leave": finalized_leave,
                "marked_absent": finalized_absent,
                "locked_with_scans": locked_with_scans,
                "total_finalized": total_finalized,
                "errors": errors
            }
        except Exception as e:
            print(f"[AUTO_LOCK] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def auto_generate_missing_records(self, target_date: date = None, include_yesterday: bool = True) -> dict:
        """
        Auto-generate attendance records for employees who never scanned
        SAFE GENERATION: Checks if records already exist for the date before creating
        Only generates records for dates on or after employee's joining date
        Uses database-level checks to prevent regeneration on server restart
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        cursor = self.db.cursor(dictionary=True)
        
        try:
            dates_to_process = [target_date]
            if include_yesterday:
                yesterday = target_date - timedelta(days=1)
                dates_to_process.append(yesterday)
            
            total_generated = 0
            errors = []
            
            for process_date in dates_to_process:
                print(f"[AUTOGEN] Processing missing records for {process_date}")

                # Get all active employees who have joined on or before this date
                cursor.execute("""
                    SELECT e.emp_id, e.full_name, e.joining_date
                    FROM employees e
                    WHERE e.status = 'Active'
                        AND (e.joining_date IS NULL OR e.joining_date <= %s)
                """, (process_date,))

                all_employees = cursor.fetchall()
                print(f"[AUTOGEN] Found {len(all_employees)} active employees for {process_date}")

                for employee in all_employees:
                    emp_id = employee['emp_id']

                    try:
                        # FIX: Check PER EMPLOYEE instead of skipping the whole date.
                        # This prevents an existing record for one employee from blocking
                        # slot creation for all others (e.g. on server restart).
                        cursor.execute("""
                            SELECT COUNT(*) as count FROM attendance
                            WHERE emp_id = %s AND att_date = %s
                        """, (emp_id, process_date))
                        already_exists = cursor.fetchone()['count'] > 0

                        if already_exists:
                            print(f"[AUTOGEN] Skipping {emp_id} on {process_date} - record already exists")
                            continue

                        # Check for leave application for this employee on this date
                        cursor.execute("""
                            SELECT status FROM leave_applications
                            WHERE emp_id = %s AND %s BETWEEN from_date AND to_date
                            ORDER BY created_at DESC LIMIT 1
                        """, (emp_id, process_date))

                        leave_app = cursor.fetchone()
                        leave_status = leave_app['status'] if leave_app else 'Not Applied'
                        
                        # Status is PENDING for all new slots (will be finalized at 7:15 PM)
                        status = STATUS_PENDING

                        # Create attendance record with appropriate leave_status
                        cursor.execute("""
                            INSERT INTO attendance (emp_id, att_date, status, leave_status, source, created_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """, (emp_id, process_date, status, leave_status, 'Auto-Generator'))

                        total_generated += 1
                        print(f"[AUTOGEN] Created {status} record for {emp_id} on {process_date} with leave_status={leave_status}")

                    except Exception as e:
                        errors.append(f"{emp_id}: {str(e)}")
                        print(f"[AUTOGEN] Error generating record for {emp_id}: {e}")

                # Commit after processing all employees for this date
                self.db.commit()
            
            return {
                "success": True,
                "dates_processed": dates_to_process,
                "records_created": total_generated,
                "records_skipped": sum(len(all_employees) - total_generated for _ in dates_to_process),
                "errors": errors
            }
            
        except Exception as e:
            print(f"[AUTOGEN] Auto-generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "dates_processed": dates_to_process
            }
        finally:
            cursor.close()
