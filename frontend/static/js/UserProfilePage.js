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

/* ---------- Chip toggle (GE categories) ---------- */

document.querySelectorAll('.chip-group .chip').forEach(chip => {
  chip.addEventListener('click', () => chip.classList.toggle('selected'));
});

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

  const completed = document.getElementById('completedCourses').value
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  return {
    displayName:      document.getElementById('displayName').value.trim() || 'Student',
    standing:         standing ? standing.value : '',
    college:          document.getElementById('college').value,
    major:            document.getElementById('majorInput').value.trim(),
    minor:            document.getElementById('minorInput').value.trim(),
    priority:         priority ? priority.value : 'degree',
    geNeeded:         geNeeded,
    preferredTime:    timeSlot ? timeSlot.value : 'any',
    workload:         workload ? workload.value : 'moderate',
    courseFormat:      format   ? format.value   : 'any',
    commuter:         commuter ? commuter.value  : 'no',
    completedCourses: completed,
    quarterTarget:    document.getElementById('quarterTarget').value,
    maxUnits:         parseInt(document.getElementById('maxUnits').value)
  };
}

function submitProfile() {
  const profile = gatherProfile();

  // Persist to localStorage so the search page can read it
  localStorage.setItem('peterProfile', JSON.stringify(profile));

  /*
   * ============================================================
   * AJAX hook — replace the URL below with your real API endpoint
   * once the backend is ready. The profile object is sent as JSON.
   * ============================================================
   *
   * Example with fetch():
   *
   * fetch('/api/profile', {
   *   method: 'POST',
   *   headers: { 'Content-Type': 'application/json' },
   *   body: JSON.stringify(profile)
   * })
   * .then(res => res.json())
   * .then(data => {
   *   console.log('Profile saved on server:', data);
   *   window.location.href = 'SearchPage.html';
   * })
   * .catch(err => console.error('Failed to save profile:', err));
   *
   * For now we just redirect immediately:
   */

  console.log('Profile saved to localStorage:', profile);
  window.location.href = 'SearchPage.html';
}
