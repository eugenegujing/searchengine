/* ===== Login Page Logic ===== */

document.addEventListener('DOMContentLoaded', () => {
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const loginBtn = document.querySelector('.btn-primary');

  loginBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
      alert("Please enter both username and password.");
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = "Logging in...";

    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (data.status === "success") {
        alert("Login successful!");
        window.location.href = "UserProfilePage.html"; // ← Redirect to user profile
      } else {
        alert(data.error || "Invalid username or password.");
      }

    } catch (err) {
      console.error(err);
      alert("An error occurred during login.");
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = "Login";
    }
  });
});