// /* ===== Search Page Logic ===== */

/* ===== Search Page Logic ===== */

/* ---------- Load or fetch user profile ---------- */

let profile = JSON.parse(localStorage.getItem('peterProfile') || 'null');
const username = localStorage.getItem('loggedInUser');

function initProfileBadge(profile) {
  if (!profile) return;

  const badge     = document.getElementById('profileBadge');
  const avatar    = document.getElementById('avatarInitial');
  const name      = document.getElementById('profileName');
  const dropdown  = document.getElementById('profileDropdown');
  const logoutBtn = document.getElementById('logoutBtn');

  // Show badge
  badge.style.display = 'flex';
  avatar.textContent  = profile.displayName.charAt(0).toUpperCase();
  name.textContent    = profile.displayName;

  // Toggle dropdown on click
  badge.addEventListener('click', (e) => {
    e.stopPropagation(); // prevent triggering document click
    dropdown.style.display = dropdown.style.display === 'flex' ? 'none' : 'flex';
  });

  // Close dropdown if clicking outside
  document.addEventListener('click', () => {
    dropdown.style.display = 'none';
  });

  // Logout functionality
  logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('peterProfile');
    localStorage.removeItem('loggedInUser');
    window.location.href = 'LoginPage.html';
  });

  // Pre-fill quarter filter
  const qSel = document.getElementById('filterQuarter');
  if (qSel && profile.quarterTarget) qSel.value = profile.quarterTarget;
}

/* ---------- Initialize profile badge ---------- */

if (profile) {
  // profile exists in localStorage
  initProfileBadge(profile);
} else if (username) {
  // fetch profile from backend
  fetch(`/api/profile?username=${encodeURIComponent(username)}`)
    .then(res => res.json())
    .then(data => {
      profile = data;
      localStorage.setItem('peterProfile', JSON.stringify(profile));
      initProfileBadge(profile);
    })
    .catch(err => {
      console.error('Failed to fetch profile:', err);
      // fallback: show default badge
      localStorage.removeItem('loggedInUser');
      window.location.href = 'LoginPage.html';
    });
} else {
  // no logged-in user → redirect to login
  window.location.href = 'LoginPage.html';
}

/* ---------- Other SearchPage logic (filters, search, etc.) ---------- */

// Example: filter range display
const unitsRange = document.getElementById('filterUnits');
const unitsVal   = document.getElementById('unitsVal');
if (unitsRange && unitsVal) {
  unitsVal.textContent = unitsRange.value;
  unitsRange.addEventListener('input', () => {
    unitsVal.textContent = unitsRange.value;
  });
}

// Add more search/filter initialization logic here...
// /* ---------- Load user profile from onboarding ---------- */

// const profile = JSON.parse(localStorage.getItem('peterProfile') || 'null');

// (function initProfileBadge() {
//   if (!profile) return;

//   const badge    = document.getElementById('profileBadge');
//   const avatar   = document.getElementById('avatarInitial');
//   const name     = document.getElementById('profileName');
//   const dropdown = document.getElementById('profileDropdown');
//   const logoutBtn = document.getElementById('logoutBtn');

//   badge.style.display = 'flex';
//   avatar.textContent = profile.displayName.charAt(0).toUpperCase();
//   name.textContent   = profile.displayName;

//   // Toggle dropdown on badge click
//   badge.addEventListener('click', () => {
//     dropdown.style.display = dropdown.style.display === 'flex' ? 'none' : 'flex';
//   });

//   // Close dropdown if clicking outside
//   document.addEventListener('click', (e) => {
//     if (!badge.contains(e.target)) {
//       dropdown.style.display = 'none';
//     }
//   });

//   // Logout functionality
//   logoutBtn.addEventListener('click', () => {
//     localStorage.removeItem('peterProfile');
//     window.location.href = 'LoginPage.html';
//   });

//   // Pre-fill quarter filter from profile
//   const qSel = document.getElementById('filterQuarter');
//   if (qSel && profile.quarterTarget) qSel.value = profile.quarterTarget;
// })();