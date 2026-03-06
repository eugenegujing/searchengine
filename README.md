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

## Search

## Ranking

## Demo Flow
