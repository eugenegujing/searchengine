"""
Quick database setup — fetches only course data (fast) and builds a minimal
courses.db so the Flask API can serve real results immediately.
Run the full index_setup.py later for majors/minors/specializations/terms.
"""
import sqlite3
import json
import os
import requests

DB_PATH = os.path.join(os.path.dirname(__file__), "courses.db")
JSON_PATH = os.path.join(os.path.dirname(__file__), "all_course_data.json")

GE_CATEGORIES = {
    "GE Ia: Lower Division Writing": "1A",
    "GE Ib: Upper Division Writing": "1B",
    "GE II: Science and Technology": "2",
    "GE III: Social & Behavioral Sciences": "3",
    "GE IV: Arts and Humanities": "4",
    "GE Va: Quantitative Literacy": "5A",
    "GE Vb: Formal Reasoning": "5B",
    "GE VI: Language Other Than English": "6",
    "GE VII: Multicultural Studies": "7",
    "GE VIII: International/Global Issues": "8",
}

QUARTERS = {
    "fall": "Fall", "spring": "Spring", "winter": "Winter",
    "summer1": "Summer1", "summer2": "Summer2", "summer10wk": "Summer10wk",
}


def fetch_courses():
    url = "https://anteaterapi.com/v2/rest/coursesCursor"
    cursor = None
    all_courses = []
    batch = 1
    while True:
        params = {"take": 100}
        if cursor:
            params["cursor"] = cursor
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json().get("data") or {}
        items = data.get("items", [])
        cursor = data.get("nextCursor")
        all_courses.extend(items)
        print(f"  Batch {batch}: {len(items)} courses (total {len(all_courses)})")
        batch += 1
        if not cursor:
            break
    with open(JSON_PATH, "w") as f:
        json.dump(all_courses, f, indent=2)
    print(f"Saved {len(all_courses)} courses to {JSON_PATH}")
    return all_courses


def build_db(courses):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS Courses (
            course_id TEXT PRIMARY KEY,
            department TEXT NOT NULL,
            course_number TEXT NOT NULL,
            course_title TEXT NOT NULL,
            min_units INTEGER NOT NULL,
            max_units INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Terms (
            course_id TEXT NOT NULL,
            section_code INTEGER,
            section_type TEXT,
            year INTEGER NOT NULL,
            quarter TEXT NOT NULL,
            building_id TEXT,
            room_number TEXT,
            start_time TEXT,
            end_time TEXT,
            days TEXT,
            restrictions TEXT,
            max_capacity TEXT,
            num_currently_enrolled TEXT,
            waitlist_capacity TEXT,
            num_on_waitlist TEXT,
            is_cancelled INTEGER,
            PRIMARY KEY (course_id, year, quarter),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
        CREATE TABLE IF NOT EXISTS GenEdRequirements (
            course_id TEXT,
            ge_category TEXT,
            ge_id TEXT,
            PRIMARY KEY (course_id, ge_category, ge_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
        CREATE TABLE IF NOT EXISTS Prerequisites (
            course_id TEXT,
            prereq_id TEXT,
            PRIMARY KEY (course_id, prereq_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
        CREATE TABLE IF NOT EXISTS Majors (
            major_id TEXT PRIMARY KEY,
            major_name TEXT NOT NULL,
            type TEXT,
            division TEXT
        );
        CREATE TABLE IF NOT EXISTS MajorCourses (
            major_id TEXT,
            course_id TEXT,
            requirement_label TEXT,
            course_count INTEGER,
            group_label TEXT,
            PRIMARY KEY (major_id, course_id, requirement_label, group_label),
            FOREIGN KEY (major_id) REFERENCES Majors(major_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
        CREATE TABLE IF NOT EXISTS Minors (
            minor_id TEXT, minor_name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS MinorCourses (
            minor_id TEXT, course_id TEXT,
            PRIMARY KEY (minor_id, course_id)
        );
    """)

    for c in courses:
        cid = c["id"]
        cur.execute("""
            INSERT OR REPLACE INTO Courses(course_id, department, course_number,
                                           course_title, min_units, max_units)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cid, c["department"], c["courseNumber"],
              c["title"], c["minUnits"], c["maxUnits"]))

        for ge in c.get("geList", []):
            ge_id = GE_CATEGORIES.get(ge)
            if ge_id:
                cur.execute("""
                    INSERT OR REPLACE INTO GenEdRequirements(course_id, ge_category, ge_id)
                    VALUES (?, ?, ?)
                """, (cid, ge, ge_id))

        for prereq in c.get("prerequisites", []):
            pid = prereq.get("id")
            if pid:
                cur.execute("""
                    INSERT OR REPLACE INTO Prerequisites(course_id, prereq_id)
                    VALUES (?, ?)
                """, (cid, pid))

        for term in c.get("terms", []):
            term_str = term if isinstance(term, str) else term.get("term", "")
            parts = term_str.strip().split()
            if len(parts) == 2:
                year_str, qtr = parts
                qtr_lower = qtr.lower()
                qtr_cap = QUARTERS.get(qtr_lower, qtr.capitalize())
                try:
                    cur.execute("""
                        INSERT OR REPLACE INTO Terms(course_id, year, quarter)
                        VALUES (?, ?, ?)
                    """, (cid, int(year_str), qtr_cap))
                except (ValueError, sqlite3.IntegrityError):
                    pass

    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM Courses").fetchone()[0]
    terms_count = cur.execute("SELECT COUNT(*) FROM Terms").fetchone()[0]
    ge_count = cur.execute("SELECT COUNT(*) FROM GenEdRequirements").fetchone()[0]
    conn.close()
    print(f"Database created: {DB_PATH}")
    print(f"  {count} courses, {terms_count} term entries, {ge_count} GE entries")


if __name__ == "__main__":
    print("Step 1: Fetching course data from Anteater API...")
    if os.path.exists(JSON_PATH):
        print(f"  Found existing {JSON_PATH}, loading...")
        with open(JSON_PATH, "r") as f:
            courses = json.load(f)
        print(f"  Loaded {len(courses)} courses")
    else:
        courses = fetch_courses()

    print("Step 2: Building database...")
    build_db(courses)
    print("Done! You can now start the Flask server with: python backend/app.py")
