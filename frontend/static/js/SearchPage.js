/* ===== Search Page Logic ===== */

/* ---------- Load user profile from onboarding ---------- */

const profile = JSON.parse(localStorage.getItem('peterProfile') || 'null');

(function initProfileBadge() {
  if (!profile) return;

  const badge    = document.getElementById('profileBadge');
  const avatar   = document.getElementById('avatarInitial');
  const name     = document.getElementById('profileName');
  const dropdown = document.getElementById('profileDropdown');
  const logoutBtn = document.getElementById('logoutBtn');

  badge.style.display = 'flex';
  avatar.textContent = profile.displayName.charAt(0).toUpperCase();
  name.textContent   = profile.displayName;

  // Toggle dropdown on badge click
  badge.addEventListener('click', () => {
    dropdown.style.display = dropdown.style.display === 'flex' ? 'none' : 'flex';
  });

  // Close dropdown if clicking outside
  document.addEventListener('click', (e) => {
    if (!badge.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });

  // Logout functionality
  logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('peterProfile');
    window.location.href = 'LoginPage.html';
  });

  // Pre-fill quarter filter from profile
  const qSel = document.getElementById('filterQuarter');
  if (qSel && profile.quarterTarget) qSel.value = profile.quarterTarget;
})();