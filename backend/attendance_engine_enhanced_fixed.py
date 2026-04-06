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

    def run_startup_catchup(self) -> dict:
        """
        Runs on system startup to handle any missed operations:
        1. Generates missing attendance records for ALL missed past days
           (not just yesterday — handles server being off for multiple days)
        2. Finalizes any PENDING records from past dates
        """
        today = datetime.now().date()
        results = {
            "slots": None,
            "finalized_dates": []
        }
        
        print(f"[CATCHUP] Starting system catch-up at {datetime.now()}")
        
        # 1. Generate missing slots for today and yesterday
        # This ensures if server was off yesterday, we get those slots
        try:
            results["slots"] = self.auto_generate_missing_records(today, include_yesterday=True)
            print(f"[CATCHUP] Slot generation: {results['slots'].get('records_created', 0)} created")
        except Exception as e:
            print(f"[CATCHUP] Slot generation error: {e}")
            results["slots_error"] = str(e)
        
        # 2. Finalize all past pending records
        # This handles cases where server was off at 7:15 PM on previous days
        try:
            cursor = self.db.cursor(dictionary=True)
            # Find all dates in the past that have PENDING records
            cursor.execute("""
                SELECT DISTINCT att_date FROM attendance 
                WHERE status = %s AND att_date < %s AND attendance_locked = 0
            """, (STATUS_PENDING, today))
            
            past_pending_dates = cursor.fetchall()
            cursor.close()
            
            if not past_pending_dates:
                print("[CATCHUP] No past PENDING records found to finalize")
            
            for row in past_pending_dates:
                past_date = row['att_date']
                print(f"[CATCHUP] Finalizing missed records for {past_date}")
                finalize_result = self.finalize_daily_attendance(past_date)
                results["finalized_dates"].append({
                    "date": past_date.strftime('%Y-%m-%d'),
                    "result": finalize_result
                })
                
        except Exception as e:
            print(f"[CATCHUP] Finalization error: {e}")
            results["finalization_error"] = str(e)
            
        print("[CATCHUP] System catch-up complete")
        return results

    def finalize_daily_attendance(self, target_date: date = None) -> dict:
        """
        AUTO LOCK PROCESS - Finalizes attendance records
        1. Find ALL pending records from past dates (not just target_date)
        2. Apply Decision Matrix:
           - Approved Leave + No Scan -> Leave
           - Not Applied/Rejected + No Scan -> Absent
           - Already has Scan -> Lock existing Present/Late status
        """
        today = datetime.now().date()
        
        # If target_date is not provided, we look back at ALL past unlocked dates
        # This fixes the issue where missed days stay "Pending" forever
        
        cursor = self.db.cursor(dictionary=True)
        try:
            # Step A: Find all dates before today that have unlocked attendance records
            query_dates = "SELECT DISTINCT att_date FROM attendance WHERE attendance_locked = 0 AND att_date < %s"
            cursor.execute(query_dates, (today,))
            unlocked_dates = [row['att_date'] for row in cursor.fetchall()]
            
            # If target_date is today and it's past 7:15 PM, add it too
            if target_date == today and datetime.now().time() >= FINALIZE_TIME:
                if today not in unlocked_dates:
                    unlocked_dates.append(today)
            elif target_date and target_date != today and target_date not in unlocked_dates:
                 unlocked_dates.append(target_date)

            print(f"[AUTO_LOCK] Found {len(unlocked_dates)} dates that need finalization: {unlocked_dates}")

            total_finalized_leave = 0
            total_finalized_absent = 0
            total_locked_scans = 0
            errors = []

            for process_date in unlocked_dates:
                print(f"[AUTO_LOCK] Finalizing records for {process_date}...")
                
                # 1. Process records WITHOUT scans (in_time is NULL)
                cursor.execute("""
                    SELECT emp_id FROM attendance 
                    WHERE att_date = %s AND attendance_locked = 0 AND in_time IS NULL
                """, (process_date,))
                
                unscanned = cursor.fetchall()
                for record in unscanned:
                    emp_id = record['emp_id']
                    
                    # Fetch detailed leave status
                    leave_status = self._get_detailed_leave_status(emp_id, process_date)
                    
                    if leave_status == 'Approved':
                        final_status = STATUS_LEAVE
                        total_finalized_leave += 1
                    else:
                        final_status = STATUS_ABSENT
                        total_finalized_absent += 1
                    
                    # Apply changes and LOCK
                    cursor.execute("""
                        UPDATE attendance 
                        SET status = %s, leave_status = %s, attendance_locked = 1, updated_at = NOW()
                        WHERE emp_id = %s AND att_date = %s
                    """, (final_status, leave_status, emp_id, process_date))
                
                # 2. Lock records WITH scans (they are already Present/Late)
                cursor.execute("""
                    UPDATE attendance 
                    SET attendance_locked = 1, updated_at = NOW()
                    WHERE att_date = %s AND attendance_locked = 0 AND in_time IS NOT NULL
                """, (process_date,))
                total_locked_scans += cursor.rowcount
                
                self.db.commit()

            print(f"[AUTO_LOCK] Done. Leave: {total_finalized_leave}, Absent: {total_finalized_absent}, Scanned: {total_locked_scans}")
            
            return {
                "success": True,
                "dates_processed": [str(d) for d in unlocked_dates],
                "marked_leave": total_finalized_leave,
                "marked_absent": total_finalized_absent,
                "locked_with_scans": total_locked_scans,
                "total_finalized": total_finalized_leave + total_finalized_absent + total_locked_scans,
                "errors": errors
            }
        except Exception as e:
            print(f"[AUTO_LOCK] ❌ Error: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
    
    def auto_generate_missing_records(self, target_date: date = None, include_yesterday: bool = True) -> dict:
        """
        Generates attendance slots for all active employees.
        Looks back up to 7 days to find any missed dates where slots weren't created.
        """
        today = datetime.now().date()
        now_time = datetime.now().time()
        if target_date is None:
            target_date = today
        
        cursor = self.db.cursor(dictionary=True)
        try:
            # Look back over the past 7 days to see if any date has 0 records
            # This handles cases where the server was offline for multiple days
            dates_to_process = []
            for i in range(7, -1, -1): # From 7 days ago to today
                dt = target_date - timedelta(days=i)
                
                # Logic: If checking Today, only process if it's past 9:45 AM
                # Older days are always backfilled immediately
                if dt == today and now_time < OFFICE_START:
                    continue
                    
                cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE att_date = %s", (dt,))
                if cursor.fetchone()['count'] == 0:
                    dates_to_process.append(dt)
            
            if not dates_to_process:
                print("[AUTOGEN] No missing dates found in the last 7 days.")
                return {"success": True, "records_created": 0}

            print(f"[AUTOGEN] Generating slots for missed dates: {dates_to_process}")
            total_generated = 0
            
            for process_date in dates_to_process:
                # Get all employees who joined on or before this date
                cursor.execute("""
                    SELECT emp_id FROM employees 
                    WHERE status = 'Active' AND (joining_date IS NULL OR joining_date <= %s)
                """, (process_date,))
                employees = cursor.fetchall()

                for emp in employees:
                    emp_id = emp['emp_id']
                    # Initial leave status check
                    cursor.execute("""
                        SELECT status FROM leave_applications
                        WHERE emp_id = %s AND %s BETWEEN from_date AND to_date
                        ORDER BY created_at DESC LIMIT 1
                    """, (emp_id, process_date))
                    leave_row = cursor.fetchone()
                    leave_status = leave_row['status'] if leave_row else 'Not Applied'

                    cursor.execute("""
                        INSERT IGNORE INTO attendance (emp_id, att_date, status, leave_status, source, created_at)
                        VALUES (%s, %s, 'Pending', %s, 'Auto-Generator', NOW())
                    """, (emp_id, process_date, leave_status))
                    total_generated += cursor.rowcount
            
            self.db.commit()
            return {
                "success": True,
                "dates_processed": [str(d) for d in dates_to_process],
                "records_created": total_generated
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
