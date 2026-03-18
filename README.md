# Face Recognition Attendance System

An AI-powered attendance management system using face recognition with InsightFace (ArcFace embeddings). Real-time employee attendance marking, leave management, and comprehensive admin dashboard.

## ✨ Features

- ✅ **Real-time Face Recognition** - InsightFace with ArcFace embeddings for accurate face matching
- ✅ **Automatic Attendance Marking** - Employees scan face to mark entry/exit
- ✅ **Smart Status Logic** - Before 11:00 AM = Present, After 11:00 AM = Late
- ✅ **Leave Management** - Apply, approve, reject leave requests
- ✅ **Admin Dashboard** - Real-time attendance overview and analytics
- ✅ **Employee Dashboard** - Personal attendance history and leave status
- ✅ **Fully Responsive Design** - Works on mobile, tablet, and desktop
- ✅ **Hybrid Attendance System** - Multiple entries/exits per day tracking
- ✅ **Automatic Slot Generation** - 9:45 AM daily slot creation for all employees
- ✅ **Attendance Finalization** - 7:15 PM automatic status finalization

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) |
| **Backend** | Python Flask |
| **Database** | MySQL |
| **Face Recognition** | InsightFace (ArcFace) with ONNX Runtime |
| **Scheduler** | APScheduler |
| **Server** | Flask Development Server |

## 📋 Project Structure

```
AI Enabled Face Recognition Attendance Management System/
├── backend/
│   ├── app.py                              # Main Flask application
│   ├── attendance_config.py                # Configuration & timing
│   ├── attendance_engine_enhanced_fixed.py # Attendance logic
│   ├── attendance_scheduler_enhanced.py    # Scheduler for auto-generation
│   ├── face_recognizer_insightface.py      # Face recognition engine
│   ├── attendance_migration.py             # Database migrations
│   ├── requirements.txt                    # Python dependencies
│   ├── README.md                           # Backend documentation
│   └── static/                             # Static files
├── faces/
│   ├── images/                             # Employee face photos for recognition
│   ├── uploads/                            # Uploaded employee photos
│   └── backup/                             # Backup photos
├── css/
│   ├── styles.css                          # Main styles
│   └── responsive.css                      # Responsive design (2000+ lines)
├── js/
│   ├── app.js                              # Core application logic
│   ├── pages.js                            # Page-specific logic
│   ├── auth.js                             # Authentication
│   ├── manage_employees.js                 # Employee management
│   └── responsive.js                       # Responsive behavior
├── components/
│   └── sidebar.html                        # Reusable sidebar component
├── database sql/
│   └── office_attendance.sql               # Complete database schema
├── *.html                                  # HTML pages (13 pages)
├── .gitignore                              # Git ignore rules
└── README.md                               # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- MySQL Server 5.7+
- Webcam/Camera (for face recognition)

### Step 1: Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 3: Setup Database
```bash
# Create database and tables
mysql -u root -p < "database sql/office_attendance.sql"
```

### Step 4: Configure Database Connection
Edit `backend/attendance_config.py`:
```python
DB_CFG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "office_attendance"
}
```

### Step 5: Run Application
```bash
python backend/app.py
```

### Step 6: Access Application
Open your browser and go to:
```
http://localhost:5000
```



## 📖 Getting Started Workflow

### 1. Login as Admin
```
URL: http://localhost:5000
Employee ID: drashti.616
Password: Mishti.4424
```

### 2. Register New Employees
1. Go to **Manage Employees** page
2. Click **Register Employee**
3. Fill in employee details:
   - Full Name
   - Email
   - Department
   - Joining Date
4. Capture employee face photo using camera
5. Click **Register Employee**
6. System generates:
   - Employee ID (emp001, emp002, etc.)
   - Temporary Password (displayed on screen)
7. **Copy and save** the credentials

### 3. Employee Changes Password
1. Employee logs in with temporary password
2. Goes to **Change Password** page
3. Enters new secure password
4. Password is updated

### 4. Employee Marks Attendance
1. Employee goes to **Face Recognition** page (index.html)
2. Allows camera access
3. Positions face in front of camera
4. System recognizes face and marks attendance
5. Status shows:
   - **Before 11:00 AM** → "Present"
   - **After 11:00 AM** → "Late"

### 5. Employee Applies for Leave
1. Employee goes to **Leave Application** page
2. Selects leave dates and type
3. Enters reason
4. Submits application
5. Status: "Pending" (waiting for admin approval)

### 6. Admin Approves/Rejects Leave
1. Admin goes to **Leave Applications** page
2. Views pending leave requests
3. Clicks **View Details**
4. Approves or Rejects
5. Employee receives status update

### 7. View Attendance Reports
**Employee View:**
- Goes to **Attendance History**
- Sees personal attendance records
- Can filter by date

**Admin View:**
- Goes to **Admin Dashboard**
- Sees real-time attendance overview
- Views all employee attendance
- Can export reports

### 8. Admin Views Leave History
1. Admin goes to **Leave Applications**
2. Filters by status (Pending, Approved, Rejected)
3. Views detailed leave information
4. Can approve/reject pending requests

## 📱 Pages Overview

| Page | Purpose | Access |
|------|---------|--------|
| `login.html` | User authentication | Public |
| `index.html` | Face recognition camera | Employee |
| `admin_dashboard.html` | Attendance overview | Admin |
| `employee_dashboard.html` | Personal attendance | Employee |
| `employee_attendance.html` | Attendance history | Employee |
| `admin_leaves.html` | Leave management | Admin |
| `employee_leave_history.html` | Leave history | Employee |
| `manage_employees.html` | Employee management | Admin |
| `register_employee.html` | Register new employee | Admin |
| `employee_profile.html` | Profile management | Employee |
| `change_password.html` | Password change | All |
| `leave_application.html` | Apply for leave | Employee |
| `attendance_report.html` | Attendance reports | Admin |

## ⏰ Attendance System Flow

### Daily Schedule
- **9:45 AM** - Scheduler automatically creates "Pending" slots for all active employees
- **9:45 AM - 11:00 AM** - Employees scan face → Status changes to "Present"
- **After 11:00 AM** - Employees scan face → Status changes to "Late"
- **7:15 PM** - Automatic finalization:
  - Pending → Absent (if no scan)
  - Pending → Present/Late (if scanned)
  - Leave → Leave (if approved leave)

### Status Logic
```
Before 11:00 AM + Face Scan = Present
After 11:00 AM + Face Scan = Late
No Scan by 7:15 PM = Absent
Approved Leave = Leave
```

## 🎯 Key Features Explained

### Face Recognition
- Uses InsightFace with ArcFace embeddings
- Automatic face detection and alignment
- Confidence-based matching (threshold: 0.5)
- 10-minute scan cooldown to prevent duplicates

### Responsive Design
- Mobile-first approach
- 6 breakpoints: 480px, 576px, 768px, 992px, 1200px, 1400px
- Touch-friendly buttons (44px minimum)
- Horizontal scroll for tables on mobile
- Flexible layouts using Flexbox and CSS Grid

### Leave Management
- Employees apply for leave with reason
- Admin approves/rejects requests
- Automatic leave status tracking
- Leave overrides attendance if approved

### Admin Dashboard
- Real-time attendance statistics
- KPI cards (Total, Present, Late, Absent, Leave)
- Detailed attendance table with entry/exit times
- Expandable rows showing scan logs
- Filter by employee ID or name

## 🔧 Configuration

### Timing Configuration (`backend/attendance_config.py`)
```python
OFFICE_START = time(9, 45, 0)              # 9:45 AM - Slot generation
LATE_TIME = time(11, 0, 0)                 # 11:00 AM - Late threshold
FINALIZE_TIME = time(19, 15, 0)            # 7:15 PM - Finalization
ATTENDANCE_MARKING_START = time(10, 0, 0)  # 10:00 AM - Marking window opens
ATTENDANCE_MARKING_END = time(19, 15, 0)   # 7:15 PM - Marking window closes
```

### Database Configuration
Edit `backend/attendance_config.py`:
```python
DB_CFG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "office_attendance"
}
```

## 🐛 Troubleshooting

### Face Recognition Not Working
- ✅ Ensure camera is connected and working
- ✅ Check lighting conditions (good lighting required)
- ✅ Verify face is clearly visible
- ✅ Check InsightFace models are downloaded (~500MB)
- ✅ Ensure employee face photo is registered

### Database Connection Error
```
Error: Can't connect to MySQL server
```
**Solution:**
- Verify MySQL is running
- Check credentials in `attendance_config.py`
- Ensure database `office_attendance` exists
- Run: `mysql -u root -p < "database sql/office_attendance.sql"`

### Port Already in Use
```
Error: Address already in use
```
**Solution:**
- Change port in `backend/app.py`:
  ```python
  app.run(host='0.0.0.0', port=5000)
  ```

### Camera Permission Denied
- Allow camera access in browser settings
- Use HTTPS or localhost
- Check browser console for errors

### Attendance Not Marking
- Verify current time is within marking window (10:00 AM - 7:15 PM)
- Check employee status is "Active"
- Verify face recognition confidence is above threshold
- Check database for errors in logs

## 📊 API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Attendance
- `GET /api/attendance/today` - Today's attendance with auto-slot generation
- `GET /api/attendance?date=YYYY-MM-DD` - Attendance for specific date
- `POST /api/attendance/recognize` - Face recognition and marking
- `GET /api/attendance/logs` - Attendance logs

### Employees
- `GET /api/employees` - List all employees
- `POST /api/employees` - Register new employee
- `GET /api/employees/{emp_id}` - Get employee details
- `DELETE /api/employees/{emp_id}` - Delete employee

### Leaves
- `GET /api/leaves` - List all leave requests
- `POST /api/leaves` - Apply for leave
- `PUT /api/leaves/{leave_id}` - Approve/reject leave

## 🎨 Responsive Design Details

### Breakpoints
- **Mobile** (< 576px) - Single column, stacked layout
- **Small Tablet** (576px - 767px) - 2 columns
- **Tablet** (768px - 991px) - 3 columns
- **Laptop** (992px - 1199px) - 4 columns
- **Desktop** (1200px - 1399px) - Full width
- **Large Desktop** (≥ 1400px) - Max-width container

### Mobile Optimizations
- Touch-friendly buttons (44px minimum)
- Horizontal scroll for tables
- Collapsible sidebar navigation
- Responsive forms (single column on mobile)
- Optimized font sizes for readability

## 📝 Database Schema

Key tables:
- `employees` - Employee information
- `attendance` - Daily attendance records
- `attendance_logs` - Detailed scan logs (entry/exit)
- `leave_applications` - Leave requests
- `admins` - Admin accounts

See `database sql/office_attendance.sql` for complete schema.

## 🔐 Security Features

- Password hashing with bcrypt
- Session-based authentication
- CORS enabled for API
- Input validation on all forms
- SQL injection prevention with parameterized queries
- Face recognition confidence threshold

## 📈 Performance Optimizations

- Lazy loading of images
- Efficient database queries with indexing
- CSS Grid and Flexbox for layout
- Minimal JavaScript dependencies
- Responsive images and media queries
- Caching of face embeddings

## 🚀 Future Enhancements

- [ ] Mobile app (React Native/Flutter)
- [ ] Email notifications for leave status
- [ ] Advanced analytics and reports
- [ ] Multi-location support
- [ ] Biometric integration (fingerprint)
- [ ] Real-time notifications
- [ ] Export to Excel/PDF
- [ ] Dark mode
- [ ] Two-factor authentication

## 📄 License

MIT License - Feel free to use this project for personal or commercial purposes.

## 👨‍💻 Author

**Drashti Rathod**
- Email: drashtir.616@gmail.com
- GitHub: [@drashti616](https://github.com/drashti616)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues, questions, or suggestions:
1. Check existing issues on GitHub
2. Create a new issue with detailed description
3. Include error messages and screenshots

## 🙏 Acknowledgments

- InsightFace for face recognition models
- Flask for web framework
- APScheduler for task scheduling
- MySQL for database

---

**Last Updated**: March 2026
**Version**: 1.0.0
