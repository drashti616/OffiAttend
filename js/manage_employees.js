/* Employee Management Page - Admin view with employee details including photos */
const API_BASE_URL = 'http://localhost:5000/api';

document.addEventListener("DOMContentLoaded", () => {
  console.log('Manage Employees page loaded');
  console.log('Checking OfficeApp availability...');
  
  // Debug: Check what's loaded
  console.log('window.OfficeApp:', typeof window.OfficeApp);
  if (window.OfficeApp) {
    console.log('OfficeApp methods:', Object.keys(window.OfficeApp));
  }
  
  // Wait a bit for OfficeApp to load
  setTimeout(() => {
    try {
      if (!window.OfficeApp) {
        console.error("OfficeApp not found after timeout");
        const tb = document.querySelector("tbody[data-employees-list]");
        if (tb) tb.innerHTML = "<tr><td colspan='10' style='color:red; font-weight:bold;'>Error: OfficeApp (JS) not loaded. Check console.</td></tr>";
        return;
      }

    const user = OfficeApp.requireAuth();
    if (!user || (user.role || "").toLowerCase() !== "admin") {
      window.location.href = "admin_dashboard.html";
      return;
    }

    const tbody = document.querySelector("tbody[data-employees-list]");
    if (!tbody) throw new Error("tbody[data-employees-list] not found");

    // Load employees
    async function loadEmployees() {
      console.log('=== loadEmployees called ===');
      
      // Add visual indicator
      const tbody = document.querySelector("tbody[data-employees-list]");
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="10" class="muted" style="background: yellow; color: red; font-weight: bold;">🔥 loadEmployees() FUNCTION CALLED! 🔥</td></tr>`;
        // Wait a moment then continue
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      try {
        const monthSelector = document.getElementById('month-selector');
        let month = monthSelector ? monthSelector.value : '';
        console.log('Month:', month);

        // Default to current month if empty
        if (!month) {
          const now = new Date();
          month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
          if (monthSelector) monthSelector.value = month;
        }

        console.log('Making API call to:', `${API_BASE_URL}/employees?month=${month}`);
        tbody.innerHTML = `<tr><td colspan="10" class="muted">Loading from API…</td></tr>`;
        const response = await fetch(`${API_BASE_URL}/employees?month=${month}`);
        console.log('Response status:', response.status);
        const data = await response.json().catch(() => ({}));
        console.log('Response data:', data);

        if (!response.ok) {
          const errMsg = data.error || `HTTP ${response.status}`;
          console.error('Response not OK:', errMsg);
          tbody.innerHTML = `<tr><td colspan="10" class="muted" style="color:#b91c1c;">API error: ${errMsg}. Check backend (Flask) and MySQL.</td></tr>`;
          return;
        }

        if (!data.success) {
          console.error('API returned success=false:', data);
          tbody.innerHTML = `<tr><td colspan="10" class="muted" style="color:#b91c1c;">Error: ${data.error || 'Unknown'}. Ensure MySQL is running and database is initialized (run backend/init_db.py).</td></tr>`;
          return;
        }

        if (!data.employees || data.employees.length === 0) {
          console.error('No employees found:', data);
          tbody.innerHTML = `<tr><td colspan="10" class="muted">No employees in database. Click <strong>Register New Employee</strong> to add one. Ensure MySQL and backend are running.</td></tr>`;
          return;
        }

        console.log('About to render employees, count:', data.employees.length);
        console.log('Sample employee data:', data.employees[0]);

        // Build full URL for profile pics if they are relative (e.g. from Flask static)
        const baseForPics = API_BASE_URL.replace(/\/api\/?$/, '');
        console.log('Starting employee rendering...');
        
        const htmlContent = data.employees.map((emp, index) => {
          console.log(`Rendering employee ${index + 1}:`, emp.emp_id, emp.full_name);
          
          const photoUrl = emp.profile_pic_path
            ? (emp.profile_pic_path.startsWith('http') ? emp.profile_pic_path : baseForPics + (emp.profile_pic_path.startsWith('/') ? '' : '/') + emp.profile_pic_path)
            : '';
          const imgSrc = photoUrl || 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/> </svg>');
          
          // Format role badge
          const roleBadge = emp.role 
            ? `<span class="badge ${emp.role.toLowerCase() === 'admin' ? 'badge-approved' : 'badge-info'}">${emp.role}</span>`
            : '<span class="badge">—</span>';
          
          // Format status badge  
          const statusBadge = emp.status
            ? `<span class="badge ${emp.status.toLowerCase() === 'active' ? 'badge-approved' : emp.status.toLowerCase() === 'inactive' ? 'badge-rejected' : 'badge-pending'}">${emp.status}</span>`
            : '<span class="badge">—</span>';
          
          console.log(`Generated badges for ${emp.emp_id}: role=${roleBadge}, status=${statusBadge}`);
          
          return `
          <tr>
            <td style="text-align:center;">
              <img src="${imgSrc}" alt="${(emp.full_name || '').replace(/"/g, '&quot;')}" 
                style="width:40px; height:40px; border-radius:50%; object-fit:cover; background:#f3f4f6; cursor:pointer;"
                onclick="viewEmployeeDetails('${emp.emp_id}')" title="View details">
            </td>
            <td><strong>${emp.emp_id}</strong></td>
            <td>${emp.full_name || '—'}</td>
            <td><span class="badge" style="background:#dcfce7; color:#166534;">${emp.total_present || 0}</span></td>
            <td><span class="badge" style="background:#fee2e2; color:#991b1b;">${emp.total_absent || 0}</span></td>
            <td><span class="badge" style="background:#ffedd5; color:#9a3412;">${emp.total_late || 0}</span></td>
            <td>${emp.designation || '—'}</td>
            <td>${roleBadge}</td>
            <td>${statusBadge}</td>
            <td>
              <div style="display:flex; gap:6px; flex-wrap:wrap;">
                <button class="btn btn-outline" style="font-size:0.85rem; padding:4px 8px;" onclick="viewEmployeeDetails('${emp.emp_id}')">View</button>
                <button type="button" class="btn btn-outline btn-delete-row" style="font-size:0.85rem; padding:4px 8px; color:#b91c1c; border-color:#b91c1c;" data-emp-id="${(emp.emp_id || '').replace(/"/g, '&quot;')}" data-emp-name="${(emp.full_name || emp.emp_id || '').replace(/"/g, '&quot;')}" title="Delete this employee and all related data">Delete</button>
              </div>
            </td>
          </tr>
        `;
        }).join('');
        
        console.log('Generated HTML content length:', htmlContent.length);
        console.log('Setting tbody.innerHTML...');
        tbody.innerHTML = htmlContent;
        console.log('tbody.innerHTML set successfully');

        tbody.querySelectorAll('.btn-delete-row').forEach(btn => {
          btn.addEventListener('click', function () {
            const id = this.getAttribute('data-emp-id');
            const name = this.getAttribute('data-emp-name') || id;
            if (id) window.deleteEmployee(id, name);
          });
        });
      } catch (error) {
        console.error("Error loading employees:", error);
        const msg = error.message || String(error);
        const isNetwork = /failed|network|cors|load/i.test(msg) || error.name === 'TypeError';
        tbody.innerHTML = `<tr><td colspan="10" class="muted" style="color:#b91c1c;">${isNetwork
          ? 'Connection error: Is the backend running? Open a terminal, run: python backend/app.py (and ensure MySQL is running).'
          : 'Error: ' + msg}</td></tr>`;
      }
    }

    // Event listener for month change
    const monthSel = document.getElementById('month-selector');
    if (monthSel) {
      monthSel.addEventListener('change', loadEmployees);
    } else {
      setTimeout(() => {
        const ms = document.getElementById('month-selector');
        if (ms) ms.addEventListener('change', loadEmployees);
      }, 500);
    }

    // Initial load - call immediately without setTimeout
    console.log('Calling loadEmployees immediately (no timeout)');
    loadEmployees();

    window.deleteEmployee = async function (empId, displayName) {
      if (!confirm(`Permanently delete "${displayName || empId}" and all their attendance, leaves, and face data?`)) return;
      try {
        const r = await fetch(`${API_BASE_URL}/employees/${encodeURIComponent(empId)}`, { method: 'DELETE' });
        const d = await r.json().catch(() => ({}));
        if (d.success) { loadEmployees(); } else { alert(d.error || 'Delete failed'); }
      } catch (e) { alert('Connection error. Ensure backend is running.'); }
    };

    // Initial load
    loadEmployees();

    // Expose function globally for onclick handlers
    window.viewEmployeeDetails = async function (empId) {
      const modal = document.getElementById('employee-detail-modal');
      const content = document.getElementById('employee-detail-content');

      if (!modal) {
        alert('Detail modal not found');
        return;
      }

      modal.style.display = 'flex';
      content.innerHTML = '<p class="muted">Loading employee details...</p>';

      try {
        const monthSelector = document.getElementById('month-selector');
        const month = monthSelector ? monthSelector.value : '';
        const response = await fetch(`${API_BASE_URL}/profile/${empId}?month=${month}`);
        const data = await response.json();

        if (!data.success) {
          content.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
          return;
        }

        const emp = data.profile;
        const baseForPics = API_BASE_URL.replace(/\/api\/?$/, '');
        const photoPath = emp.profile_pic_path || emp.face_profile?.image_path;
        const photoUrl = photoPath ? (photoPath.startsWith('http') ? photoPath : baseForPics + (photoPath.startsWith('/') ? '' : '/') + photoPath) : '';

        let html = `
          <div style="display:grid; grid-template-columns: 150px 1fr; gap:20px; margin-bottom:20px;">
            ${photoUrl ?
            `<img src="${photoUrl.replace(/"/g, '&quot;')}" alt="${(emp.full_name || '').replace(/"/g, '&quot;')}" 
                style="width:150px; height:150px; object-fit:cover; border-radius:8px; background:#f3f4f6; border:2px solid #e5e7eb;">` :
            `<div style="width:150px; height:150px; background:#f3f4f6; border-radius:8px; border:2px solid #e5e7eb; display:flex; align-items:center; justify-content:center; color:#9ca3af; font-size:3rem;">📷</div>`
          }
            <div>
              <h2 style="margin:0; font-size:1.5rem;">${emp.full_name}</h2>
              <div class="row" style="gap:8px; margin-top:8px;">
                <span class="badge">${emp.designation || '—'}</span>
                <span class="badge">${emp.status || '—'}</span>
              </div>
              
              <div style="margin-top:16px;">
                <div class="small"><strong>Employee ID:</strong> ${emp.emp_id}</div>
                <div class="small"><strong>Role:</strong> ${emp.role || '—'}</div>
                <div class="small"><strong>Department:</strong> ${emp.department || '—'}</div>
                <div class="small"><strong>Email:</strong> ${emp.email || '—'}</div>
                <div class="small"><strong>Mobile:</strong> ${emp.mobile || '—'}</div>
              </div>

              <div style="margin-top:12px; background:#f0f9ff; padding:10px; border-radius:6px; border-left:3px solid #3b82f6;">
                <div class="small"><strong>Account Status:</strong></div>
                <div class="small" id="emp-password-display">
                  <button class="btn btn-outline" style="font-size:0.8rem; padding:2px 8px; margin-top:4px;" onclick="revealEmpPassword('${emp.emp_id}')">
                    🔐 Reveal Password
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div style="border-top:1px solid #e5e7eb; padding-top:16px; margin-top:16px;">
            <div class="small"><strong>Joining Date:</strong> ${emp.joining_date || '—'}</div>
            <div class="small"><strong>Member Since:</strong> ${emp.created_at ? new Date(emp.created_at).toLocaleDateString() : '—'}</div>
          </div>
        `;

        // Append Stats
        const lateDatesHtml = (emp.late_dates || []).length > 0
          ? emp.late_dates.map(d => `<div class="badge" style="background:#fff7ed; color:#c2410c; border:1px solid #fdba74;">${d.date} (${d.time})</div>`).join('')
          : '<span class="muted small">No late entries</span>';

        html += `
          <div style="margin-top:20px; padding-top:20px; border-top:1px solid #e5e7eb;">
             <h4 style="margin:0 0 10px 0;">Monthly Attendance Stats (${document.getElementById('month-selector')?.value || 'Current Month'})</h4>
             <div class="row" style="gap:10px; margin-bottom:15px;">
                <div style="flex:1; padding:10px; background:#f0f9ff; border-radius:6px; text-align:center;">
                   <div style="font-size:0.8rem; color:#0369a1;">Present</div>
                   <div style="font-size:1.2rem; font-weight:bold; color:#0c4a6e;">${emp.total_present || 0}</div>
                </div>
                <div style="flex:1; padding:10px; background:#fef2f2; border-radius:6px; text-align:center;">
                   <div style="font-size:0.8rem; color:#b91c1c;">Absent</div>
                   <div style="font-size:1.2rem; font-weight:bold; color:#7f1d1d;">${emp.total_absent || 0}</div>
                </div>
                <div style="flex:1; padding:10px; background:#fffbeb; border-radius:6px; text-align:center;">
                   <div style="font-size:0.8rem; color:#b45309;">Late</div>
                   <div style="font-size:1.2rem; font-weight:bold; color:#78350f;">${emp.total_late || 0}</div>
                </div>
                <div style="flex:1; padding:10px; background:#f3f4f6; border-radius:6px; text-align:center;">
                   <div style="font-size:0.8rem; color:#4b5563;">Leave</div>
                   <div style="font-size:1.2rem; font-weight:bold; color:#1f2937;">${emp.total_leave || 0}</div>
                </div>
             </div>
             
             <div style="background:#fff; border:1px solid #e5e7eb; padding:10px; border-radius:6px;">
                <strong style="display:block; margin-bottom:5px; font-size:0.9rem;">Late Entries History:</strong>
                <div style="display:flex; flex-wrap:wrap; gap:5px;">
                   ${lateDatesHtml}
                </div>
             </div>
          </div>
        `;

        html += `
          <div style="margin-top:20px; padding-top:16px; border-top:1px solid #e5e7eb; display:flex; gap:10px; flex-wrap:wrap;">
            <a href="edit_employee.html?emp_id=${encodeURIComponent(emp.emp_id)}" class="btn btn-primary">Modify</a>
            <button type="button" class="btn btn-outline btn-delete-in-modal" style="color:#b91c1c; border-color:#b91c1c;" data-emp-id="${(emp.emp_id || '').replace(/"/g, '&quot;')}" data-emp-name="${(emp.full_name || emp.emp_id || '').replace(/"/g, '&quot;')}">Delete</button>
            <button type="button" class="btn btn-outline" onclick="closeEmployeeDetailModal()">Close</button>
          </div>
        `;
        content.innerHTML = html;
        content.querySelectorAll('.btn-delete-in-modal').forEach(btn => {
          btn.addEventListener('click', function () {
            const id = this.getAttribute('data-emp-id');
            const name = this.getAttribute('data-emp-name') || id;
            closeEmployeeDetailModal();
            if (id) window.deleteEmployee(id, name);
          });
        });

      } catch (error) {
        console.error("Error fetching employee details:", error);
        content.innerHTML = `<p style="color:red;">Connection error: ${error.message}</p>`;
      }
    };

    // Reveal employee password
    window.revealEmpPassword = async function (empId) {
      const adminPassword = prompt("Enter admin password to reveal employee credentials:");
      if (!adminPassword) return;

      try {
        const response = await fetch(`${API_BASE_URL}/employees/${empId}/reveal-password`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ admin_password: adminPassword })
        });

        const data = await response.json();

        if (!data.success) {
          alert("Invalid admin password: " + data.error);
          return;
        }

        const passwordDisplay = document.getElementById('emp-password-display');
        if (passwordDisplay) {
          passwordDisplay.innerHTML = `
            <div style="background:#fef2f2; padding:8px; border-radius:4px; border:1px solid #fca5a5;">
              <code style="font-family:monospace; font-weight:bold; color:#991b1b; word-break:break-all;">
                ${data.password}
              </code>
              <button class="btn btn-outline" style="font-size:0.8rem; padding:2px 8px; margin-top:4px; display:block;" onclick="location.reload()">
                Hide Password
              </button>
            </div>
          `;
        }
      } catch (error) {
        alert("Connection error: " + error.message);
        console.error(error);
      }
    };

  } catch (err) {
    console.error("CRITICAL JS ERROR:", err);
    const tb = document.querySelector("tbody[data-employees-list]");
    if (tb) tb.innerHTML = `<tr><td colspan='9' style='color:red; font-weight:bold;'>CRITICAL JS ERROR: ${err.message}</td></tr>`;
  }
  }, 1000); // End of setTimeout
});

function closeEmployeeDetailModal() {
  const modal = document.getElementById('employee-detail-modal');
  if (modal) modal.style.display = 'none';
}
