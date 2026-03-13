import sqlite3
import os

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

conn.commit()
conn.close()

# print("User tables created successfully")