# 📚 UCI Course Recommender

## Overview
This project is a lightweight course search and ranking system for UC Irvine built using:
- Python
- SQLite
- WebSOC data

Instead of relying on live API calls, this system uses a locally collected WebSOC dataset to build a searchable database of:
- Courses
- Sections
- Meeting times
- Locations

The goal of this demo is to show:
- Database indexing
- Term filtering
- Course ranking
- Real meeting data integration

## Setup

```bash
# 1. Clone the repo and enter the project directory
cd searchengine

# 2. (Optional) Create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Build the database (first run downloads data from Anteater API, ~5 min)
cd backend
python index_setup.py
# To force re-download existing JSON data:
python index_setup.py --force

# 5. Start the server
python server.py

# 6. Open http://localhost:8080 in browser
```

## File Descriptions

```
searchengine/
├── backend/
│   ├── index/
│   │   ├── common.py                # Shared constants (QUARTERS, GE_CATEGORIES) and utility functions
│   │   ├── index_search.py          # CourseSearch class — query courses by major, minor, GE, term, etc.
│   │   └── sql_index.py             # Builds the SQLite database: creates tables, inserts all data
│   │
│   ├── tests/
│   │   └── index_query_tests.py     # Unit tests for CourseSearch and query functions
│   │
│   ├── data_collection.py           # Fetches raw data from Anteater API and saves to JSON files
│   ├── data_categorization.py       # Builds standalone JSON indexes by dept, instructor, level, GE
│   ├── index_setup.py               # Main setup script: downloads data (if needed) and builds courses.db
│   ├── quick_setup.py               # Lightweight setup: builds a minimal DB (no WebSOC term details)
│   ├── server.py                    # Flask web server — serves frontend and provides REST API endpoints
│   ├── progress_report_1_demo.py    # Demo script used for progress report #1 presentation
│   │
│   ├── all_course_data.json         # [Generated] All course data from Anteater API
│   ├── all_major_data.json          # [Generated] All majors and their graduation requirements
│   ├── all_minor_data.json          # [Generated] All minors and their requirements
│   ├── all_specialization_data.json # [Generated] All specializations and their requirements
│   └── courses.db                   # [Generated] SQLite database built from the JSON files above
│
├── frontend/
│   ├── UserProfilePage.html         # Onboarding page: 4-step form for student profile
│   ├── SearchPage.html              # Main search page: filters, search bar, course result cards
│   └── static/
│       ├── css/style.css            # All styling for both pages
│       └── js/
│           ├── UserProfilePage.js   # Onboarding form logic, saves profile to localStorage
│           └── SearchPage.js        # Search page logic: calls API, renders course cards
│
├── requirements.txt                 # Python dependencies (flask, flask-cors, requests)
└── README.md                        # This file
```

## Database Schema

The SQLite database is built in `backend/index/sql_index.py` and stores both static catalog metadata and term-specific meeting data.

### Core tables

#### `Courses`
Stores general course metadata.

| Column | Description |
|--------|-------------|
| `course_id` | Canonical course id (ex: `I&CSCI31`) |
| `department` | Department code / name |
| `course_number` | Course number |
| `course_title` | Official course title |
| `min_units` | Minimum units |
| `max_units` | Maximum units |
| `repeatability` | Repeatability metadata |
| `grading_option` | Grading option |
| `corequisites` | Corequisite text |

#### `Terms`
Stores term-specific section and meeting information from WebSOC.

| Column | Description |
|--------|-------------|
| `course_id` | References `Courses.course_id` |
| `section_code` | WebSOC section code |
| `section_type` | Lecture / discussion / lab / etc. |
| `year` | Academic year |
| `quarter` | Quarter code |
| `building_id` | Building code |
| `room_number` | Room number |
| `start_time` | Start time |
| `end_time` | End time |
| `days` | Meeting days |
| `restrictions` | Enrollment restrictions |
| `max_capacity` | Section capacity |
| `num_currently_enrolled` | Current enrollment |
| `waitlist_capacity` | Waitlist capacity |
| `num_on_waitlist` | Current waitlist count |
| `is_cancelled` | Cancellation flag |

### Requirement tables

These tables support degree-aware search and ranking.

#### `Majors`
Stores major metadata.

#### `MajorRequirements`
Stores hierarchical graduation requirement groups for each major.

#### `MajorCourses`
Maps courses to major requirements and requirement groups.

#### `Minors`
Stores minor metadata.

#### `MinorRequirements`
Stores minor requirement groups.

#### `MinorCourses`
Maps courses to minor requirements.

#### `Specializations`
Stores specialization metadata and parent major relationship.

#### `SpecializationRequirements`
Stores specialization requirement groups.

#### `SpecializationCourses`
Maps courses to specialization requirements.

### Prerequisite tables

#### `PrerequisiteRelationships`
Stores AND / OR prerequisite tree structure.

#### `PrerequisiteCourses`
Stores actual prerequisite courses belonging to each relationship node.

This allows the system to evaluate more complex prerequisite logic than a flat prerequisite list.

### GE tables

#### `GenEdRequirements`
Maps courses to UCI GE categories.

### Inverted index tables

#### `InvertedCourseIndex`
Stores token frequencies for course title / department / number search.

#### `InvertedMajorIndex`
Stores token frequencies for major-name search.

---

## Search

Search is handled primarily through `CourseSearch` in `backend/index/index_search.py`.

### Supported search/filter features

The backend can filter courses by:

- term (`year`, `quarter`)
- selected major(s)
- selected minor(s)
- selected specialization(s)
- completed prerequisites
- major / minor / specialization requirement progress
- GE needs
- text query terms through inverted indexes

### Query flow

At a high level, the system does the following:

1. Load relevant requirement-linked course ids from the database.
2. Intersect them with term availability from `Terms`.
3. Remove already completed courses if requested.
4. Check prerequisite satisfaction using the prerequisite relationship tree.
5. Return feasible results.
6. Optionally apply ranking and sort by score.

### Example usage

```python
from index.index_search import CourseSearch

search = CourseSearch("courses.db")
search.add_major("BS-201")
search.add_prerequisite("MATH1B")

results = search.search(2026, "Spring")
for course in results:
    print(course)
```

## Ranking

Ranking is implemented in `ranking.py` using the function: `compute_match_score(…)`

The system assigns a score to each course based on multiple factors and returns both:
- a numeric score
- a list of human-readable reasons (for explainability)

---

### Ranking Signals

Courses are scored using a combination of academic relevance, user preferences, and real-world scheduling constraints.

#### 🎓 Academic Relevance

- **Major requirement** (+30)  
  Courses required for the selected major are prioritized.

- **Prerequisite completion** (+15 / disqualify if unmet)  
  Courses with unmet prerequisites are heavily penalized.

- **Dependency bonus** (+ up to 15)  
  Courses that unlock future required courses are boosted.

---

#### 📚 Graduation Progress

- **GE requirement match** (+20)  
  Courses satisfying remaining GE categories are prioritized.

---

#### ⏰ User Preferences

- **Preferred time match** (+15)  
  Morning / afternoon / evening preferences.

- **Preferred format** (+10)  
  Online vs in-person preference.

- **Unit constraint** (+10)  
  Courses within the user's max unit limit.

- **Workload preference**
  - Light workload → prefer low-unit / low-difficulty courses
  - Heavy workload → slight boost for higher-unit courses

---

#### 🔍 Keyword Boosts

Optional keyword-based boosts:

- `"morning"`, `"afternoon"`, `"evening"` → +10
- `"online"` → +15 (only if actually online)
- `"easy"` → small boost (+5)

---

#### 🏫 Section & Availability Signals

- **More sections available** (+ up to 5)
- **Open seats available** (+ up to 6)
- **Low or no waitlist** (+ up to 2)

These signals prioritize courses that are easier to enroll in.

---

### Contextual Scheduling Penalties

The ranking system adapts dynamically based on the student's current schedule.

- **Time conflicts** (−40)  
  Courses overlapping with existing schedule are heavily penalized.

- **Walking distance penalty** (−10)  
  Consecutive classes in different buildings are penalized.

- **Final exam conflict** (−15)  
  Courses with finals on the same day are penalized.

---

### Scoring Output

- Each ranked result includes:
`{
“course_id”: “I&CSCI32”,
“score”: 78,
“reasons”: [
“Required for your major”,
“Prerequisites completed”,
“Matches morning preference”,
“Units <= 4”,
“3 section option(s)”
]
}`
---

### Key Design Principles

- **Explainability**  
  Every score includes reasons to justify ranking decisions.

- **Personalization**  
  Results change based on user profile and schedule.

- **Feasibility-first**  
  Courses that cannot be taken (prereqs not met) are filtered out.

- **Real-world constraints**  
  Uses actual meeting times, enrollment data, and schedule conflicts.

---

### Summary

The ranking system is not static — it dynamically adapts based on:

- academic progress (major / prerequisites / GE)
- user preferences (time, format, workload)
- real schedule constraints (conflicts, walking, finals)
- enrollment feasibility (sections, waitlist)

This produces a more realistic and useful course recommendation experience compared to simple filtering or keyword search.
