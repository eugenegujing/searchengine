/* ===== Register Page Logic ===== */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('registerForm');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!username || !password || !confirmPassword) {
      alert("Please fill in all fields.");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (data.status === "registered") {
        alert("Registration successful! Redirecting to login...");
        window.location.href = "LoginPage.html"; // redirect to login
      } else {
        alert(data.error || "Registration failed.");
      }
    } catch (err) {
      console.error(err);
      alert("An error occurred during registration.");
    }
  });
});