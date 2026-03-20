import sqlite3
import os

def create_user_index():
    DB_PATH = os.path.join(os.path.dirname(__file__), "courses.db")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # cursor.execute("""DROP TABLE IF EXISTS Users;""")
    # cursor.execute("""DROP TABLE IF EXISTS UserCompletedCourses;""")
    # cursor.execute("""DROP TABLE IF EXISTS UserGeNeeds;""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        display_name TEXT,
        standing TEXT,
        college TEXT,
        major TEXT,
        minor TEXT,
        priority TEXT,
        preferred_time TEXT,
        workload TEXT,
        course_format TEXT,
        commuter TEXT,
        quarter_target TEXT,
        max_units INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UserGeNeeds (
        user_id INTEGER,
        ge_category TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UserCompletedCourses (
        user_id INTEGER,
        course_code TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # CourseGrades table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CourseGrades (
        course_id TEXT PRIMARY KEY,
        average_gpa REAL,
        grade_a_count INTEGER,
        grade_b_count INTEGER,
        grade_c_count INTEGER,
        grade_d_count INTEGER,
        grade_f_count INTEGER,
        FOREIGN KEY (course_id) REFERENCES Courses(course_id)
    )
    """)

    # Add instructor column to Terms if missing
    existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(Terms)").fetchall()]
    if "instructor" not in existing_cols:
        cursor.execute("ALTER TABLE Terms ADD COLUMN instructor TEXT")

    conn.commit()
    conn.close()