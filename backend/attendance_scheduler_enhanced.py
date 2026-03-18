"""
Enhanced Attendance Scheduler - Daily Status Automation
Implements the complete attendance status automation system
Runs daily processing and 19:00 finalization
"""
import threading
import time
from datetime import datetime, time as dt_time
from attendance_engine_enhanced_fixed import EnhancedAttendanceEngine
from attendance_config import FINALIZE_TIME, DB_CFG
import mysql.connector

class EnhancedAttendanceScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the enhanced attendance scheduler"""
        if self.running:
            print("[ENHANCED_SCHEDULER] Already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print(f"[ENHANCED_SCHEDULER] Started - Daily processing at 9:45 AM, finalization at {FINALIZE_TIME} daily")
    
    def stop(self):
        """Stop the enhanced attendance scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("[ENHANCED_SCHEDULER] Stopped")
    
    def _run_scheduler(self):
        """Main enhanced scheduler loop"""
        from attendance_config import OFFICE_START
        
        last_slot_generation_run = None
        last_finalization_run = None
        slot_generation_attempted_today = False
        finalization_attempted_today = False
        
        while self.running:
            now = datetime.now()
            current_date = now.date()
            current_time = now.time()
            
            # SLOT GENERATION at 9:45 AM
            # Run if it's past OFFICE_START and hasn't run today
            should_generate_slots = (
                current_date != last_slot_generation_run and 
                current_time >= OFFICE_START and
                not slot_generation_attempted_today
            )
            
            if should_generate_slots:
                print(f"[ENHANCED_SCHEDULER] ⏰ Time is {current_time}, OFFICE_START is {OFFICE_START}")
                print(f"[ENHANCED_SCHEDULER] 📋 Generating daily attendance slots for {current_date}")
                
                try:
                    conn = mysql.connector.connect(**DB_CFG)
                    engine = EnhancedAttendanceEngine(conn)
                    
                    # Generate pending slots for all active employees
                    slot_result = engine.auto_generate_missing_records(current_date, include_yesterday=False)
                    
                    conn.close()
                    
                    print(f"[ENHANCED_SCHEDULER] ✅ Slot generation complete:")
                    print(f"  - Records created: {slot_result.get('records_created', 0)}")
                    print(f"  - Records skipped: {slot_result.get('records_skipped', 0)}")
                    
                    last_slot_generation_run = current_date
                    slot_generation_attempted_today = True
                    
                except Exception as e:
                    print(f"[ENHANCED_SCHEDULER] ❌ Slot generation error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Final status evaluation (Scheduled for 7:15 PM / FINALIZE_TIME)
            # Run if it's past FINALIZE_TIME and hasn't run today
            finalization_time = FINALIZE_TIME
            
            # Check if we should run finalization
            should_finalize = (
                current_date != last_finalization_run and 
                current_time >= finalization_time and
                not finalization_attempted_today
            )
            
            if should_finalize:
                print(f"[ENHANCED_SCHEDULER] ⏰ Time is {current_time}, FINALIZE_TIME is {finalization_time}")
                print(f"[ENHANCED_SCHEDULER] 🔒 Finalizing attendance status for {current_date}")
                
                try:
                    conn = mysql.connector.connect(**DB_CFG)
                    engine = EnhancedAttendanceEngine(conn)
                    
                    # Finalize all pending statuses to final statuses
                    final_result = engine.finalize_daily_attendance(current_date)
                    
                    conn.close()
                    
                    print(f"[ENHANCED_SCHEDULER] ✅ Finalization complete:")
                    print(f"  - Total finalized: {final_result.get('total_finalized', 0)}")
                    print(f"  - Marked Present/Leave: {final_result.get('marked_present', 0)}")
                    print(f"  - Marked Absent: {final_result.get('marked_absent', 0)}")
                    
                    last_finalization_run = current_date
                    finalization_attempted_today = True
                    
                except Exception as e:
                    print(f"[ENHANCED_SCHEDULER] ❌ Finalization error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Reset flags at midnight
            if current_time < dt_time(0, 1, 0):  # Between midnight and 00:01
                slot_generation_attempted_today = False
                finalization_attempted_today = False
            
            # Sleep for 30 seconds
            time.sleep(30)

# Global enhanced scheduler instance
_enhanced_scheduler = None

def start_enhanced_attendance_scheduler():
    """Start the global enhanced attendance scheduler"""
    global _enhanced_scheduler
    if _enhanced_scheduler is None:
        _enhanced_scheduler = EnhancedAttendanceScheduler()
    _enhanced_scheduler.start()
    return _enhanced_scheduler

def stop_enhanced_attendance_scheduler():
    """Stop the global enhanced attendance scheduler"""
    global _enhanced_scheduler
    if _enhanced_scheduler:
        _enhanced_scheduler.stop()
        _enhanced_scheduler = None
