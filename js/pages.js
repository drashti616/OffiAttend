/* Page-specific behavior (frontend-only demo) */

function renderNav() {
  const container = document.querySelector("[data-nav-role-links]");
  const brandLink = document.querySelector("[data-brand-link]");
  const profileLink = document.querySelector("[data-profile-link]");
  if (!container) return;
  const user = window.OfficeApp && window.OfficeApp.currentUser();
  const isAdmin = (user && (user.role || "").toLowerCase()) === "admin";
  const currentPage = (window.location.pathname || "").split("/").pop() || window.location.href;

  if (brandLink) brandLink.href = isAdmin ? "admin_dashboard.html" : "employee_dashboard.html";
  if (profileLink) profileLink.href = isAdmin ? "admin_profile.html" : "employee_profile.html";

  const navItem = (href, label, icon) => {
    const active = currentPage === href ? " active" : "";
    return `<a class="nav-item${active}" href="${href}">${icon}<span>${label}</span></a>`;
  };
  const iconDashboard = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>';
  const iconUsers = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>';
  const iconClipboard = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>';
  const iconCalendar = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>';
  const iconUserPlus = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>';
  const iconHybrid = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path><polyline points="9 11 12 14 16 10"></polyline></svg>';

  let html = "";
  if (isAdmin) {
    html += navItem("admin_dashboard.html", "Dashboard", iconDashboard);
    html += navItem("register_employee.html", "Register Employee", iconUserPlus);
    html += navItem("manage_employees.html", "Employees", iconUsers);
    html += navItem("attendance_report.html", "Attendance Report", iconClipboard);
    html += navItem("admin_leaves.html", "Leave Management", iconCalendar);
  } else {
    html += navItem("employee_dashboard.html", "Dashboard", iconDashboard);
    html += navItem("leave_application.html", "Apply Leave", iconCalendar);
    html += navItem("employee_leave_history.html", "Leave History", iconCalendar);
    html += navItem("employee_attendance.html", "Attendance", iconClipboard);
  }
  container.innerHTML = html;
}

document.addEventListener("DOMContentLoaded", () => {
  if (!window.OfficeApp) return;

  const legacyLogoutBtn = document.querySelector("[data-logout]");
  if (legacyLogoutBtn) legacyLogoutBtn.addEventListener("click", () => OfficeApp.logout());

  OfficeApp.setNavbarUser();
  window.OfficeApp.renderNav = renderNav;
  if (document.querySelector("[data-nav-role-links]")) renderNav();

  // Guard pages that request auth – must be logged in to see any panel
  if (document.body.dataset.requiresAuth === "true") {
    const user = OfficeApp.requireAuth();
    if (!user) return;

    const isAdmin = (user.role || "").toLowerCase() === "admin";
    const href = window.location.href || "";
    // Send admin to admin panel if they opened an employee-only page (not report)
    if (isAdmin && href.includes("employee_dashboard.html")) {
      window.location.replace("admin_dashboard.html");
      return;
    }
    if (isAdmin && href.includes("employee_profile.html")) {
      window.location.replace("admin_dashboard.html");
      return;
    }
    // Send employee to employee panel if they opened an admin-only page
    if (!isAdmin && (href.includes("admin_dashboard.html") || href.includes("admin_profile.html") || href.includes("manage_employees.html") || href.includes("admin_leaves.html") || href.includes("register_employee.html") || href.includes("edit_employee.html"))) {
      window.location.replace("employee_dashboard.html");
      return;
    }

    // Hide admin-only UI blocks for non-admin
    const adminOnly = document.querySelectorAll("[data-admin-only]");
    if (!isAdmin) {
      adminOnly.forEach(el => (el.style.display = "none"));
    }

  }

  // Home buttons
  const btnRegister = document.querySelector("[data-go-register]");
  if (btnRegister) btnRegister.addEventListener("click", () => (window.location.href = "register_employee.html"));

  // Attendance Camera: automatic face recognition - no manual selection
  const video = document.querySelector("video[data-camera]");
  const captureInBtn = document.querySelector("[data-capture-in]");
  const captureOutBtn = document.querySelector("[data-capture-out]");
  const statusEl = document.querySelector("[data-status]");

  if (video && (captureInBtn || captureOutBtn)) {
    let stream = null;
    const startCam = async () => {
      try {
        if (statusEl) statusEl.innerHTML = `<span class="badge badge-warning">Requesting camera permission...</span>`;

        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          },
          audio: false
        });

        video.srcObject = stream;
        await video.play();

        if (statusEl) statusEl.innerHTML = `<span class="badge badge-present">Camera ready - Position your face in the frame</span>`;

        // Enable capture buttons
        if (captureInBtn) captureInBtn.disabled = false;
        if (captureOutBtn) captureOutBtn.disabled = false;

      } catch (e) {
        console.error('Camera error:', e);
        let message = 'Camera access failed';
        let instruction = 'Please allow camera access';

        if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
          message = 'Camera permission denied';
          instruction = 'Click 📷 icon in address bar and allow camera access';
        } else if (e.name === 'NotFoundError') {
          message = 'No camera found';
          instruction = 'Please connect a camera';
        } else if (e.name === 'NotReadableError') {
          message = 'Camera already in use';
          instruction = 'Close other apps using camera';
        }

        if (statusEl) {
          statusEl.innerHTML = `<span class="badge badge-absent">${message}</span><br><small>${instruction}. Refresh page after fixing.</small>`;
        }

        // Keep buttons disabled
        if (captureInBtn) captureInBtn.disabled = true;
        if (captureOutBtn) captureOutBtn.disabled = true;
      }
    };
    startCam();

    const captureFrame = () => {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      return canvas.toDataURL('image/jpeg', 0.85);
    };

    const doMark = async (action) => {
      if (statusEl) statusEl.innerHTML = `<span class="badge badge-warning">Recognizing face...</span>`;

      // Disable buttons during processing
      if (captureInBtn) captureInBtn.disabled = true;
      if (captureOutBtn) captureOutBtn.disabled = true;

      try {
        const imageData = captureFrame();

        // Use the correct face recognition API endpoint
        const res = await fetch(`${OfficeApp.API_BASE_URL}/attendance/recognize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: imageData })
        });

        const data = await res.json();

        if (data.success) {
          if (statusEl) {
            // Display the message from backend with employee ID and time
            const message = (data.message || `✅ Successfully marked attendance`).replace(/\n/g, '<br>');
            statusEl.innerHTML = `<span class="badge badge-present">${message}</span>`;
            console.log('✅ Attendance Success:', data.message);
            console.log('📊 Confidence:', data.confidence);
          }
        } else {
          if (statusEl) {
            let badge = 'Absent';
            let message = (data.error || 'Attendance failed').replace(/\n/g, '<br>');

            // Handle specific security validation messages
            if (data.error === 'Entry already recorded. Please scan EXIT first.') {
              badge = 'Present';
              message = '⚠️ Entry already recorded. Please scan EXIT to complete your attendance.';
            } else if (data.error === 'Scan ENTRY first') {
              badge = 'Absent';
              message = '❌ EXIT scan requires same-day ENTRY. Please scan ENTRY first.';
            }

            statusEl.innerHTML = `<span class="badge badge-${badge.toLowerCase()}">${message}</span>`;
            console.log('⚠️ Attendance Error:', message);
          }
        }

      } catch (e) {
        console.error('Attendance error:', e);
        if (statusEl) statusEl.innerHTML = `<span class="badge badge-absent">❌ Connection error. Ensure backend is running.</span>`;
      } finally {
        // Re-enable buttons after processing
        setTimeout(() => {
          if (captureInBtn) captureInBtn.disabled = false;
          if (captureOutBtn) captureOutBtn.disabled = false;
        }, 2000);
      }
    };

    if (captureInBtn) captureInBtn.addEventListener("click", () => doMark('in'));
    if (captureOutBtn) captureOutBtn.addEventListener("click", () => doMark('out'));

    window.addEventListener("beforeunload", () => {
      if (stream) stream.getTracks().forEach(t => t.stop());
    });
  }

  // Initialize registration form variables
  const regForm = document.querySelector("[data-register-form]");
  const empIdInput = document.querySelector("[data-emp-id]");
  const passwordInput = document.querySelector("[data-password]");
  const passwordError = document.querySelector("[data-password-error]");
  const faceImageInput = document.querySelector("[data-face-image-input]");

  // Password validation function
  function validatePasswordFormat(password) {
    if (password.length > 8) return { valid: false, error: "Password must be maximum 8 characters" };
    if (!/[A-Z]/.test(password)) return { valid: false, error: "Password must contain at least one uppercase letter" };
    if (!/[a-z]/.test(password)) return { valid: false, error: "Password must contain at least one lowercase letter" };
    if (!/[0-9]/.test(password)) return { valid: false, error: "Password must contain at least one number" };
    if (!/[$#.]/.test(password)) return { valid: false, error: "Password must contain at least one special character ($, #, .)" };
    return { valid: true };
  }

  // Password validation on input
  if (passwordInput && passwordError) {
    passwordInput.addEventListener("blur", () => {
      const pwd = passwordInput.value.trim();
      if (pwd) {
        const validation = validatePasswordFormat(pwd);
        if (!validation.valid) {
          passwordError.textContent = validation.error;
          passwordError.style.color = "#b91c1c";
        } else {
          passwordError.textContent = "✓ Password format valid";
          passwordError.style.color = "#166534";
        }
      } else {
        passwordError.textContent = "";
      }
    });
  }

  // Password Generator
  const genBtn = document.querySelector("[data-generate-password]");
  if (genBtn && passwordInput) {
    genBtn.addEventListener("click", () => {
      const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@$#.";
      let password = "";
      password += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[Math.floor(Math.random() * 26)];
      password += "abcdefghijklmnopqrstuvwxyz"[Math.floor(Math.random() * 26)];
      password += "0123456789"[Math.floor(Math.random() * 10)];
      password += "@$#."[Math.floor(Math.random() * 4)];
      for (let i = 0; i < 4; i++) password += chars[Math.floor(Math.random() * chars.length)];
      password = password.split('').sort(() => 0.5 - Math.random()).join('');

      passwordInput.value = password;

      if (passwordError) {
        const v = validatePasswordFormat(password);
        passwordError.textContent = v.valid ? "✓ Password generated" : v.error;
        passwordError.style.color = v.valid ? "#166534" : "#b91c1c";
      }
    });
  }

  if (regForm) {
    const regMsg = document.querySelector("[data-register-msg]");

    regForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const user = OfficeApp.currentUser();
      // Allow Admin to register employees
      if ((user?.role || "").toLowerCase() !== "admin") {
        if (regMsg) {
          regMsg.innerHTML = `${OfficeApp.fmtBadge("Rejected")} Admin access required.`;
          regMsg.style.display = 'block';
        }
        return;
      }

      const fd = new FormData(regForm);
      const emp_id = String(fd.get("emp_id") || "").trim();
      const full_name = String(fd.get("full_name") || "").trim();
      let password = String(fd.get("password") || "").trim();

      // Admin attaches photo for both face recognition and profile
      const employee_photo = document.getElementById("employee_photo_data")?.value || null;
      console.log("Admin photo upload - employee_photo:", employee_photo ? "uploaded" : "not uploaded");

      // Validate photo is required
      if (!employee_photo) {
        if (regMsg) {
          regMsg.innerHTML = `${OfficeApp.fmtBadge("Pending")} Employee photo is required.`;
          regMsg.style.display = 'block';
        }
        return;
      }

      // Handle 5-shot images (fallback for old format)
      const faceImagesJson = document.getElementById("face_images_data") ? document.getElementById("face_images_data").value : null;
      let face_images = [];
      try {
        if (faceImagesJson) face_images = JSON.parse(faceImagesJson);
      } catch (e) { console.error("Error parsing face images", e); }


      if (!full_name) {
        if (regMsg) {
          regMsg.innerHTML = `${OfficeApp.fmtBadge("Pending")} Full Name is required.`;
          regMsg.style.display = 'block';
        }
        return;
      }

      if (!password) {
        if (regMsg) {
          regMsg.innerHTML = `${OfficeApp.fmtBadge("Pending")} Password is required.`;
          regMsg.style.display = 'block';
        }
        return;
      }

      // Validate password format
      const validation = validatePasswordFormat(password);
      if (!validation.valid) {
        if (regMsg) {
          regMsg.innerHTML = `${OfficeApp.fmtBadge("Rejected")} ${validation.error}`;
          regMsg.style.display = 'block';
        }
        if (passwordError) passwordError.textContent = validation.error;
        return;
      }

      // Submit to API
      try {
        const submitBtn = regForm.querySelector("button[type='submit']");
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.textContent = "Saving...";
        }

        const response = await fetch(`${OfficeApp.API_BASE_URL || 'http://localhost:5000/api'}/employees`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name,
            password,
            mobile: String(fd.get("mobile") || "").trim(),
            email: String(fd.get("email") || "").trim(),
            designation: String(fd.get("designation") || "").trim(),
            joining_date: String(fd.get("joining_date") || "").trim() || null,
            address: String(fd.get("address") || "").trim(),
            role: String(fd.get("role") || "Employee"),
            status: String(fd.get("status") || "Active"),
            // Admin attaches photo for both face recognition and profile
            ...(employee_photo && { employee_photo }),
            ...(face_images.length > 0 && { face_images })
          })
        });

        const data = await response.json();

        if (!data.success) {
          if (regMsg) {
            regMsg.innerHTML = `${OfficeApp.fmtBadge("Rejected")} ${data.error || "Registration failed"}`;
            regMsg.style.display = 'block';
          }
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Save Employee";
          }
          return;
        }

        const createdEmpId = data.emp_id;
        const tempPassword = data.temp_password;

        if (regMsg) {
          regMsg.innerHTML = `${OfficeApp.fmtBadge("Approved")} Employee registered! Username: <strong>${createdEmpId}</strong>`;
          regMsg.style.display = 'block';
        }

        // Show temporary password popup
        showTempPasswordPopup(createdEmpId, tempPassword);

        regForm.reset();

        // Clear photo preview and status
        document.getElementById("employee_photo_data").value = '';
        const photoPreview = document.getElementById("photo-preview");
        if (photoPreview) {
          photoPreview.innerHTML = '<span style="color:#9ca3af; font-size:12px;">No photo attached</span>';
          photoPreview.style.border = '1px dashed #d1d5db';
        }
        document.getElementById('photo-status').textContent = '';

        // Clear face preview
        if (document.getElementById("face_images_data")) document.getElementById("face_images_data").value = '';
        const slots = document.querySelectorAll('#face-previews .face-slot');
        slots.forEach(slot => {
          slot.innerHTML = '';
          slot.style.border = '1px dashed #d1d5db';
        });
        document.getElementById('face-status').textContent = '';


        // Reload next emp_id
        const nextIdResponse = await fetch(`${OfficeApp.API_BASE_URL || 'http://localhost:5000/api'}/employees/next-id`);
        const nextIdData = await nextIdResponse.json();
        if (nextIdData.success && empIdInput) {
          empIdInput.value = nextIdData.emp_id;
        }

        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Save Employee";
        }

      } catch (error) {
        console.error("Registration error:", error);
        if (regMsg) {
          regMsg.innerHTML = `${OfficeApp.fmtBadge("Rejected")} Connection error. Ensure backend is running.`;
          regMsg.style.display = 'block';
        }
        const submitBtn = regForm.querySelector("button[type='submit']");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Save Employee";
        }
      }
    });
  }

  // Admin dashboard: DISABLED - now handled by inline script in admin_dashboard.html
  // The new implementation includes View buttons and enhanced functionality
  /*
  const adminTable = document.querySelector("tbody[data-admin-attendance]");
  if (adminTable) {
    const dateLabel = document.querySelector("[data-dashboard-date]");
   
    let attendanceData = [];

    const dateLongEl = document.querySelector("[data-dashboard-date-long]");
    const render = (date) => {
      const d = date || new Date().toISOString().slice(0, 10);
      if (dateLabel) dateLabel.textContent = "Date: " + d;
      if (dateLongEl) {
        try {
          const dateObj = new Date(d + "T12:00:00");
          const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
          dateLongEl.textContent = " (" + dateObj.toLocaleDateString(undefined, options) + ")";
        } catch (e) { console.error("Error formatting date", e); }
      }

      adminTable.innerHTML = attendanceData.map(r => {
        const dateStr = (r) => {
          if (!r.date && !r.att_date) return '—';
          try {
            // Handle DD-MM-YYYY format from backend
            const dateField = r.date || r.att_date;
            if (typeof dateField === 'string' && /^\d{2}-\d{2}-\d{4}$/.test(dateField)) {
              return dateField; // Already in DD-MM-YYYY format
            } else if (typeof dateField === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateField)) {
              // Convert YYYY-MM-DD to DD-MM-YYYY without Date object to avoid timezone
              const [year, month, day] = dateField.split('-');
              return `${day}-${month}-${year}`;
            } else {
              // Return as-is if format is unexpected
              return dateField || '—';
            }
          } catch (e) { return dateField || '—'; }
        };

        return `
          <tr>
            <td>${dateStr(r)}</td>
            <td>${r.emp_id}</td>
            <td>${r.name}</td>
            <td>${r.entry_time || r.in_time || '—'}</td>
            <td>${r.exit_time || r.out_time || '—'}</td>
            <td>${OfficeApp.fmtBadge(r.status)}</td>
          </tr>
        `;
      }).join("") || `<tr><td colspan="6" class="muted">No records for today</td></tr>`;

      const setNum = (sel, n) => { const el = document.querySelector(sel); if (el) el.textContent = String(n); };
      setNum("[data-kpi-total]", totalEmp);
      setNum("[data-kpi-present]", presentCount);
      setNum("[data-kpi-absent]", absentCount);
      setNum("[data-kpi-leave]", leaveCount);
      setNum("[data-kpi-late]", lateCount);
    };

    let totalEmp = 0, presentCount = 0, absentCount = 0, leaveCount = 0, lateCount = 0;

    const fetchData = () => {
      const today = new Date().toISOString().slice(0, 10);
      Promise.all([
        fetch(`${OfficeApp.API_BASE_URL}/attendance?date=${today}`).then(r => r.json()).catch(() => ({ success: false })),
        fetch(`${OfficeApp.API_BASE_URL}/employees`).then(r => r.json()).catch(() => ({ success: false })),
        fetch(`${OfficeApp.API_BASE_URL}/stats/daily?date=${today}`).then(r => r.json()).catch(() => ({ success: false }))
      ]).then(([attRes, empRes, statsRes]) => {
        if (attRes && attRes.success) attendanceData = attRes.attendance || [];
        else attendanceData = [];
        if (empRes && empRes.success) totalEmp = (empRes.employees || []).length;
        else totalEmp = 0;
        if (statsRes && statsRes.success) {
          presentCount = statsRes.present || 0;
          absentCount = statsRes.absent || 0;
          leaveCount = statsRes.leave || 0;
          lateCount = 0;
        }
        render(today);
      }).catch((err) => {
        attendanceData = [];
        totalEmp = presentCount = absentCount = leaveCount = lateCount = 0;
        adminTable.innerHTML = '<tr><td colspan="6" class="muted" style="color:#b91c1c;">Connection error. Ensure backend is running on http://localhost:5000</td></tr>';
        const setNum = (sel, n) => { const el = document.querySelector(sel); if (el) el.textContent = String(n); };
        setNum("[data-kpi-total]", "—"); setNum("[data-kpi-present]", "—"); setNum("[data-kpi-absent]", "—"); setNum("[data-kpi-leave]", "—"); setNum("[data-kpi-late]", "—");
      });
    };
    

    fetchData();
  }
  */

  // Employee dashboard - fetch profile from API and show name, designation, department, joining date, photo
  const empCard = document.querySelector("[data-emp-name]");
  if (empCard) {
    const user = OfficeApp.currentUser();
    if (user && user.emp_id) {
      const apiUrl = (OfficeApp.API_BASE_URL || (window.location.origin + "/api"));
      fetch(`${apiUrl}/profile/${encodeURIComponent(user.emp_id)}`)
        .then(r => r.json())
        .then(d => {
          if (!d.success || !d.profile) {
            const set = (sel, text) => { const el = document.querySelector(sel); if (el) el.textContent = text || "—"; };
            set("[data-emp-name]", user.name || user.emp_id);
            set("[data-emp-id]", user.emp_id);
            set("[data-user-initial]", (user.name || user.emp_id).charAt(0).toUpperCase());
            return;
          }
          const p = d.profile;
          const set = (sel, text) => { const el = document.querySelector(sel); if (el) el.textContent = text || "—"; };
          set("[data-emp-name]", p.full_name || user.name || user.emp_id);
          set("[data-emp-id]", p.emp_id || user.emp_id);
          set("[data-emp-designation]", p.designation || "Employee");
          set("[data-emp-department]", p.department || "—");
          set("[data-emp-joining]", p.joining_date ? new Date(p.joining_date).toLocaleDateString() : "—");
          const initial = (p.full_name || user.name || user.emp_id || "E").trim().charAt(0).toUpperCase();
          set("[data-user-initial]", initial);
          const picPath = p.profile_pic_path || (p.face_profile && p.face_profile.image_path);
          const avatarEl = empCard.closest(".gradient-card")?.querySelector("[data-user-initial]")?.parentElement;
          if (avatarEl && picPath) {
            const base = (apiUrl || "").replace(/\/api\/?$/, "");
            const src = picPath.startsWith("http") ? picPath : base + (picPath.startsWith("/") ? "" : "/") + picPath;
            avatarEl.innerHTML = `<img src="${src.replace(/"/g, "&quot;")}" alt="Profile" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">`;
          }
        })
        .catch(() => {
          const user2 = OfficeApp.currentUser();
          if (user2) {
            const set = (sel, text) => { const el = document.querySelector(sel); if (el) el.textContent = text || "—"; };
            set("[data-emp-name]", user2.name || user2.emp_id);
            set("[data-emp-id]", user2.emp_id);
            set("[data-emp-designation]", "Employee");
            set("[data-user-initial]", (user2.name || user2.emp_id).charAt(0).toUpperCase());
          }
        });
    }
  }

  // Employee dashboard - fetch from API with daily + month filter
  const empTable = document.querySelector("tbody[data-emp-attendance]");
  if (empTable) {
    const user = OfficeApp.currentUser();
    const monthEl = document.querySelector("#emp-filter-month");
    const dateEl = document.querySelector("#emp-filter-date");

    const fetchEmpAttendance = () => {
      const month = (monthEl?.value || "").trim();
      const date = (dateEl?.value || "").trim();
      let url = `${OfficeApp.API_BASE_URL}/attendance?emp_id=${user.emp_id}`;
      if (date) url += `&date=${date}`;
      else if (month) url += `&month=${month}`;
      fetch(url)
        .then(r => r.json())
        .then(d => {
          const rows = (d.attendance || []).filter(a => a.emp_id === user.emp_id);
          empTable.innerHTML = rows.map(r => `
            <tr>
              <td>${r.date || r.att_date}</td>
              <td>${r.entry_time || r.in_time || '—'}</td>
              <td>${r.exit_time || r.out_time || '—'}</td>
              <td>${OfficeApp.fmtBadge(r.status)}</td>
            </tr>
          `).join("") || `<tr><td colspan="4" class="muted">No records</td></tr>`;

          const present = rows.filter(a => (a.status || "").toLowerCase() === "present").length;
          const absent = rows.filter(a => (a.status || "").toLowerCase() === "absent").length;
          const leave = rows.filter(a => (a.status || "").toLowerCase() === "leave").length;
          const late = rows.filter(a => (a.status || "").toLowerCase() === "late").length;
          const setNum = (sel, n) => { const el = document.querySelector(sel); if (el) el.textContent = String(n); };
          setNum("[data-kpi-present]", present);
          setNum("[data-kpi-absent]", absent);
          setNum("[data-kpi-leave]", leave);
          setNum("[data-kpi-late]", late);
        })
        .catch(() => { empTable.innerHTML = `<tr><td colspan="4" class="muted" style="color:#b91c1c;">Connection error. Ensure backend is running on port 5000.</td></tr>`; });
    };

    monthEl?.addEventListener("change", fetchEmpAttendance);
    dateEl?.addEventListener("change", fetchEmpAttendance);
    fetchEmpAttendance();

    const leaveBtn = document.querySelector("[data-apply-leave]");
    leaveBtn?.addEventListener("click", () => (window.location.href = "leave_application.html"));
  }

  // Leave application page
  const leaveForm = document.querySelector("form[data-leave]");
  const leaveTbody = document.querySelector("tbody[data-leave-history]");
  if (leaveForm) {
    const user = OfficeApp.currentUser();
    const state = OfficeApp.getState();

    // Create error/success message container
    const messageDiv = document.createElement("div");
    messageDiv.style.cssText = "margin-bottom: var(--space-lg); padding: var(--space-md); border-radius: 6px; display: none; font-weight: 500;";
    leaveForm.parentElement.insertBefore(messageDiv, leaveForm);

    const showMessage = (text, isError = false) => {
      messageDiv.textContent = text;
      messageDiv.style.display = "block";
      messageDiv.style.backgroundColor = isError ? "#fee2e2" : "#dcfce7";
      messageDiv.style.color = isError ? "#991b1b" : "#166534";
      messageDiv.style.borderLeft = `4px solid ${isError ? "#dc2626" : "#16a34a"}`;
      
      if (!isError) {
        setTimeout(() => {
          messageDiv.style.display = "none";
        }, 4000);
      }
    };

    const render = () => {
      // Only render if leave history table exists on this page
      if (!leaveTbody) return;
      
      // Fetch from backend
      fetch(`${OfficeApp.API_BASE_URL}/leaves?emp_id=${user.emp_id}`)
        .then(r => r.json())
        .then(d => {
          if (d.success) {
            leaveTbody.innerHTML = d.leaves.map(l => `
            <tr>
              <td>${l.from_date} → ${l.to_date}</td>
              <td>${l.leave_type}</td>
              <td>${(l.reason || '—').substring(0, 40)}${(l.reason || '').length > 40 ? '…' : ''}</td>
              <td>${OfficeApp.fmtBadge(l.status)}</td>
              <td>
                <button class="btn btn-gradient-primary btn-sm" style="padding:6px 12px; font-size:12px; border-radius:4px;" onclick="viewEmployeeLeaveDetails(${JSON.stringify(l).replace(/"/g, '&quot;')})">
                  <span style="display: flex; align-items: center; gap:4px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    View Details
                  </span>
                </button>
              </td>
            </tr>
          `).join("") || `<tr><td colspan="5" class="muted">No leave history</td></tr>`;
          }
        });
    };
    render();


  }

  // Attendance report - handled by inline script in attendance_report.html (today default, API)

  // Show temporary password popup
  function showTempPasswordPopup(empId, tempPassword) {
    console.log('=== PASSWORD POPUP DEBUG ===');
    console.log('empId:', empId);
    console.log('tempPassword:', tempPassword);
    console.log('tempPassword type:', typeof tempPassword);
    console.log('tempPassword length:', tempPassword ? tempPassword.length : 'N/A');
    console.log('tempPassword trimmed:', tempPassword ? tempPassword.trim() : 'N/A');
    console.log('==========================');

    if (!tempPassword || tempPassword.trim() === '') {
      console.error('ERROR: tempPassword is null or empty!');
      alert('Error: No password was generated! Please try registering again.');
      return;
    }

    // Create modal overlay
    const modalOverlay = document.createElement('div');
    modalOverlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10000;
  `;

    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    max-width: 400px;
    width: 90%;
    text-align: center;
  `;

    modalContent.innerHTML = `
    <div style="font-size: 48px; margin-bottom: 20px;">🎉</div>
    <h2 style="color: #333; margin-bottom: 20px;">Employee Registered Successfully!</h2>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
      <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Employee Username:</p>
      <p style="margin: 0; font-size: 18px; font-weight: bold; color: #333;">${empId}</p>
    </div>
    <div style="background: #fff3cd; border: 2px solid #ffeaa7; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
      <p style="margin: 0 0 10px 0; color: #856404; font-size: 14px; font-weight: bold;">⚠️ TEMPORARY PASSWORD</p>
      <p id="modalPassword" style="margin: 0; font-size: 20px; font-weight: bold; color: #333; font-family: monospace; letter-spacing: 2px; user-select: all; -webkit-user-select: all; -moz-user-select: all; -ms-user-select: all;">${tempPassword || 'ERROR: No password generated'}</p>
      <p style="margin: 10px 0 0 0; color: #856404; font-size: 12px;">Copy this password now. It will not be shown again!</p>
    </div>
    <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
      <p style="margin: 0; color: #155724; font-size: 14px;">
        <strong>📋 Next Steps:</strong><br>
        1. Share these credentials with the employee<br>
        2. Employee must change password on first login<br>
        3. Temporary password expires after first use
      </p>
    </div>
    <button id="copyPasswordBtn" style="
      background: #007bff;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 5px;
      cursor: pointer;
      margin-right: 10px;
      font-size: 14px;
    ">📋 Copy Password</button>
    <button id="closeModalBtn" style="
      background: #6c757d;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 14px;
    ">Close</button>
  `;

    modalOverlay.appendChild(modalContent);
    document.body.appendChild(modalOverlay);

    // Copy password functionality
    const copyBtn = document.getElementById('copyPasswordBtn');
    const closeBtn = document.getElementById('closeModalBtn');

    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        console.log('=== COPY BUTTON DEBUG ===');
        console.log('Copy button clicked');

        // Read password from DOM element instead of variable
        const passwordElement = document.getElementById('modalPassword');
        const password = passwordElement ? passwordElement.textContent.trim() : '';

        console.log('Password element:', passwordElement);
        console.log('Password text:', password);
        console.log('Password length:', password.length);
        console.log('========================');

        if (!password) {
          console.error('ERROR: No password to copy!');
          alert('Error: No password to copy!');
          return;
        }

        console.log('Attempting to copy password...');

        // Try modern clipboard API first
        if (navigator.clipboard && navigator.clipboard.writeText) {
          console.log('Using modern Clipboard API...');
          navigator.clipboard.writeText(password).then(() => {
            console.log('Password copied to clipboard successfully');
            copyBtn.textContent = '✅ Copied!';
            copyBtn.style.background = '#28a745';
            setTimeout(() => {
              copyBtn.textContent = '📋 Copy Password';
              copyBtn.style.background = '#007bff';
            }, 2000);
          }).catch(err => {
            console.error('Clipboard API failed:', err);
            // Fallback to older method
            const passwordElement = document.getElementById('modalPassword');
            const password = passwordElement ? passwordElement.textContent.trim() : '';
            fallbackCopyToClipboard(password, copyBtn);
          });
        } else {
          // Fallback for older browsers
          const passwordElement = document.getElementById('modalPassword');
          const password = passwordElement ? passwordElement.textContent.trim() : '';
          fallbackCopyToClipboard(password, copyBtn);
        }
      });
    }

    // Close modal functionality
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
      });
    }

    // Close on overlay click
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) {
        document.body.removeChild(modalOverlay);
      }
    });
  }

  // Fallback copy function for older browsers
  function fallbackCopyToClipboard(text, button) {
    console.log('=== FALLBACK COPY DEBUG ===');
    console.log('Text to copy:', text);
    console.log('Text length:', text ? text.length : 'N/A');
    console.log('==========================');

    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      textArea.setSelectionRange(0, 99999); // For mobile devices

      console.log('Attempting execCommand("copy")...');
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);

      console.log('execCommand result:', successful);

      if (successful) {
        console.log('Password copied using fallback method');
        button.textContent = '✅ Copied!';
        button.style.background = '#28a745';
        setTimeout(() => {
          button.textContent = '📋 Copy Password';
          button.style.background = '#007bff';
        }, 2000);
      } else {
        console.error('Fallback copy method failed');
        alert('Failed to copy password. Please copy manually: ' + text);
      }
    } catch (err) {
      console.error('Fallback copy error:', err);
      alert('Failed to copy password. Please copy manually: ' + text);
    }
  }

  // Employee Leave Details Modal Functions
  window.viewEmployeeLeaveDetails = function (leave) {
    console.log('Viewing employee leave details:', leave);

    // Populate modal with leave data
    document.getElementById('employee-detail-emp-id').textContent = leave.emp_id || '—';
    document.getElementById('employee-detail-leave-type').textContent = leave.leave_type || '—';
    document.getElementById('employee-detail-from-date').textContent = formatDate(leave.from_date) || '—';
    document.getElementById('employee-detail-to-date').textContent = formatDate(leave.to_date) || '—';
    document.getElementById('employee-detail-status').innerHTML = OfficeApp.fmtBadge?.(leave.status) || leave.status || '—';
    document.getElementById('employee-detail-applied-date').textContent = formatDate(leave.created_at) || '—';
    document.getElementById('employee-detail-reason').textContent = leave.reason || '—';

    // Show modal
    const modal = document.getElementById('employeeLeaveDetailsModal');
    if (modal) {
      modal.style.display = 'flex';
      modal.classList.add('show');
    } else {
      console.error('Modal not found: employeeLeaveDetailsModal');
      alert('Modal not found. Please refresh the page and try again.');
    }
  };

  window.closeEmployeeLeaveDetailsModal = function () {
    const modal = document.getElementById('employeeLeaveDetailsModal');
    if (modal) {
      modal.style.display = 'none';
      modal.classList.remove('show');
    }
  };

  function formatDate(dateString) {
    if (!dateString) return '';

    try {
      const date = new Date(dateString);
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}-${month}-${year}`; // dd-mm-yyyy format
    } catch (e) {
      return dateString;
    }
  }

  // Close modal when clicking overlay
  document.addEventListener('click', function (event) {
    const modal = document.getElementById('employeeLeaveDetailsModal');
    if (event.target === modal) {
      closeEmployeeLeaveDetailsModal();
    }
  });

});
