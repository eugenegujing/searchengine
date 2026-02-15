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

/* ---------- Demo course data (replace with AJAX) ---------- */

const DEMO_COURSES = [
  {
    id: 'ICS31',
    code: 'I&C SCI 31',
    title: 'Introduction to Programming',
    dept: 'I&C SCI',
    level: 'lower',
    units: 4,
    instructor: 'Kay, R.',
    time: 'MWF 10:00-10:50am',
    location: 'SSH 100',
    format: 'in-person',
    ge: [],
    tags: ['major'],
    matchScore: 95,
    explanation: 'Required for your ICS/CS major. No prerequisites — a great starting point.'
  },
  {
    id: 'ICS32',
    code: 'I&C SCI 32',
    title: 'Programming with Software Libraries',
    dept: 'I&C SCI',
    level: 'lower',
    units: 4,
    instructor: 'Thornton, A.',
    time: 'TuTh 2:00-3:20pm',
    location: 'ALP 1300',
    format: 'in-person',
    ge: [],
    tags: ['major', 'prereq'],
    matchScore: 90,
    explanation: 'Builds on ICS 31. Prerequisite: ICS 31 with grade C or better.'
  },
  {
    id: 'WRITING40',
    code: 'WRITING 40',
    title: 'Intro to Writing & Rhetoric',
    dept: 'WRITING',
    level: 'lower',
    units: 4,
    instructor: 'Garcia, M.',
    time: 'MWF 11:00-11:50am',
    location: 'HH 112',
    format: 'in-person',
    ge: ['Ia'],
    tags: ['ge'],
    matchScore: 82,
    explanation: 'Satisfies GE Ia (Lower Division Writing). Moderate workload with weekly essays.'
  },
  {
    id: 'MATH2A',
    code: 'MATH 2A',
    title: 'Single-Variable Calculus I',
    dept: 'MATH',
    level: 'lower',
    units: 4,
    instructor: 'Chen, L.',
    time: 'MWF 9:00-9:50am',
    location: 'MSTB 120',
    format: 'in-person',
    ge: ['Va'],
    tags: ['major', 'ge'],
    matchScore: 88,
    explanation: 'Satisfies GE Va and is required for most STEM majors. Morning section.'
  },
  {
    id: 'ANTHRO2A',
    code: 'ANTHRO 2A',
    title: 'Intro to Sociocultural Anthropology',
    dept: 'ANTHRO',
    level: 'lower',
    units: 4,
    instructor: 'Dominguez, V.',
    time: 'TuTh 11:00-12:20pm',
    location: 'SSL 228',
    format: 'in-person',
    ge: ['III', 'VII'],
    tags: ['ge'],
    matchScore: 75,
    explanation: 'Satisfies GE III and GE VII. No prerequisites, lighter workload.'
  },
  {
    id: 'COMPSCI161',
    code: 'COMPSCI 161',
    title: 'Design and Analysis of Algorithms',
    dept: 'COMPSCI',
    level: 'upper',
    units: 4,
    instructor: 'Goodrich, M.',
    time: 'TuTh 3:30-4:50pm',
    location: 'DBH 1500',
    format: 'in-person',
    ge: [],
    tags: ['major'],
    matchScore: 92,
    explanation: 'Core upper-division CS course. Prerequisites: ICS 46, MATH 2B, ICS 6D.'
  },
  {
    id: 'ARTVIS20',
    code: 'ART VIS 20',
    title: 'Foundations in Digital Art',
    dept: 'ART',
    level: 'lower',
    units: 4,
    instructor: 'Park, S.',
    time: 'MW 2:00-4:50pm',
    location: 'CAC 2015',
    format: 'in-person',
    ge: ['IV'],
    tags: ['ge'],
    matchScore: 68,
    explanation: 'Satisfies GE IV (Arts & Humanities). Fun elective, no prerequisites.'
  },
  {
    id: 'PSYCH9A',
    code: 'PSYCH 9A',
    title: 'Psychology Fundamentals',
    dept: 'PSYCH',
    level: 'lower',
    units: 4,
    instructor: 'Hagedorn, J.',
    time: 'MWF 1:00-1:50pm',
    location: 'PCB 1100',
    format: 'in-person',
    ge: ['III'],
    tags: ['ge'],
    matchScore: 72,
    explanation: 'Satisfies GE III. Large lecture format, manageable workload.'
  },
  {
    id: 'IN4MATX43',
    code: 'IN4MATX 43',
    title: 'Introduction to Software Engineering',
    dept: 'IN4MATX',
    level: 'lower',
    units: 4,
    instructor: 'Ziv, H.',
    time: 'TuTh 9:30-10:50am',
    location: 'ICS 174',
    format: 'in-person',
    ge: [],
    tags: ['major'],
    matchScore: 85,
    explanation: 'Recommended for ICS/SE majors. Covers SDLC, teamwork, testing.'
  },
  {
    id: 'PHYSICS7C',
    code: 'PHYSICS 7C',
    title: 'Classical Physics',
    dept: 'PHYSICS',
    level: 'lower',
    units: 4,
    instructor: 'Feng, W.',
    time: 'MWF 8:00-8:50am',
    location: 'RH 104',
    format: 'in-person',
    ge: ['II'],
    tags: ['ge', 'warning'],
    matchScore: 60,
    explanation: 'Satisfies GE II. Warning: early morning section with heavy workload.'
  }
];

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

/* ---------- Search via AJAX (stub) ---------- */

/**
 * Replace this function body with a real fetch() call to your backend.
 *
 * Example:
 *
 *   async function searchCourses(query, filters) {
 *     const spinner = document.getElementById('loadingSpinner');
 *     spinner.classList.add('show');
 *
 *     const params = new URLSearchParams({
 *       q:        query,
 *       quarter:  filters.quarter,
 *       dept:     filters.dept,
 *       level:    filters.level,
 *       ge:       filters.ge,
 *       time:     filters.time,
 *       format:   filters.format,
 *       maxUnits: filters.maxUnits
 *     });
 *
 *     // Include the user profile so the backend can personalize ranking
 *     const res = await fetch(`/api/search?${params}`, {
 *       method: 'POST',
 *       headers: { 'Content-Type': 'application/json' },
 *       body: JSON.stringify({ profile })
 *     });
 *     const data = await res.json();
 *
 *     spinner.classList.remove('show');
 *     renderResults(data.courses);
 *   }
 */

function searchCourses(query, filters) {
  const spinner = document.getElementById('loadingSpinner');
  spinner.classList.add('show');

  // Simulate AJAX delay
  setTimeout(() => {
    let results = [...DEMO_COURSES];

    // Client-side filtering (demo only — real filtering happens on the server)
    if (query) {
      const q = query.toLowerCase();
      results = results.filter(c =>
        c.title.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        c.dept.toLowerCase().includes(q) ||
        c.explanation.toLowerCase().includes(q) ||
        c.ge.some(g => g.toLowerCase().includes(q))
      );
    }
    if (filters.dept)     results = results.filter(c => c.dept === filters.dept);
    if (filters.level)    results = results.filter(c => c.level === filters.level);
    if (filters.ge)       results = results.filter(c => c.ge.includes(filters.ge));
    if (filters.format && filters.format !== '')
      results = results.filter(c => c.format === filters.format);
    if (filters.maxUnits && filters.maxUnits < 8)
      results = results.filter(c => c.units <= filters.maxUnits);

    // Sort
    const sortBy = document.getElementById('sortBy').value;
    if (sortBy === 'match')      results.sort((a, b) => b.matchScore - a.matchScore);
    if (sortBy === 'units-asc')  results.sort((a, b) => a.units - b.units);
    if (sortBy === 'units-desc') results.sort((a, b) => b.units - a.units);
    if (sortBy === 'dept')       results.sort((a, b) => a.dept.localeCompare(b.dept));

    spinner.classList.remove('show');
    renderResults(results);
  }, 400);
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
