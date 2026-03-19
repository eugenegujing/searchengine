import sys
import os
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ranking import compute_match_score
from user_index import create_user_index
from index.index_search import CourseSearch

sys.path.insert(0, os.path.dirname(__file__))

DB_PATH = os.path.join(os.path.dirname(__file__), "courses.db")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# ── GE mapping (frontend value → database ge_id) ──

GE_VALUE_TO_CATEGORY = {
    "Ia":   "GE Ia: Lower Division Writing",
    "Ib":   "GE Ib: Upper Division Writing",
    "II":   "GE II: Science and Technology",
    "III":  "GE III: Social & Behavioral Sciences",
    "IV":   "GE IV: Arts and Humanities",
    "Va":   "GE Va: Quantitative Literacy",
    "Vb":   "GE Vb: Formal Reasoning",
    "VI":   "GE VI: Language Other Than English",
    "VII":  "GE VII: Multicultural Studies",
    "VIII": "GE VIII: International/Global Issues",
}

GE_ID_TO_VALUE = {
    "1A": "Ia", "1B": "Ib", "2": "II", "3": "III", "4": "IV",
    "5A": "Va", "5B": "Vb", "6": "VI", "7": "VII", "8": "VIII",
}



def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Build inverted index from course data ──

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "to", "for", "is", "on",
    "at", "by", "with", "from", "as", "its", "it", "this", "that", "are",
    "was", "be", "has", "had", "not", "but", "what", "all", "were", "we",
    "when", "your", "can", "each", "which", "their", "if", "do", "will",
    "about", "up", "out", "them", "then", "no", "into", "than", "other",
    "div", "division",  # not useful as search terms
}

# ── Common abbreviations → actual department/index terms ──
SYNONYMS = {
    "cs": "compsci",
    "ics": "compsci",
    "info": "informatics",
    "stats": "statistics",
    "bio": "biological",
    "chem": "chemistry",
    "econ": "economics",
    "psych": "psychology",
    "phys": "physics",
    "eng": "engineering",
    "math": "math",
    "poli": "political",
    "anthro": "anthropology",
    "soc": "social",
}

# ─────────────── Serve frontend pages ───────────────

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "LoginPage.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ─────────────── API: Search courses ───────────────

@app.route("/api/search")
def api_search():
    q       = request.args.get("q", "").strip()
    quarter = request.args.get("quarter", "")
    dept    = request.args.get("dept", "")
    level   = request.args.get("level", "")
    ge      = request.args.get("ge", "")
    max_units = request.args.get("maxUnits", "")
    sort_by = request.args.get("sortBy", "relevance")
    username = request.args.get("username")
    time_pref = request.args.get("timeOfDay", "")
    pill = request.args.get("pill", "")

    conn = get_db()

    user_profile = None
    completed = set()
    ge_needed = set()
    major_course_ids = set()
    prereq_map = {}
    course_search = None

    if username:
        user_profile = conn.execute("""
            SELECT * FROM Users WHERE username = ?
        """, (username,)).fetchone()


        # convert to dict so you can safely use .get()
        if user_profile:
            user_profile = dict(user_profile)

        if user_profile:
            user_id = user_profile["id"]

            # completed courses (stored as course_id, e.g. "ICS31")
            rows = conn.execute("""
                SELECT course_code FROM UserCompletedCourses WHERE user_id = ?
            """, (user_id,)).fetchall()
            completed = {r["course_code"] for r in rows}

            # build prereq_map: course_id -> set of prereq_course_ids
            prereq_rows = conn.execute("""
                SELECT course_id, prereq_course_id FROM PrerequisiteCourses
            """).fetchall()
            for pr in prereq_rows:
                prereq_map.setdefault(pr["course_id"], set()).add(pr["prereq_course_id"])

            # ge needs
            rows = conn.execute("""
                SELECT ge_category FROM UserGeNeeds WHERE user_id = ?
            """, (user_id,)).fetchall()
            ge_needed = {r["ge_category"] for r in rows}

            # major requirement courses
            major_id = user_profile.get("major") or ""
            if major_id:
                course_search = CourseSearch(DB_PATH)
                course_search.add_major(major_id)
                for course_id in completed:
                    course_search.add_prerequisite(course_id)
                major_course_ids = course_search.search(include_prereq_unsatisfied=True,include_completed=False)
                # rows = conn.execute("""
                #     SELECT course_id FROM MajorCourses
                #     WHERE major_id = ? AND course_id IS NOT NULL
                # """, (major_id,)).fetchall()
                # major_course_ids = {r["course_id"] for r in rows}

    clauses = []
    params  = []
    need_terms = False

    if quarter:
        parts = quarter.split("-")
        if len(parts) == 2:
            need_terms = True
            clauses.append("T.year = ?")
            params.append(int(parts[0]))
            clauses.append("LOWER(T.quarter) = LOWER(?)")
            params.append(parts[1])
            if course_search:
                major_course_ids = course_search.search(parts[0], parts[1],include_prereq_unsatisfied=True,include_completed=False)

    if dept:
        clauses.append("C.department = ?")
        params.append(dept)

    if level == "lower":
        clauses.append("CAST(C.course_number AS INTEGER) < 100")
    elif level == "upper":
        clauses.append("CAST(C.course_number AS INTEGER) >= 100")

    if ge:
        ge_category = GE_VALUE_TO_CATEGORY.get(ge)
        if ge_category:
            clauses.append("""C.course_id IN (
                SELECT course_id FROM GenEdRequirements WHERE ge_category = ?
            )""")
            params.append(ge_category)

    if max_units and max_units.isdigit() and int(max_units) < 8:
        clauses.append("C.max_units <= ?")
        params.append(int(max_units))

    # Extract special keywords from search query for ranking, search DB with remaining words
    RANKING_KEYWORDS = {"easy", "online", "morning", "afternoon", "evening"}
    FILTER_KEYWORDS = {"ge"}  # keywords that map to DB filters, not text search
    LEVEL_KEYWORDS = {"upper", "lower"}  # treated as course level filters
    search_keywords = []
    search_terms = []
    if q:
        for word in re.findall(r"[a-z0-9]+", q.lower()):
            if word in RANKING_KEYWORDS:
                search_keywords.append(word)
            elif word in FILTER_KEYWORDS:
                # "ge" → filter to courses with GE requirements
                clauses.append("""C.course_id IN (
                    SELECT DISTINCT course_id FROM GenEdRequirements
                )""")
            elif word in LEVEL_KEYWORDS:
                # "upper" / "lower" → course level filter
                if word == "upper":
                    clauses.append("CAST(C.course_number AS INTEGER) >= 100")
                else:
                    clauses.append("CAST(C.course_number AS INTEGER) < 100")
            elif word not in STOP_WORDS and len(word) > 1:
                # Apply synonym mapping
                mapped = SYNONYMS.get(word, word)
                search_terms.append(mapped)

        # Use inverted index: each search term must match
        for term in search_terms:
            clauses.append("""C.course_id IN (
                SELECT course_id FROM InvertedCourseIndex WHERE term = ?
            )""")
            params.append(term)
    
    if time_pref:
        need_terms = True  # make sure we join Terms table
        if time_pref.lower() == "morning":
            clauses.append("T.start_time < '12:00'")
        elif time_pref.lower() == "afternoon":
            clauses.append("T.start_time >= '12:00' AND T.start_time < '17:00'")
        elif time_pref.lower() == "evening":
            clauses.append("T.start_time >= '17:00'")

    # ── Quick-filter pill logic ──
    if pill == "lower-div":
        clauses.append("CAST(C.course_number AS INTEGER) < 100")
    elif pill == "upper-div":
        clauses.append("CAST(C.course_number AS INTEGER) >= 100")
        clauses.append("CAST(C.course_number AS INTEGER) < 200")
    elif pill == "morning":
        need_terms = True
        clauses.append("T.start_time < '12:00'")
        clauses.append("T.start_time != 'TBA'")
    elif pill == "ge" and ge_needed:
        # Convert short codes (e.g. "VI") to full DB names (e.g. "GE VI: Language Other Than English")
        ge_full_names = []
        for code in ge_needed:
            full_name = GE_VALUE_TO_CATEGORY.get(code)
            if full_name:
                ge_full_names.append(full_name)
            else:
                ge_full_names.append(code)  # fallback: use as-is
        if ge_full_names:
            placeholders_ge = ",".join("?" * len(ge_full_names))
            clauses.append(f"""C.course_id IN (
                SELECT course_id FROM GenEdRequirements WHERE ge_category IN ({placeholders_ge})
            )""")
            params.extend(ge_full_names)
    elif pill == "major" and major_course_ids:
        placeholders_mc = ",".join("?" * len(major_course_ids))
        clauses.append(f"C.course_id IN ({placeholders_mc})")
        params.extend(major_course_ids)

    where = " AND ".join(clauses) if clauses else "1=1"

    if need_terms:
        join_clause = "INNER JOIN Terms T ON C.course_id = T.course_id"
    else:
        join_clause = ""

    # First query: get distinct courses (LIMIT applies to courses, not sections)
    sql = f"""
        SELECT DISTINCT
            C.course_id,
            C.department,
            C.course_number,
            C.course_title,
            C.min_units,
            C.max_units
        FROM Courses C
        {join_clause}
        WHERE {where}
        ORDER BY C.department, C.course_number
    """

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception:
        conn.close()
        return jsonify({"courses": [], "error": "Database not ready. Run index_setup.py first."})

    # Build a lookup of course_id -> first term info for the selected quarter
    course_terms = defaultdict(list)
    if need_terms:
        course_ids = [row["course_id"] for row in rows]
        if course_ids:
            placeholders = ",".join("?" * len(course_ids))
            parts = quarter.split("-")
            term_rows = conn.execute(f"""
                SELECT course_id, section_code, start_time, end_time, days, building_id, room_number
                FROM Terms
                WHERE course_id IN ({placeholders}) AND year = ? AND LOWER(quarter) = LOWER(?)
            """, course_ids + [int(parts[0]), parts[1]]).fetchall()
            for tr in term_rows:
                course_terms[tr["course_id"]].append(tr)

    try:
        ge_rows = conn.execute("""
            SELECT course_id, ge_category, ge_id FROM GenEdRequirements
        """).fetchall()
    except Exception:
        ge_rows = []
    course_ge = {}
    for r in ge_rows:
        cid = r["course_id"]
        ge_id = r["ge_id"]
        ge_val = GE_ID_TO_VALUE.get(ge_id, ge_id)
        course_ge.setdefault(cid, [])
        if ge_val not in course_ge[cid]:
            course_ge[cid].append(ge_val)

    courses = []
    for row in rows:
        cid = row["course_id"]

        course_number_str = row["course_number"] or ""
        try:
            num = int("".join(c for c in course_number_str if c.isdigit()) or "0")
        except ValueError:
            num = 0
        level_str = "lower" if num < 100 else "upper"

        term_courses = course_terms.get(cid, [])
        time_str = ""
        days_str = ""
        location = "TBA"

        for course in term_courses:
            if course["section_code"] % 10 == 0:
                term = course
                time_str = format_time(term["start_time"], term["end_time"])
                days_str = term["days"] or ""
                location_parts = []
                if term["building_id"] and term["building_id"] != "TBA":
                    location_parts.append(term["building_id"])
                if term["room_number"]:
                    location_parts.append(str(term["room_number"]))
                location = " ".join(location_parts) or "TBA"
        

        ge_list = course_ge.get(cid, [])
        tags = []
        if ge_list:
            tags.append("ge")
        if cid in major_course_ids:
            tags.append("major")

        explanation_parts = []
        if ge_list:
            ge_names = ", ".join(f"GE {g}" for g in ge_list)
            explanation_parts.append(f"Satisfies {ge_names}")

        course_units = row["max_units"] or row["min_units"] or 4
        course_time_str = f"{days_str} {time_str}".strip() if time_str else "TBA"

        course_dict = {
            "id": cid,
            "ge": ge_list,
            "time": course_time_str,
            "units": course_units,
            "format": "in-person",
        }

        score = 0
        reasons = []

        if user_profile:
            score, reasons = compute_match_score(
                course_id=cid,
                user_profile=user_profile,
                completed=completed,
                ge_needed=ge_needed,
                db_path=DB_PATH,
                keywords=search_keywords,
                course=course_dict,
                major_course_ids=major_course_ids,
                prereq_map=prereq_map,
            )
        else:
            score = 50

        # fallback explanation if ranking doesn't provide one
        if not reasons and explanation_parts:
            reasons = explanation_parts

        courses.append({
            "id": cid,
            "code": f"{row['department']} {row['course_number']}",
            "title": row["course_title"],
            "dept": row["department"],
            "level": level_str,
            "units": course_units,
            "instructor": "",
            "time": course_time_str,
            "location": location,
            "format": "in-person",
            "ge": ge_list,
            "tags": tags,
            "matchScore": score,
            "explanation": ". ".join(reasons) if reasons else "",
        })

    if sort_by == "units-asc":
        courses.sort(key=lambda c: c["units"])
    elif sort_by == "units-desc":
        courses.sort(key=lambda c: c["units"], reverse=True)
    elif sort_by == "dept":
        courses.sort(key=lambda c: c["dept"])
    elif sort_by == "relevance":
        courses.sort(key=lambda c: c["matchScore"], reverse=True)
    
    # apply limit to 50 results
    courses = courses[:50]

    conn.close()
    return jsonify({"courses": courses})


# ─────────────── API: List departments ───────────────

@app.route("/api/departments")
def api_departments():
    conn = get_db()
    try:
        rows = conn.execute("SELECT DISTINCT department FROM Courses ORDER BY department").fetchall()
        conn.close()
        return jsonify([r["department"] for r in rows])
    except Exception:
        conn.close()
        return jsonify([])


# ─────────────── API: List majors ───────────────

@app.route("/api/majors")
def api_majors():
    conn = get_db()
    try:
        rows = conn.execute("SELECT major_id, major_name FROM Majors ORDER BY major_name").fetchall()
        conn.close()
        return jsonify([{"id": r["major_id"], "name": r["major_name"]} for r in rows])
    except Exception:
        conn.close()
        return jsonify([])


@app.route("/api/major-courses/<major_id>")
def api_major_courses(major_id):
    """Return required courses for a major, grouped into categories."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT MC.course_id, MC.group_label,
                   C.department, C.course_number, C.course_title
            FROM MajorCourses MC
            JOIN Courses C ON MC.course_id = C.course_id
            WHERE MC.major_id = ? AND MC.course_id IS NOT NULL
            ORDER BY C.department, C.course_number
        """, (major_id,)).fetchall()
        conn.close()

        # Count courses per group_label to classify
        from collections import Counter
        group_counts = Counter(r["group_label"] for r in rows)

        core = []
        electives = []
        ge = []
        seen = set()

        for r in rows:
            cid = r["course_id"]
            if cid in seen:
                continue
            seen.add(cid)
            entry = {
                "course_id": cid,
                "code": f"{r['department']} {r['course_number']}",
                "title": r["course_title"],
            }
            gl = (r["group_label"] or "").lower()
            if "ge " in gl or "ge-" in gl or gl.startswith("ge"):
                ge.append(entry)
            elif group_counts[r["group_label"]] > 10:
                electives.append(entry)
            else:
                core.append(entry)

        return jsonify({"core": core, "electives": electives, "ge": ge})
    except Exception:
        conn.close()
        return jsonify({"core": [], "electives": [], "ge": []})
    
# ─────────────── API: Register ───────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    display_name = data.get("displayName", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Check if username exists
    existing = cur.execute("SELECT id FROM Users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

    # insert user
    cur.execute("""
        INSERT INTO Users (username, password, display_name)
        VALUES (?, ?, ?)
    """, (username, password, display_name))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()

    return jsonify({"status": "registered", "user_id": user_id})

# ─────────────── API: Login ───────────────

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, standing, display_name
        FROM Users
        WHERE username=? AND password=?
    """, (username, password))

    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "error", "error": "Invalid credentials"})

    profile_completed = bool(row["standing"])  # True if standing is not NULL / empty

    return jsonify({
        "status": "success",
        "profile_completed": profile_completed,
        "displayName": row["display_name"]
    })

# ─────────────── API: Save/Update User Profile ───────────────

@app.route("/api/profile", methods=["POST"])
def api_save_profile_partial():
    data = request.get_json()
    username = data.get("username")
    new_profile = data.get("profile", {})

    if not username or not new_profile:
        return jsonify({"error": "Missing username or profile"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Get existing user
    cur.execute("SELECT * FROM Users WHERE username = ?", (username,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    user_id = user["id"]

    # Merge old values with new values
    merged = {
        "display_name": new_profile.get("displayName") or user["display_name"],
        "standing": new_profile.get("standing") or user["standing"],
        "college": new_profile.get("college") or user["college"],
        "major": new_profile.get("major") or user["major"],
        "minor": new_profile.get("minor") or user["minor"],
        "priority": new_profile.get("priority") or user["priority"],
        "preferred_time": new_profile.get("preferredTime") or user["preferred_time"],
        "workload": new_profile.get("workload") or user["workload"],
        "course_format": new_profile.get("courseFormat") or user["course_format"],
        "commuter": new_profile.get("commuter") or user["commuter"],
        "quarter_target": new_profile.get("quarterTarget") or user["quarter_target"],
        "max_units": new_profile.get("maxUnits") or user["max_units"]
    }

    # Update user with merged values
    cur.execute("""
        UPDATE Users
        SET display_name=?, standing=?, college=?, major=?, minor=?,
            priority=?, preferred_time=?, workload=?, course_format=?,
            commuter=?, quarter_target=?, max_units=?
        WHERE id=?
    """, (
        merged["display_name"], merged["standing"], merged["college"],
        merged["major"], merged["minor"], merged["priority"], merged["preferred_time"],
        merged["workload"], merged["course_format"], merged["commuter"],
        merged["quarter_target"], merged["max_units"], user_id
    ))

    # Optional: update GE needs / completed courses only if provided
    if "geNeeded" in new_profile:
        cur.execute("DELETE FROM UserGeNeeds WHERE user_id=?", (user_id,))
        for ge in new_profile["geNeeded"]:
            cur.execute("INSERT INTO UserGeNeeds (user_id, ge_category) VALUES (?, ?)", (user_id, ge))

    if "completedCourses" in new_profile:
        cur.execute("DELETE FROM UserCompletedCourses WHERE user_id=?", (user_id,))
        for course in new_profile["completedCourses"]:
            cur.execute("INSERT INTO UserCompletedCourses (user_id, course_code) VALUES (?, ?)", (user_id, course))

    conn.commit()
    conn.close()

    return jsonify({"status": "saved", "user_id": user_id})

# @app.route("/api/profile", methods=["POST"], strict_slashes=False)
# def api_save_profile():
#     data = request.get_json()
#     username = data.get("username")
#     profile = data.get("profile")

#     conn = get_db()
#     cur = conn.cursor()

#     # check if user already exists
#     cur.execute("SELECT id FROM Users WHERE username = ?", (username,))
#     row = cur.fetchone()

#     if row:
#         user_id = row["id"]

#         # UPDATE existing profile
#         cur.execute("""
#             UPDATE Users
#             SET display_name=?,
#                 standing=?,
#                 college=?,
#                 major=?,
#                 minor=?,
#                 priority=?,
#                 preferred_time=?,
#                 workload=?,
#                 course_format=?,
#                 commuter=?,
#                 quarter_target=?,
#                 max_units=?
#             WHERE id=?
#         """, (
#             profile.get("displayName"),
#             profile.get("standing"),
#             profile.get("college"),
#             profile.get("major"),
#             profile.get("minor"),
#             profile.get("priority"),
#             profile.get("preferredTime"),
#             profile.get("workload"),
#             profile.get("courseFormat"),
#             profile.get("commuter"),
#             profile.get("quarterTarget"),
#             profile.get("maxUnits"),
#             user_id
#         ))

#         # clear old GE + courses
#         cur.execute("DELETE FROM UserGeNeeds WHERE user_id=?", (user_id,))
#         cur.execute("DELETE FROM UserCompletedCourses WHERE user_id=?", (user_id,))

#     else:
#         # INSERT new user
#         cur.execute("""
#             INSERT INTO Users (
#                 username,
#                 display_name,
#                 standing,
#                 college,
#                 major,
#                 minor,
#                 priority,
#                 preferred_time,
#                 workload,
#                 course_format,
#                 commuter,
#                 quarter_target,
#                 max_units
#             )
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             username,
#             profile.get("displayName"),
#             profile.get("standing"),
#             profile.get("college"),
#             profile.get("major"),
#             profile.get("minor"),
#             profile.get("priority"),
#             profile.get("preferredTime"),
#             profile.get("workload"),
#             profile.get("courseFormat"),
#             profile.get("commuter"),
#             profile.get("quarterTarget"),
#             profile.get("maxUnits")
#         ))

#         user_id = cur.lastrowid

#     # Insert GE needs
#     for ge in profile.get("geNeeded", []):
#         cur.execute(
#             "INSERT INTO UserGeNeeds (user_id, ge_category) VALUES (?, ?)",
#             (user_id, ge)
#         )

#     # Insert completed courses
#     for course in profile.get("completedCourses", []):
#         cur.execute(
#             "INSERT INTO UserCompletedCourses (user_id, course_code) VALUES (?, ?)",
#             (user_id, course)
#         )

#     conn.commit()
#     conn.close()

#     return jsonify({"status": "saved", "user_id": user_id})

# ─────────────── API: Get User Profile ───────────────

@app.route("/api/profile", methods=["GET"])
def api_get_profile():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Missing username"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Fetch main user info
    cur.execute("""
        SELECT id, display_name, standing, college, major, minor,
               priority, preferred_time, workload, course_format,
               commuter, quarter_target, max_units
        FROM Users
        WHERE username = ?
    """, (username,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Profile not found"}), 404

    user_id = user["id"]

    # Fetch GE needs
    cur.execute("SELECT ge_category FROM UserGeNeeds WHERE user_id = ?", (user_id,))
    ge_rows = cur.fetchall()
    ge_needed = [r["ge_category"] for r in ge_rows]

    # Fetch completed courses
    cur.execute("SELECT course_code FROM UserCompletedCourses WHERE user_id = ?", (user_id,))
    course_rows = cur.fetchall()
    completed_courses = [r["course_code"] for r in course_rows]

    conn.close()

    profile = {
        "username": username,
        "displayName": user["display_name"],
        "standing": user["standing"],
        "college": user["college"],
        "major": user["major"],
        "minor": user["minor"],
        "priority": user["priority"],
        "preferredTime": user["preferred_time"],
        "workload": user["workload"],
        "courseFormat": user["course_format"],
        "commuter": user["commuter"],
        "quarterTarget": user["quarter_target"],
        "maxUnits": user["max_units"],
        "geNeeded": ge_needed,
        "completedCourses": completed_courses
    }

    return jsonify(profile)

# ─────────────── Helpers ───────────────

def format_time(start, end):
    if not start or start == "TBA":
        return ""
    return f"{start}-{end}" if end and end != "TBA" else start


# ─────────────── Run ───────────────

if __name__ == "__main__":
    if not Path(DB_PATH).exists():
        print(f"WARNING: Database not found at {DB_PATH}")
        print("Run index_setup.py first to build the database.")
    # Ensure user tables exist (Users, UserGeNeeds, UserCompletedCourses)
    # create_user_index()
    # Build inverted index if not already populated
    # build_inverted_index()
    app.run(debug=True, port=8080)
