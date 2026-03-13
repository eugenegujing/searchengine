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

        // store who logged in
        localStorage.setItem("loggedInUser", username);

        if (data.profile_completed) {
            // fetch saved profile from backend
            fetch(`/api/profile?username=${username}`)
            .then(res => res.json())
            .then(profileData => {
                localStorage.setItem('peterProfile', JSON.stringify(profileData));
                window.location.href = "SearchPage.html";
                });
        } 
        else {
            window.location.href = "UserProfilePage.html";
        }
      } 
      else {
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