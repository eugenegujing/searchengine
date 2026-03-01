import sqlite3
import json

""" Run database.py and index.py before running this file """

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

class CourseSearch():
    """

    Class for creating queries and retrieving results

    Member Variables:
        -db_path: path to database
        -course: set containing course ids
        -majors: set containing major ids
        -minors: set containing minor ids
        -specializations: set containing specialization ids
        -completed: set containing completed prerequisites

    To create a query:
        -Initialize a CourseSearch object
        -Add majors, minors, etc
        -Call the search method

    """
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.courses = set()
        self.majors = set()
        self.minors = set()
        self.specializations = set()
        self.completed = set()

    def add_major(self, major_id):
        self.majors.add(major_id)

    def remove_major(self, major_id):
        self.majors.remove(major_id)

    def add_minor(self, minor_id):
        self.minors.add(minor_id)

    def remove_minor(self, minor_id):
        self.minors.remove(minor_id)

    def add_specialization(self, spec):
        self.specializations.add(spec)

    def remove_specialization(self, spec):
        self.specializations.remove(spec)

    def add_prerequisite(self, course_id):
        if (type(course_id) is tuple):
            course_id = course_id[0]
        self.completed.add(course_id)

    def _add_sqlite_result_to_set(self, sqlite_res: tuple, set_out: set):
        """
        takes sqlite output in the form of ((X,), (Y,), (Z,)) and adds X, Y, and Z to a set
        """
        for res in sqlite_res:
            set_out.add(res[0])

    def search(self, year=None, quarter=None):
        if quarter: quarter = quarter.lower()
        for major_id in self.majors:
            sql_out = filter_course_major(major_id, self.db_path)
            self._add_sqlite_result_to_set(sql_out, self.courses)

        for minor_id in self.minors:
            sql_out = filter_course_minor(minor_id, self.db_path)
            self._add_sqlite_result_to_set(sql_out, self.courses)
        
        for course_id in self.completed:
            try:
                self.courses.remove(course_id)
            except KeyError:
                pass

        term_results = filter_course_term(year, quarter, self.db_path)
        if len(self.majors) == 0:
            self.courses = set(term_results)
        else:
            term_set = set()
            self._add_sqlite_result_to_set(term_results, term_set)
            self.courses = term_set & self.courses

        results = set()
        for course in self.courses:
            prereqs_completed = True
            for prereq in get_prerequisites(course, self.db_path):
                if (prereq[0] not in self.completed):
                    prereqs_completed = False
                    break
            if prereqs_completed:
                results.add(course)
        return results
    
    def search_ranked(self, year=None, quarter=None, k=10):
        feasible = self.search(year, quarter)
        ranked = []
        for cid in feasible:
            score, reasons = score_course_simple(
                cid, self.db_path, self.majors, self.minors
            )
            meta = get_course_meta(cid, self.db_path)
            
            ranked.append({
                "course_id": cid,
                "score": score,
                "reasons": reasons,
                **meta
            })
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked[:k]
    


def create_index(path: str, course_data: list[dict]):
    
    """
    create_index: creates tables and indexes for provided course data
        path: path to database
        type: str

        course_data: list of course json data collected from 
        type: list[dict]

    Database structure:
    
        Buildings: Building names and locations
        Courses: General course information
        GenEdRequirements: Stores which courses fulfill each GE category
        Majors: General major information
        MajorCourses: Stores required courses for each major
        Minors: General minor information
        MinorCourses: Stores required courses for each minor
        Prerequisites: Stores which courses have prerequisites
        Specializations: Specialization information
        SpecializationCourses Stores required courses for each specialization
        Terms: Stores term-specific course information
    
    """
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
            course_code INTEGER,
            year INTEGER NOT NULL, 
            quarter TEXT NOT NULL,
            format TEXT,
            building_id TEXT,
            building_number INTEGER,
            start_time TEXT,
            end_time TEXT,
            days TEXT,
            PRIMARY KEY (course_code, year, quarter),
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
            type TEXT,
            division TEXT,
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
    print("Database created at", path)
    return conn

def filter_course_term(year: int, quarter: str, db_path):
    quarter = quarter.lower()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if (year and quarter):
        query = "SELECT course_id FROM Terms WHERE year = ? AND quarter = ?"
        results = cursor.execute(query, (year, quarter)).fetchall()
    elif not year:
        query = "SELECT course_id FROM Terms WHERE quarter = ?"
        results = cursor.execute(query, (quarter)).fetchall()
    elif not quarter:
        query = "SELECT course_id FROM Terms WHERE year = ?"
        results = cursor.execute(query, (year)).fetchall()
    else:
        results = cursor.execute("SELECT course_id FROM Terms").fetchall()

    return results

def filter_course_major(major_id: str, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT course_id FROM MajorCourses WHERE major_id = ?"
    results = cursor.execute(query, (major_id,)).fetchall()

    return results

def filter_course_minor(minor_id: str, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT course_id FROM MinorCourses WHERE minor_id = ?"
    results = cursor.execute(query, (minor_id,)).fetchall()

    return results

def get_prerequisites(course_id: str, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT prereq_id FROM Prerequisites WHERE course_id = ?"
    results = cursor.execute(query, (course_id,)).fetchall()
    
    return results
# def filter_prerequisites(course_id, db_path=DB_PATH):

def get_course_meta(course_id: str, db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    row = cur.execute("""
        SELECT department, course_number, course_title, min_units, max_units
        FROM Courses WHERE course_id = ?
    """, (course_id,)).fetchone()
    conn.close()

    if not row:
        return {"dept": "", "code": course_id, "title": course_id, "min_units": None, "max_units": None}

    dept, num, title, min_u, max_u = row
    return {"dept": dept, "code": f"{dept} {num}", "title": title, "min_units": min_u, "max_units": max_u}


def is_major_course(course_id: str, major_id: str, db_path: str) -> bool:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    hit = cur.execute("""
        SELECT 1 FROM MajorCourses WHERE major_id = ? AND course_id = ? LIMIT 1
    """, (major_id, course_id)).fetchone()
    conn.close()
    return hit is not None


def is_minor_course(course_id: str, minor_id: str, db_path: str) -> bool:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    hit = cur.execute("""
        SELECT 1 FROM MinorCourses WHERE minor_id = ? AND course_id = ? LIMIT 1
    """, (minor_id, course_id)).fetchone()
    conn.close()
    return hit is not None


def score_course_simple(course_id: str, db_path: str, majors: set, minors: set):
    # weights (tune later)
    W_MAJOR = 4.0
    W_MINOR = 2.0
    W_NO_PREREQ = 0.5

    score = 0.0
    reasons = []

    # Major relevance
    for mid in majors:
        if is_major_course(course_id, mid, db_path):
            score += W_MAJOR
            reasons.append("Required for your major")
            break

    # Minor relevance
    for nid in minors:
        if is_minor_course(course_id, nid, db_path):
            score += W_MINOR
            reasons.append("Counts toward your minor")
            break

    # Bonus: no prereqs
    prereqs = get_prerequisites(course_id, db_path)
    if len(prereqs) == 0:
        score += W_NO_PREREQ
        reasons.append("No prerequisites")

    return score, reasons[:3]

def main():
    with open("all_course_data.json", "r") as f:
        all_course_data = json.load(f)
        create_index(DB_PATH, all_course_data)
    

if __name__ == "__main__":
    main()
    
    # spring_2026 = filter_course_term(2026, "Spring")
    # for course in spring_2026:
    #     print(course[0])