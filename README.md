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
