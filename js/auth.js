/* Login + role-based routing - API authentication */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form[data-login]");
  if (!form) return;

  const err = document.querySelector("[data-error]");
  const empIdEl = document.querySelector("#emp_id");
  const passEl = document.querySelector("#password");
  const submitBtn = form.querySelector("button[type='submit']");

  const apiBase = 'http://localhost:5000/api';

  function showError(msg) {
    if (err) {
      err.textContent = msg || "";
      err.classList.toggle("show", !!msg);
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("");

    const emp_id = (empIdEl?.value || "").trim();
    const password = passEl?.value || "";

    if (!emp_id || !password) {
      showError("Please enter Employee ID and password.");
      return;
    }

    // Disable button during request
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Logging in...";
    }

    try {
      const response = await fetch(`${apiBase}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          emp_id: emp_id,  // Send emp_id as username field
          password: password 
        }),
      });

      console.log('Sending request with fields:', { emp_id: emp_id, password: password }); // Debug log

      let data = {};
      try {
        data = await response.json();
        console.log('Login response:', data); // Debug log
        console.log('Response status:', response.status); // Debug log
        console.log('Response headers:', response.headers); // Debug log
      } catch (_) {
        showError("Invalid response from server. Is the backend running?");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Sign In";
        }
        return;
      }

      if (!response.ok || !data.success) {
        showError(data.error || "Invalid Employee ID or password.");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Sign In";
        }
        return;
      }

      // Store user session (both localStorage and sessionStorage so panel loads after login)
      const sessionUser = {
        emp_id: data.user.emp_id,
        name: data.user.name || data.user.full_name,
        role: data.user.role || "Employee",
      };
      const sessionStr = JSON.stringify(sessionUser);
      localStorage.setItem("session_user", sessionStr);
      try {
        sessionStorage.setItem("session_user", sessionStr);
      } catch (_) {}

      // Check if user must change password
      if (data.redirect_to && data.redirect_to === 'change_password.html') {
        // Show message and redirect to change password
        if (data.message) {
          alert(data.message);
        }
        window.location.replace("change_password.html");
        return;
      }

      // Redirect based on role so admin/employee see their panel
      if ((sessionUser.role || "").toLowerCase() === "admin") {
        window.location.replace("admin_dashboard.html");
      } else {
        window.location.replace("employee_dashboard.html");
      }
    } catch (error) {
      console.error("Login error:", error);
      showError("Connection error. Ensure the backend is running (e.g. python backend/app.py) and open this page at http://localhost:5000");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign In";
      }
    }
  });
});

