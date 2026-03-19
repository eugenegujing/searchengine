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

/* ---------- DOM references ---------- */

const searchInput    = document.getElementById('searchInput');
const resultsList    = document.getElementById('resultsList');
const resultCount    = document.getElementById('resultCount');
const emptyState     = document.getElementById('emptyState');
const loadingSpinner = document.getElementById('loadingSpinner');
const sortBySelect   = document.getElementById('sortBy');

/* ---------- Live search on typing ---------- */

let searchTimer = null;

if (searchInput) {
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => applyFilters(), 300);
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      clearTimeout(searchTimer);
      applyFilters();
    }
  });
}

if (sortBySelect) {
  sortBySelect.addEventListener('change', () => applyFilters());
}

/* ---------- Quick-filter pill clicks ---------- */

let activePill = null;

document.querySelectorAll('.pill').forEach(pill => {
  const filter = pill.dataset.filter;

  pill.addEventListener('click', () => {
    // Toggle: click same pill again to deactivate
    if (activePill === filter) {
      pill.classList.remove('active');
      activePill = null;
      applyFilters();
      return;
    }

    // Deactivate previous pill
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activePill = filter;
    applyFilters();
  });
});

/* ---------- Apply filters → call /api/search ---------- */

function applyFilters() {
  const q        = (searchInput?.value || '').trim();
  const quarter  = document.getElementById('filterQuarter')?.value || '';
  const dept     = document.getElementById('filterDept')?.value || '';
  const level    = document.getElementById('filterLevel')?.value || '';
  const ge       = document.getElementById('filterGE')?.value || '';
  const maxUnits = document.getElementById('filterUnits')?.value || '';
  const sortBy   = sortBySelect?.value || 'relevance';

  const params = new URLSearchParams();
  if (q)        params.set('q', q);
  if (quarter)  params.set('quarter', quarter);
  if (dept)     params.set('dept', dept);
  if (level)    params.set('level', level);
  if (ge)       params.set('ge', ge);
  if (maxUnits && parseInt(maxUnits) < 8) params.set('maxUnits', maxUnits);
  params.set('sortBy', sortBy);
  if (username) params.set('username', username);
  if (activePill) params.set('pill', activePill);

  // Show loading, hide empty state
  loadingSpinner.classList.add('show');
  emptyState.style.display = 'none';
  resultsList.innerHTML = '';

  fetch(`/api/search?${params.toString()}`)
    .then(res => res.json())
    .then(data => {
      loadingSpinner.classList.remove('show');
      const courses = data.courses || [];
      resultCount.textContent = courses.length;

      if (courses.length === 0) {
        emptyState.style.display = 'block';
        emptyState.querySelector('h3').textContent = 'No courses found';
        emptyState.querySelector('p').textContent  = 'Try adjusting your filters or search terms.';
        return;
      }

      emptyState.style.display = 'none';
      courses.forEach(c => resultsList.appendChild(buildCourseCard(c)));
    })
    .catch(err => {
      loadingSpinner.classList.remove('show');
      console.error('Search error:', err);
      resultCount.textContent = '0';
      emptyState.style.display = 'block';
      emptyState.querySelector('h3').textContent = 'Something went wrong';
      emptyState.querySelector('p').textContent  = 'Could not reach the server. Is it running?';
    });
}

/* ---------- Build a course card ---------- */

function buildCourseCard(c) {
  const card = document.createElement('div');
  card.className = 'course-card';

  let tagsHtml = '';
  if (c.ge && c.ge.length > 0) {
    c.ge.forEach(g => {
      tagsHtml += `<span class="tag tag-ge">GE ${g}</span>`;
    });
  }
  if (c.level === 'upper') {
    tagsHtml += '<span class="tag tag-info">Upper Div</span>';
  }
  else if (c.level === 'graduate') {
    tagsHtml += '<span class="tag tag-info">Graduate</span>';
  }

  card.innerHTML = `
    <div class="card-top">
      <div>
        <div class="course-code">${c.code}</div>
        <div class="course-title">${c.title}</div>
      </div>
      <div class="match-score">${c.matchScore}% match</div>
    </div>
    <div class="course-meta">
      <span>${c.units} units</span>
      <span>${c.time}</span>
      <span>${c.location}</span>
    </div>
    ${tagsHtml ? `<div class="tags">${tagsHtml}</div>` : ''}
    ${c.explanation ? `<div class="explanation">${c.explanation}</div>` : ''}
  `;

  return card;
}

/* ---------- Reset filters ---------- */

function resetFilters() {
  if (searchInput) searchInput.value = '';
  activePill = null;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));

  const ids = ['filterQuarter', 'filterDept', 'filterLevel', 'filterGE', 'filterTime', 'filterFormat'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.selectedIndex = 0;
  });

  const filterUnits = document.getElementById('filterUnits');
  if (filterUnits) {
    filterUnits.value = 8;
    if (unitsVal) unitsVal.textContent = '8';
  }

  resultsList.innerHTML = '';
  resultCount.textContent = '0';
  emptyState.style.display = 'block';
  emptyState.querySelector('h3').textContent = 'Start searching for courses';
  emptyState.querySelector('p').textContent  = 'Type a query above or use the filters to find courses that fit your schedule and goals.';
}

/* ---------- Auto-search on page load ---------- */
applyFilters();