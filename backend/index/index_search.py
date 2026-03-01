import sqlite3
from collections import defaultdict
from Index.common import *

#===================================================================================

class CourseSearchException(Exception):
    pass

#===================================================================================

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
    def __init__(self, db_path):
        self.db_path = db_path
        self.courses = set()
        self.majors = set()
        self.minors = set()
        self.specializations = set()
        self.completed = []

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
        elif (type(course_id) is not str):
            raise ValueError
        self.completed.append(course_id)

    def _add_sqlite_result_to_set(self, sqlite_res: tuple, set_out: set):
        """
        takes sqlite output in the form of ((X,), (Y,), (Z,)) and adds X, Y, and Z to a set
        """
        for res in sqlite_res:
            set_out.add(res[0])

    def search(self, year=None, quarter=None):
        quarter = quarter.lower()
        for major_id in self.majors:
            sql_out = filter_course_major(major_id, self.db_path)
            self._add_sqlite_result_to_set(sql_out, self.courses)

        for minor_id in self.minors:
            sql_out = filter_course_minor(minor_id, self.db_path)
            self._add_sqlite_result_to_set(sql_out, self.courses)
        
        for course_id in set(self.completed):
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
    
    def get_major_requirement_completion(self):
        """
        returns a dictionary containing requirement completion information for each major

        Return format:
            Key: major id
            Value: tuple with requirement information => (completed, in progress, not started)
        """
        res = {}
        for major in self.majors:
            res[major] = filter_major_requirements(self.db_path, major, self.completed)
        
        return res
        
    
    def get_minor_requirement_completion(self):
        pass

#===================================================================================

def get_majors(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    return cursor.execute("SELECT * FROM Majors").fetchall()

def get_minors(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    return cursor.execute("SELECT * FROM Minors").fetchall()

def get_specializations(db_path, major):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    return cursor.execute("SELECT specialization_id, specialization_name FROM Specializations").fetchall()


def filter_course_term(year: int, quarter: str, db_path):
    quarter = quarter.lower()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    assert((quarter in QUARTERS.keys()) or (quarter is None), "Invalid quarter argument")
    if (quarter is not None):
        quarter = QUARTERS[quarter]
    if (year and quarter):
        query = "SELECT * FROM Terms WHERE year = ? AND quarter = ?"
        results = cursor.execute(query, (year, quarter)).fetchall()
    elif not year:
        query = "SELECT * FROM Terms WHERE quarter = ?"
        results = cursor.execute(query, (quarter)).fetchall()
    elif not quarter:
        query = "SELECT * FROM Terms WHERE year = ?"
        results = cursor.execute(query, (year)).fetchall()
    else:
        results = cursor.execute("SELECT * FROM Terms").fetchall()

    return results

def filter_course_major(major_id: str, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT course_id FROM MajorCourses WHERE major_id = ? AND course_id IS NOT NULL"
    results = cursor.execute(query, (major_id,)).fetchall()

    return results

def filter_course_minor(minor_id: str, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT course_id FROM MinorCourses WHERE minor_id = ? AND course_id IS NOT NULL"
    results = cursor.execute(query, (minor_id,)).fetchall()

    return results

def filter_specialization(specialization_id: str, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT course_id FROM SpecializationCourses WHERE specialization_id = ? AND course_id IS NOT NULL"
    results = cursor.execute(query, (specialization_id,)).fetchall()

    return results

def filter_major_requirements(db_path, major, completed_courses: list=None):
    """
    Retrieves requirement progress for a given major based on already completed courses

    Returns:
        complete=> dictionary containing titles of requirements as keys and which classes contributed towards it as values

        in_progress=> dictionary containing same corresponding data as above

        not_started=> set containing titles of requirements with no courses completed
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if (completed_courses is None):
        completed_courses = []
    completed_courses = completed_courses.copy()


    course_query = """
        SELECT group_label, course_count, requirement_label FROM MajorCourses 
        WHERE major_id = ? AND group_label IS NOT NULL
    """
    course_group_data = set(cursor.execute(course_query, (major,)).fetchall())
    
    parent_requirements = defaultdict(set)
    complete = defaultdict(list)
    in_progress = defaultdict(list)
    not_started = set()
    completion = {
        "complete": defaultdict(set),
        "inProgress": defaultdict(set),
        "notStarted": defaultdict(set)
    }
    completed_units = defaultdict(int)
    in_progress_requirements = defaultdict(set)
    incomplete_requirements = set()

    # for course based requirements

    for group in course_group_data:
        group_label = group[0]
        course_count = group[1]
        parent_requirement = group[2]
        completed_in_group = []

        if (parent_requirement):
            parent_requirements[parent_requirement].add(group_label)

        courses = cursor.execute("SELECT course_id, course_count FROM MajorCourses WHERE group_label = ?", (group_label,)).fetchall()
        for course in set(courses):
            course_id = course[0]
            if (course_id in completed_courses):
                completed_in_group.append(course_id)

        n_completed = len(completed_in_group)
        if (n_completed >= course_count):
            complete[group_label] = completed_in_group
        elif (n_completed > 0):
            in_progress[group_label] = completed_in_group
        else:
            not_started.add(group_label)


    # for unit based requirements

    completed_req_units = {}
    completed_req_courses = defaultdict(list)

    unit_query = """
        SELECT requirement_label FROM MajorCourses 
        WHERE major_id = ? AND group_label IS NULL
    """
    unit_requirements = set(cursor.execute(unit_query, (major,)).fetchall())
    for requirement_group in unit_requirements:
        requirement_label = requirement_group[0]
        courses = cursor.execute("SELECT course_id FROM MajorCourses WHERE requirement_label = ?", (requirement_label,)).fetchall()
        requirement_courses = set(query_result_to_list(courses))
        completed_unit_courses = []
        completed_units = 0
        
        for course in completed_courses:
            if (course in requirement_courses):
                completed_unit_courses.append(course)

        if (len(completed_unit_courses) > 0):
            # completed_req_units[requirement_label] = completed_units
            completed_req_courses[requirement_label].append(completed_unit_courses)
        else:
            not_started.add(requirement_group)

    
    while (len(completed_req_courses) > 0):
        # label, units_completed = completed_req_units.popitem()
        label, courses_completed = completed_req_courses.popitem()
        courses_completed = merge_requirement_course_lists(courses_completed)
        query = """
            SELECT requirement_type, requirement_count, parent_label
            FROM MajorRequirements 
            WHERE major_id = ? AND requirement_label = ? 
        """
        requirement = cursor.execute(query, (major, label)).fetchall()[0]
        req_type = requirement[0]
        req_count = requirement[1]
        parent = requirement[2]
        units_completed = get_units_from_course_lists(courses_completed, cursor=cursor)
        if (parent and req_type == "Unit"):
            completed_req_courses[parent].append(courses_completed)

        if (req_type == "Unit" and units_completed >= req_count):
            complete[label] = merge_requirement_courses(complete[label], courses_completed)

        elif (req_type == "Unit" and units_completed > 0):
            in_progress[label] = merge_requirement_courses(complete[label], courses_completed)

        if (parent):
            parent_requirements[parent].add(label)
        
    
    while (len(parent_requirements) > 0):

        requirement_label, children_reqs = parent_requirements.popitem()
        completed_requirements = complete.keys()
        in_progress_requirements = in_progress.keys()
        query = """
                SELECT requirement_type, requirement_count, parent_label
                FROM MajorRequirements 
                WHERE major_id = ? AND requirement_label = ?
                """
        requirement = cursor.execute(query, (major, requirement_label)).fetchall()[0]
        req_type = requirement[0]
        req_count = requirement[1]
        parent = requirement[2]
        req_completed_courses = []
        n_req_completed = 0
        n_in_progress = 0
        if (parent):
            parent_requirements[parent] = requirement_label


        for child in children_reqs:
            if (child in completed_requirements):
                n_req_completed += 1
                req_completed_courses = merge_requirement_courses(req_completed_courses, complete[child])
            elif (child in in_progress_requirements):
                n_in_progress += 1
                req_completed_courses = merge_requirement_courses(req_completed_courses, complete[child])
            
        if (n_req_completed > req_count):
            complete[requirement_label] = req_completed_courses
        elif (n_req_completed > 0):
            in_progress[requirement_label] = req_completed_courses

    return (complete, in_progress, not_started)


def get_units_from_course_lists(course_list: list, cursor=None, db_path=None):
    if (cursor is None and db_path is None):
        raise CourseSearchException("Must provide either database cursor or database path")
    if (cursor is None):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    course_counts = defaultdict(int)
    for course in course_list:
        course_counts[course] = max(course_counts[course], course_list.count(course))

    res = 0
    for course, course_count in course_counts.items():
        n_units = cursor.execute("SELECT min_units FROM Courses WHERE course_id = ?", (course,)).fetchall()[0][0]
        res += n_units * course_count

    return res

def merge_requirement_course_lists(course_lists: list[list]):
    res = []
    for course_list in course_lists:
        res = merge_requirement_courses(res, course_list)
    return res

def merge_requirement_courses(curr: list, new: list):
    course_counts = defaultdict(int)
    for course in set(curr.copy()):
        course_counts[course] = curr.count(course)
    for course in set(new.copy()):
        course_counts[course] = max(course_counts[course], new.count(course))
    res = []
    for course, count in course_counts.items():
        for _ in range(count):
            res.append(course)
    return res

def get_course_data(course_id: str, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM Courses WHERE course_id = ?"
    results = cursor.execute(query, (course_id,)).fetchall()

    return results

def get_course_data_from_term(course_id: str, year, quarter, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if (quarter.lower() in QUARTERS.keys()):
        quarter = QUARTERS[quarter.lower()]
    else:
        raise CourseSearchException(f"Tried to search for invalid quarter: {quarter}")
    
    query = "SELECT * FROM Terms WHERE course_id = ? AND year = ? AND quarter = ?"
    try:
        results = cursor.execute(query, (course_id, int(year), quarter,)).fetchall()
    except sqlite3.OperationalError as e:
        raise CourseSearchException(f"{e.sqlite_errorname}, {e.sqlite_errorcode}, {e.__str__()}")
    
    return results


def get_prerequisites(course_id: str, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT prereq_id FROM Prerequisites WHERE course_id = ?"
    results = cursor.execute(query, (course_id,)).fetchall()
    
    return results
