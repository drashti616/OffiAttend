/* Shared UI helpers + demo data (frontend-only) */
const STORAGE_KEY = "office_attendance_demo_v2";
const API_BASE_URL = 'http://localhost:5000/api';

function getState() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function setState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function seedIfEmpty() {
  if (getState()) return;
  setState({
    users: [],
    employees: [],
    attendance: [],
    leaves: []
  });
}

const SESSION_KEY = "session_user";

function escapeHtml(s) {
  if (s == null) return '';
  const t = String(s);
  return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function currentUser() {
  let u = localStorage.getItem(SESSION_KEY);
  if (!u && typeof sessionStorage !== "undefined") u = sessionStorage.getItem(SESSION_KEY);
  if (!u) return null;
  try { return JSON.parse(u); } catch { return null; }
}

function requireAuth() {
  seedIfEmpty();
  const user = currentUser();
  if (!user || !user.emp_id) {
    // Clear any cached data
    localStorage.clear();
    sessionStorage.clear();
    
    // Prevent back button
    window.history.pushState(null, null, window.location.href);
    window.onpopstate = function() {
      window.history.pushState(null, null, window.location.href);
    };
    
    window.location.href = "login.html";
    return null;
  }
  
  // Setup back button prevention for authenticated users
  window.history.pushState(null, null, window.location.href);
  window.onpopstate = function() {
    // If user tries to go back, check if still authenticated
    const currentUser_check = currentUser();
    if (!currentUser_check || !currentUser_check.emp_id) {
      window.location.href = "login.html";
    } else {
      window.history.pushState(null, null, window.location.href);
    }
  };
  
  return user;
}

function setNavbarUser() {
  const user = currentUser();
  document.querySelectorAll("[data-username]").forEach(el => { if (user) el.textContent = user.name || user.emp_id; });
  document.querySelectorAll("[data-userrole]").forEach(el => { if (user) el.textContent = user.role || "User"; });
}
function logout() {
  // Clear all session data
  localStorage.removeItem(SESSION_KEY);
  try { sessionStorage.removeItem(SESSION_KEY); } catch (e) { }
  
  // Clear all localStorage to prevent any cached data
  localStorage.clear();
  
  // Prevent back button by replacing history
  window.history.pushState(null, null, window.location.href);
  window.onpopstate = function() {
    window.history.pushState(null, null, window.location.href);
  };
  
  // Redirect to login
  window.location.href = "login.html";
  
  // Prevent any further navigation
  setTimeout(() => {
    window.location.href = "login.html";
  }, 100);
}

function qs(sel, root = document) { return root.querySelector(sel); }
function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

function fmtBadge(status) {
  const s = (status || "").toLowerCase();
  if (s === "present") return `<span class="badge badge-present">Present</span>`;
  if (s === "absent") return `<span class="badge badge-absent">Absent</span>`;
  if (s === "leave") return `<span class="badge badge-leave">Leave</span>`;
  if (s === "late") return `<span class="badge badge-late">Late</span>`;
  if (s === "approved") return `<span class="badge badge-approved">Approved</span>`;
  if (s === "rejected") return `<span class="badge badge-rejected">Rejected</span>`;
  if (s === "pending") return `<span class="badge badge-pending">Pending</span>`;
  return `<span class="badge">${status || "—"}</span>`;
}

function downloadCsv(filename, rows) {
  const escape = (v) => {
    const s = String(v ?? "");
    // Replace problematic characters with proper CSV format
    if (/[,"\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
    // Convert any non-printable characters to spaces or proper format
    return s.replace(/[^\x20-\x7E]/g, (match) => {
      const charCode = match.charCodeAt(0);
      // Allow standard printable ASCII characters
      if (charCode >= 32 && charCode <= 126) {
        return match;
      }
      // Replace other characters with space or remove
      return charCode === 8212 || charCode === 8213 ? '—' : ' '; // Replace em-dash with proper dash, others with space
    });
  };
  const csv = rows.map(r => r.map(escape).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function downloadPdf(filename, rows) {
  const { jsPDF } = window.jspdf || {};
  
  if (!jsPDF) {
    alert("PDF export requires jsPDF library. Please add: <script src=\"https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js\"></script>");
    return;
  }

  try {
    const doc = new jsPDF();
    
    // Add title
    doc.setFontSize(16);
    doc.text("Attendance Report", 105, 20, { align: 'center' });
    
    // Prepare table data
    const headers = ["Emp ID", "Name", "Date", "In Time", "Out Time", "Status"];
    const data = rows.map(r => [r.emp_id, r.name, r.date || r.att_date, r.entry_time || r.in_time, r.exit_time || r.out_time, r.status]);
    
    // Add headers
    let yPosition = 40;
    doc.setFontSize(12);
    doc.setFont(undefined, 'bold');
    headers.forEach((header, index) => {
      doc.text(header, 20, yPosition, { align: 'left' });
      yPosition += 10;
    });
    
    // Add data rows
    doc.setFont(undefined, 'normal');
    data.forEach((row) => {
      let xPosition = 20;
      row.forEach((cell, index) => {
        doc.text(cell || '—', xPosition, yPosition, { align: 'left' });
        xPosition += 100; // Column width
      });
      yPosition += 8;
    });
    
    // Add footer
    doc.setFontSize(10);
    doc.text(`Generated on ${new Date().toLocaleString()}`, 105, yPosition + 20, { align: 'center' });
    
    // Save the PDF
    doc.save(filename);
  } catch (error) {
    console.error('PDF export error:', error);
    alert('Failed to generate PDF. Please try again.');
  }
}

// Sidebar Component Loader
async function loadSidebar() {
  const container = document.getElementById('sidebar-container');
  if (!container) return;

  try {
    const response = await fetch('components/sidebar.html');
    if (!response.ok) throw new Error('Failed to fetch sidebar');
    const html = await response.text();
    container.innerHTML = html;

    // Initialize mobile menu after sidebar is loaded
    initMobileMenu();

    // Inject dynamic nav links
    if (window.OfficeApp && typeof window.OfficeApp.renderNav === 'function') {
      window.OfficeApp.renderNav();
    }

    setNavbarUser();

    const logoutBtn = container.querySelector("[data-logout]");
    if (logoutBtn) logoutBtn.addEventListener("click", () => logout());

    const mainContent = document.querySelector('.main-content');
    if (mainContent && !mainContent.querySelector('.layout-topbar')) {
      const topbar = document.createElement('header');
      topbar.className = 'layout-topbar';
      topbar.setAttribute('role', 'banner');
      mainContent.insertBefore(topbar, mainContent.firstChild);
    }
    if (mainContent && !mainContent.querySelector('.layout-bottombar')) {
      const bottombar = document.createElement('footer');
      bottombar.className = 'layout-bottombar';
      bottombar.setAttribute('role', 'contentinfo');
      bottombar.innerHTML = '<div class="layout-bottombar-inner">&copy; ' + new Date().getFullYear() + ' OffiAttend. All rights reserved.</div>';
      mainContent.appendChild(bottombar);
    }

    // Make sidebar visible immediately after loading
    const sidebar = container.querySelector('.side-panel');
    if (sidebar) {
      sidebar.style.opacity = '1';
      sidebar.style.visibility = 'visible';
    }

    // Dispatch event to notify sidebar is loaded
    document.dispatchEvent(new CustomEvent('sidebarLoaded'));
    return true;
  } catch (error) {
    console.error('Error loading sidebar:', error);
    return false;
  }
}

// Mobile Menu Toggle Functionality
function initMobileMenu() {
  const toggle = document.querySelector('.mobile-menu-toggle');
  const sidebar = document.querySelector('.side-panel');
  const overlay = document.querySelector('.mobile-overlay');

  if (!toggle || !sidebar || !overlay) return;

  // Toggle menu
  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');
    document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
  });

  // Close on overlay click
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  });

  // Close on navigation link/button click (mobile)
  const navLinks = sidebar.querySelectorAll('.nav-links a, .nav-item, .nav-item-btn');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 768) {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });

  // Close on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('mobile-open')) {
      sidebar.classList.remove('mobile-open');
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  });
}

function checkApiHealth() {
  const base = 'http://localhost:5000';
  fetch(base + '/api/health').then(r => r.json()).then(d => {
    if (d && d.status === 'ok' && d.db_ok === false) {
      let banner = document.getElementById('api-db-banner');
      if (!banner) {
        banner = document.createElement('div');
        banner.id = 'api-db-banner';
        banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;background:#b91c1c;color:#fff;padding:10px 20px;text-align:center;font-size:14px;';
        banner.innerHTML = 'Database not connected. Start <strong>MySQL</strong>, then run: <code style="background:rgba(0,0,0,0.2);padding:2px 6px;">python backend/init_db.py</code> to create the database.';
        document.body.appendChild(banner);
      }
    }
  }).catch(() => { });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    loadSidebar();
    checkApiHealth();
  });
} else {
  loadSidebar();
  checkApiHealth();
}

window.OfficeApp = {
  API_BASE_URL,
  getState, setState, seedIfEmpty,
  currentUser, requireAuth, setNavbarUser, logout,
  qs, qsa, fmtBadge, downloadCsv,
  loadSidebar
};



// ── GLOBAL SECURITY: Enforce authentication on all pages ──────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Check if page requires authentication
  const body = document.body;
  const requiresAuth = body.getAttribute('data-requires-auth') === 'true';
  
  if (requiresAuth) {
    const user = currentUser();
    if (!user || !user.emp_id) {
      // Not authenticated - redirect to login
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = 'login.html';
      return;
    }
    
    // Setup back button prevention
    window.history.pushState(null, null, window.location.href);
    window.onpopstate = function() {
      const user_check = currentUser();
      if (!user_check || !user_check.emp_id) {
        window.location.href = 'login.html';
      } else {
        window.history.pushState(null, null, window.location.href);
      }
    };
  }
});

// ── Prevent caching of authenticated pages ────────────────────────────────
// This ensures browser doesn't cache sensitive pages
if (document.body.getAttribute('data-requires-auth') === 'true') {
  // Disable caching for authenticated pages
  if ('caches' in window) {
    caches.keys().then(names => {
      names.forEach(name => {
        caches.delete(name);
      });
    });
  }
}
