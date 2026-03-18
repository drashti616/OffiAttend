"""
Attendance Configuration - Centralized timing and settings
"""
from datetime import time

# Office timing configuration
OFFICE_START = time(9, 45, 0)  # 9:45 AM
LATE_TIME = time(11, 0, 0)    # 11:00 AM  
FINALIZE_TIME = time(19, 15, 0) # 7:15 PM
ATTENDANCE_MARKING_START = time(10, 0, 0)  # 10:00 AM - Attendance marking window opens
ATTENDANCE_MARKING_END = time(19, 15, 0)   # 7:15 PM - Attendance marking window closes

# Attendance status constants
STATUS_PRESENT = "Present"
STATUS_LATE = "Late"
STATUS_LEAVE = "Leave"
STATUS_ABSENT = "Absent"
STATUS_PENDING = "Pending"

DB_CFG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "office_attendance"
}

# Log types
LOG_ENTRY = "ENTRY"
LOG_EXIT = "EXIT"

# Database table names
TABLE_ATTENDANCE_LOGS = "attendance_logs"
TABLE_ATTENDANCE = "attendance"

# Database configuration
DB_CFG = dict(host="localhost", port=3306, user="root", password="", database="office_attendance")

