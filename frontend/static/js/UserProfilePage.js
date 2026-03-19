/* ===== Onboarding Multi-Step Form ===== */

let currentStep = 1;
const totalSteps = 4;

/* ---------- Step navigation ---------- */

function showStep(n) {
  document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.step-dot').forEach(d => {
    const ds = parseInt(d.dataset.step);
    d.classList.remove('active', 'done');
    if (ds < n)  d.classList.add('done');
    if (ds === n) d.classList.add('active');
  });
  const target = document.querySelector(`.form-step[data-step="${n}"]`);
  if (target) target.classList.add('active');
  currentStep = n;
}

function nextStep() {
  if (currentStep < totalSteps) showStep(currentStep + 1);
}

function prevStep() {
  if (currentStep > 1) showStep(currentStep - 1);
}

/* ---------- Completed courses state ---------- */

const completedSet = new Set();

/* ---------- Load major courses into the grid ---------- */

function loadMajorCourses(majorId, savedCompleted) {
  const grid = document.getElementById('completedCoursesGrid');
  const hint = document.getElementById('noMajorHint');
  grid.innerHTML = '';
  completedSet.clear();

  if (!majorId) {
    hint.style.display = '';
    return;
  }
  hint.style.display = 'none';

  fetch(`/api/major-courses/${encodeURIComponent(majorId)}`)
    .then(res => res.json())
    .then(data => {
      const sections = [
        { key: 'core', label: 'Core Requirements', open: true },
        { key: 'electives', label: 'Electives', open: false },
        { key: 'ge', label: 'GE Requirements', open: false },
      ];

      let hasAny = false;
      sections.forEach(sec => {
        const courses = data[sec.key] || [];
        if (!courses.length) return;
        hasAny = true;

        const section = document.createElement('div');
        section.className = 'cc-section';

        const header = document.createElement('div');
        header.className = 'cc-section-header' + (sec.open ? ' open' : '');
        header.innerHTML = `<span class="cc-toggle">${sec.open ? '\u25BC' : '\u25B6'}</span> ${sec.label} <span class="cc-count">(${courses.length})</span>`;

        const body = document.createElement('div');
        body.className = 'cc-section-body';
        if (!sec.open) body.style.display = 'none';

        header.addEventListener('click', () => {
          const isOpen = body.style.display !== 'none';
          body.style.display = isOpen ? 'none' : '';
          header.querySelector('.cc-toggle').textContent = isOpen ? '\u25B6' : '\u25BC';
          header.classList.toggle('open', !isOpen);
        });

        courses.forEach(c => {
          const card = document.createElement('div');
          card.className = 'course-chip';
          card.dataset.courseId = c.course_id;

          // If this course was previously saved as completed, mark it
          if (savedCompleted && savedCompleted.has(c.course_id)) {
            card.classList.add('completed');
            completedSet.add(c.course_id);
          }

          card.innerHTML = `<span class="cc-code">${c.code}</span><span class="cc-icon"></span>`;
          card.title = c.title;
          card.addEventListener('click', () => {
            if (card.classList.contains('completed')) {
              card.classList.remove('completed');
              completedSet.delete(c.course_id);
            } else {
              card.classList.add('completed');
              completedSet.add(c.course_id);
            }
          });
          body.appendChild(card);
        });

        section.appendChild(header);
        section.appendChild(body);
        grid.appendChild(section);
      });

      if (!hasAny) {
        hint.textContent = 'No required courses found for this major.';
        hint.style.display = '';
      }
    })
    .catch(err => console.error('Failed to load major courses:', err));
}

/* ---------- Major dropdown change ---------- */

document.getElementById('majorSelect').addEventListener('change', function () {
  loadMajorCourses(this.value, null);
});

/* ---------- Chip toggle (GE categories) ---------- */

document.querySelectorAll('.chip-group .chip').forEach(chip => {
  chip.addEventListener('click', () => chip.classList.toggle('selected'));
});

/* ---------- Populate form from saved profile ---------- */

function populateProfile(profile) {
  // Step 1: Basic Info
  if (profile.displayName) {
    document.getElementById('displayName').value = profile.displayName;
  }
  if (profile.standing) {
    const radio = document.querySelector(`input[name="standing"][value="${profile.standing}"]`);
    if (radio) radio.checked = true;
  }
  if (profile.college) {
    document.getElementById('college').value = profile.college;
  }

  // Step 2: Academic Goals
  if (profile.major) {
    document.getElementById('majorSelect').value = profile.major;
  }
  if (profile.minor) {
    document.getElementById('minorInput').value = profile.minor;
  }
  if (profile.priority) {
    const radio = document.querySelector(`input[name="priority"][value="${profile.priority}"]`);
    if (radio) radio.checked = true;
  }
  if (profile.geNeeded && profile.geNeeded.length) {
    profile.geNeeded.forEach(ge => {
      const chip = document.querySelector(`#geChips .chip[data-value="${ge}"]`);
      if (chip) chip.classList.add('selected');
    });
  }

  // Step 3: Preferences
  if (profile.preferredTime) {
    const radio = document.querySelector(`input[name="timeSlot"][value="${profile.preferredTime}"]`);
    if (radio) radio.checked = true;
  }
  if (profile.workload) {
    const radio = document.querySelector(`input[name="workload"][value="${profile.workload}"]`);
    if (radio) radio.checked = true;
  }
  if (profile.courseFormat) {
    const radio = document.querySelector(`input[name="format"][value="${profile.courseFormat}"]`);
    if (radio) radio.checked = true;
  }
  if (profile.commuter) {
    const radio = document.querySelector(`input[name="commuter"][value="${profile.commuter}"]`);
    if (radio) radio.checked = true;
  }

  // Step 4: Quarter & Units
  if (profile.quarterTarget) {
    document.getElementById('quarterTarget').value = profile.quarterTarget;
  }
  if (profile.maxUnits) {
    document.getElementById('maxUnits').value = profile.maxUnits;
  }

  // Load major courses with saved completed courses pre-checked
  if (profile.major) {
    const saved = new Set(profile.completedCourses || []);
    loadMajorCourses(profile.major, saved);
  }
}

/* ---------- Init: load majors then load saved profile ---------- */

(function init() {
  const username = localStorage.getItem("loggedInUser");

  fetch('/api/majors')
    .then(res => res.json())
    .then(majors => {
      const sel = document.getElementById('majorSelect');
      majors.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.name;
        sel.appendChild(opt);
      });

      // After majors are loaded, fetch saved profile
      if (username) {
        return fetch(`/api/profile?username=${encodeURIComponent(username)}`);
      }
    })
    .then(res => {
      if (res && res.ok) return res.json();
    })
    .then(profile => {
      if (profile && !profile.error) {
        populateProfile(profile);
      }
    })
    .catch(err => console.error('Failed to load profile:', err));
})();

/* ---------- Collect & save profile ---------- */

function gatherProfile() {
  const standing = document.querySelector('input[name="standing"]:checked');
  const priority = document.querySelector('input[name="priority"]:checked');
  const timeSlot = document.querySelector('input[name="timeSlot"]:checked');
  const workload = document.querySelector('input[name="workload"]:checked');
  const format   = document.querySelector('input[name="format"]:checked');
  const commuter = document.querySelector('input[name="commuter"]:checked');

  const geNeeded = [];
  document.querySelectorAll('#geChips .chip.selected').forEach(c => {
    geNeeded.push(c.dataset.value);
  });

  return {
    displayName:      document.getElementById('displayName').value.trim() || 'Student',
    standing:         standing ? standing.value : '',
    college:          document.getElementById('college').value,
    major:            document.getElementById('majorSelect').value,
    minor:            document.getElementById('minorInput').value.trim(),
    priority:         priority ? priority.value : 'degree',
    geNeeded:         geNeeded,
    preferredTime:    timeSlot ? timeSlot.value : 'any',
    workload:         workload ? workload.value : 'moderate',
    courseFormat:      format   ? format.value   : 'any',
    commuter:         commuter ? commuter.value  : 'no',
    completedCourses: Array.from(completedSet),
    quarterTarget:    document.getElementById('quarterTarget').value,
    maxUnits:         parseInt(document.getElementById('maxUnits').value)
  };
}

function submitProfile() {
  const profile = gatherProfile();
  const username = localStorage.getItem("loggedInUser");

  fetch('/api/profile', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: username,
      profile: profile
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log('Profile saved:', data);
    window.location.href = 'SearchPage.html';
  });
}
