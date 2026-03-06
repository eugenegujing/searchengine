import sys
import os
import sqlite3
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

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


# ─────────────── Serve frontend pages ───────────────

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "UserProfilePage.html")


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

    conn = get_db()

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

    if q:
        clauses.append("""(
            C.course_title LIKE ? OR
            C.department LIKE ? OR
            C.course_number LIKE ? OR
            C.course_id LIKE ?
        )""")
        like = f"%{q}%"
        params.extend([like, like, like, like])

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
        LIMIT 50
    """

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception:
        conn.close()
        return jsonify({"courses": [], "error": "Database not ready. Run index_setup.py first."})

    # Build a lookup of course_id -> first term info for the selected quarter
    course_terms = {}
    if need_terms:
        course_ids = [row["course_id"] for row in rows]
        if course_ids:
            placeholders = ",".join("?" * len(course_ids))
            parts = quarter.split("-")
            term_rows = conn.execute(f"""
                SELECT course_id, start_time, end_time, days, building_id, room_number
                FROM Terms
                WHERE course_id IN ({placeholders}) AND year = ? AND LOWER(quarter) = LOWER(?)
            """, course_ids + [int(parts[0]), parts[1]]).fetchall()
            for tr in term_rows:
                if tr["course_id"] not in course_terms:
                    course_terms[tr["course_id"]] = tr

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

        term = course_terms.get(cid)
        if term:
            time_str = format_time(term["start_time"], term["end_time"])
            days_str = term["days"] or ""
            location_parts = []
            if term["building_id"] and term["building_id"] != "TBA":
                location_parts.append(term["building_id"])
            if term["room_number"]:
                location_parts.append(str(term["room_number"]))
            location = " ".join(location_parts) or "TBA"
        else:
            time_str = ""
            days_str = ""
            location = "TBA"

        ge_list = course_ge.get(cid, [])
        tags = []
        if ge_list:
            tags.append("ge")

        explanation_parts = []
        if ge_list:
            ge_names = ", ".join(f"GE {g}" for g in ge_list)
            explanation_parts.append(f"Satisfies {ge_names}")

        courses.append({
            "id": cid,
            "code": f"{row['department']} {row['course_number']}",
            "title": row["course_title"],
            "dept": row["department"],
            "level": level_str,
            "units": row["max_units"] or row["min_units"] or 4,
            "instructor": "",
            "time": f"{days_str} {time_str}".strip() if time_str else "TBA",
            "location": location,
            "format": "in-person",
            "ge": ge_list,
            "tags": tags,
            "matchScore": 80,
            "explanation": ". ".join(explanation_parts) if explanation_parts else "",
        })

    if sort_by == "units-asc":
        courses.sort(key=lambda c: c["units"])
    elif sort_by == "units-desc":
        courses.sort(key=lambda c: c["units"], reverse=True)
    elif sort_by == "dept":
        courses.sort(key=lambda c: c["dept"])

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
    app.run(debug=True, port=8080)
