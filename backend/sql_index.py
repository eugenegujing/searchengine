import sqlite3
import json

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
    "GE VIII: International/Global Issues": "8"

                 }

DB_PATH = "courses.db"

def create_index(path: str, course_data: list[dict]):
    # create sql database with tables for courses, majors/minors, and buildings

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.executescript('''
                                 
        CREATE TABLE IF NOT EXISTS Buildings (
            building_id TEXT PRIMARY KEY,
            location TEXT NOT NULL
        );

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
            year INTEGER NOT NULL, 
            quarter TEXT NOT NULL,
            format TEXT,
            building_id TEXT,
            building_number INTEGER,
            PRIMARY KEY (course_id, year, quarter),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            FOREIGN KEY (building_id, building_number) REFERENCES Buildings(building_id, building_number)
        );
                         
        CREATE TABLE IF NOT EXISTS Prerequisites (
            course_id TEXT,
            prereq_id TEXT,
            PRIMARY KEY (course_id, prereq_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            FOREIGN KEY (prereq_id) REFERENCES Courses(course_id)
        );
                         
        CREATE TABLE IF NOT EXISTS GenEdRequirements (
            course_id TEXT,
            ge_category TEXT,
            ge_id TEXT,
            PRIMARY KEY (course_id, ge_category, ge_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );

        CREATE TABLE IF NOT EXISTS Majors (
            major_id TEXT,
            major_name TEXT NOT NULL,
            PRIMARY KEY (major_id)
        );
                         
        CREATE TABLE IF NOT EXISTS MajorCourses (
            major_id TEXT,
            course_id TEXT,
            PRIMARY KEY (major_id, course_id)
            FOREIGN KEY (major_id) REFERENCES Majors(major_id)
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
                         
        CREATE TABLE IF NOT EXISTS Minors (
            minor_id TEXT,
            minor_name TEXT NOT NULL
        );
                         
        CREATE TABLE IF NOT EXISTS MinorCourses (
        minor_id TEXT,
        course_id TEXT,
        PRIMARY KEY (minor_id, course_id)
        FOREIGN KEY (minor_id) REFERENCES Majors(minor_id)
        FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
                         
        CREATE TABLE IF NOT EXISTS Specializations (
            specialization_id TEXT PRIMARY KEY,
            specialization_name TEXT NOT NULL,
            major_id TEXT NOT NULL,
            FOREIGN KEY (major_id) REFERENCES Majors(major_id) 
        );
                         
        CREATE TABLE IF NOT EXISTS SpecializationCourses (
            specialization_id TEXT,
            course_id TEXT,
            PRIMARY KEY (specialization_id, course_id)
            FOREIGN KEY (specialization_id) REFERENCES Majors(specialization_id)
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
                         
        CREATE TABLE IF NOT EXISTS InvertedCourseIndex (
            course_id TEXT,
            term TEXT,
            frequency INTEGER,
            PRIMARY KEY (course_id, term),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
        );
                         
        CREATE INDEX IF NOT EXISTS idx_courseterms
        ON InvertedCourseIndex(course_id, term);
                         
    ''')

    for course in course_data:
        cid = course["id"]
        cdep = course["department"]
        cnumber = course["courseNumber"]
        ctitle = course["title"]
        cmin_units = course["minUnits"]
        cmax_units = course["maxUnits"]
        cursor.execute('''
            INSERT OR REPLACE INTO Courses(course_id, department, 
                                           course_number, course_title,
                                           min_units, max_units)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cid, cdep, cnumber, ctitle, cmin_units, cmax_units))    

        for ge in course["geList"]:
            ge_id = GE_CATEGORIES[ge]
            cursor.execute('''
                INSERT OR REPLACE INTO GenEdRequirements(course_id, ge_category, ge_id)
                VALUES (?, ?, ?)       
            ''', (cid, ge, ge_id))

        for prereq in course["prerequisites"]:
            prereq_id = prereq["id"]
            cursor.execute('''
                INSERT OR REPLACE INTO Prerequisites(course_id, prereq_id)
                VALUES (?, ?)
            ''', (cid, prereq_id))

        for term in course["terms"]:
            year, quarter = term.lower().split()
            cursor.execute('''
                INSERT OR REPLACE INTO Terms(course_id, year, quarter)
                VALUES (?, ?, ?)
            ''', (cid, year, quarter))

    conn.commit()
    return conn

def filter_course_term(year: int, quarter: str, db_path=DB_PATH):
    quarter = quarter.lower()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT course_id FROM Terms WHERE year = ? AND quarter = ?"
    results = cursor.execute(query, (year, quarter)).fetchall()

    return results

if __name__ == "__main__":
    with open("all_course_data.json", "r") as f:
        all_course_data = json.load(f)
        create_index(DB_PATH, all_course_data)
    
    # spring_2026 = filter_course_term(2026, "Spring")
    # for course in spring_2026:
    #     print(course[0])