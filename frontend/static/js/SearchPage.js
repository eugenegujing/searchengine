/* ===== Search Page Logic ===== */

/* ---------- Load user profile from onboarding ---------- */

const profile = JSON.parse(localStorage.getItem('peterProfile') || 'null');

(function initProfileBadge() {
  if (!profile) return;
  const badge = document.getElementById('profileBadge');
  const avatar = document.getElementById('avatarInitial');
  const name   = document.getElementById('profileName');
  if (badge) {
    badge.style.display = 'flex';
    avatar.textContent = profile.displayName.charAt(0).toUpperCase();
    name.textContent   = profile.displayName;
  }
  // Pre-fill quarter filter from profile
  const qSel = document.getElementById('filterQuarter');
  if (qSel && profile.quarterTarget) qSel.value = profile.quarterTarget;
})();

/* ---------- Backend API base URL ---------- */

const API_BASE = window.location.origin;

/* ---------- Render functions ---------- */

function buildTagHTML(tags, ge) {
  let html = '';
  if (tags.includes('major'))   html += '<span class="tag tag-major">Major Req</span>';
  if (tags.includes('ge'))      html += ge.map(g => `<span class="tag tag-ge">GE ${g}</span>`).join('');
  if (tags.includes('prereq'))  html += '<span class="tag tag-prereq">Has Prereqs</span>';
  if (tags.includes('warning')) html += '<span class="tag tag-warning">Heads Up</span>';
  return html;
}

function renderCourseCard(course) {
  return `
    <div class="course-card" data-id="${course.id}">
      <div class="card-top">
        <div>
          <div class="course-code">${course.code}</div>
          <div class="course-title">${course.title}</div>
        </div>
        <div class="match-score">${course.matchScore}% match</div>
      </div>
      <div class="course-meta">
        <span>${course.instructor}</span>
        <span>${course.time}</span>
        <span>${course.location}</span>
        <span>${course.units} units</span>
        <span>${course.format}</span>
      </div>
      <div class="tags">${buildTagHTML(course.tags, course.ge)}</div>
      <div class="explanation">${course.explanation}</div>
    </div>`;
}

function renderResults(courses) {
  const list  = document.getElementById('resultsList');
  const empty = document.getElementById('emptyState');
  const count = document.getElementById('resultCount');

  if (courses.length === 0) {
    list.innerHTML = '';
    empty.style.display = 'block';
    count.textContent = '0';
    return;
  }

  empty.style.display = 'none';
  count.textContent = courses.length;
  list.innerHTML = courses.map(renderCourseCard).join('');
}

/* ---------- Search via backend API ---------- */

async function searchCourses(query, filters) {
  const spinner = document.getElementById('loadingSpinner');
  spinner.classList.add('show');

  const params = new URLSearchParams();
  if (query)           params.set('q', query);
  if (filters.quarter) params.set('quarter', filters.quarter);
  if (filters.dept)    params.set('dept', filters.dept);
  if (filters.level)   params.set('level', filters.level);
  if (filters.ge)      params.set('ge', filters.ge);
  if (filters.maxUnits && filters.maxUnits < 8)
    params.set('maxUnits', filters.maxUnits);
  params.set('sortBy', document.getElementById('sortBy').value);

  try {
    const res = await fetch(`${API_BASE}/api/search?${params.toString()}`);
    const data = await res.json();
    spinner.classList.remove('show');
    renderResults(data.courses || []);
  } catch (err) {
    console.error('Search API error:', err);
    spinner.classList.remove('show');
    renderResults([]);
  }
}

/* ---------- Gather current filter values ---------- */

function getFilters() {
  return {
    quarter:  document.getElementById('filterQuarter').value,
    dept:     document.getElementById('filterDept').value,
    level:    document.getElementById('filterLevel').value,
    ge:       document.getElementById('filterGE').value,
    time:     document.getElementById('filterTime').value,
    format:   document.getElementById('filterFormat').value,
    maxUnits: parseInt(document.getElementById('filterUnits').value)
  };
}

/* ---------- Event handlers ---------- */

// Search on Enter key
document.getElementById('searchInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    searchCourses(e.target.value.trim(), getFilters());
  }
});

// Apply filters button
function applyFilters() {
  const query = document.getElementById('searchInput').value.trim();
  searchCourses(query, getFilters());
}

// Reset filters
function resetFilters() {
  document.getElementById('filterDept').value    = '';
  document.getElementById('filterLevel').value   = '';
  document.getElementById('filterGE').value      = '';
  document.getElementById('filterTime').value    = '';
  document.getElementById('filterFormat').value  = '';
  document.getElementById('filterUnits').value   = 8;
  document.getElementById('unitsVal').textContent = '8';
  document.getElementById('searchInput').value   = '';

  // Remove active pills
  document.querySelectorAll('.pill.active').forEach(p => p.classList.remove('active'));

  renderResults([]);
  document.getElementById('emptyState').style.display = 'block';
}

// Units slider display
document.getElementById('filterUnits').addEventListener('input', e => {
  document.getElementById('unitsVal').textContent = e.target.value;
});

// Quick-filter pills
document.querySelectorAll('.pill').forEach(pill => {
  pill.addEventListener('click', () => {
    pill.classList.toggle('active');

    const filterType = pill.dataset.filter;
    const filters = getFilters();
    const query = document.getElementById('searchInput').value.trim();

    // Map pill to a quick filter action
    if (pill.classList.contains('active')) {
      switch (filterType) {
        case 'major':
          // If user has a major set, search for it
          if (profile && profile.major) {
            document.getElementById('searchInput').value = profile.major;
          }
          break;
        case 'ge':
          // If user has GE needs, pick first one
          if (profile && profile.geNeeded && profile.geNeeded.length > 0) {
            document.getElementById('filterGE').value = profile.geNeeded[0];
          }
          break;
        case 'no-prereq':
          // Search hint
          document.getElementById('searchInput').value = 'no prerequisites';
          break;
        case 'low-workload':
          document.getElementById('searchInput').value = 'lighter workload';
          break;
        case 'morning':
          document.getElementById('filterTime').value = 'morning';
          break;
        case 'online':
          document.getElementById('filterFormat').value = 'online';
          break;
      }
    }
    searchCourses(document.getElementById('searchInput').value.trim(), getFilters());
  });
});

// Sort change
document.getElementById('sortBy').addEventListener('change', () => {
  const query = document.getElementById('searchInput').value.trim();
  searchCourses(query, getFilters());
});

/* ---------- On load: show empty state or auto-search ---------- */

(function init() {
  // If the user came from onboarding with a profile, run an initial personalized search
  if (profile && profile.major) {
    searchCourses('', getFilters());
  }
})();
