import sqlite3
import json
from collections import defaultdict
from Index.index_search import *
from Index.common import *
import data_collection


def create_index(db_path: str, course_data: list[dict], major_data: list[dict], 
                 minor_data: list[dict], specialization_data: list[dict], n_terms=None):
    
    """
    create_index: creates tables and indexes for provided course data
        db_path: path to database
        type: str

        course_data: list of course json data collected from api
        type: list[dict]

    Database structure:
    
        Buildings: Building names and locations
        Courses: General course information
        GenEdRequirements: Stores which courses fulfill each GE category
        Majors: General major information
        MajorRequirements: Requirements needed to graduate with a given major
        MajorCourses: Stores required courses for each major as well as whcih requirements they fulfill
        Minors: General minor information
        MinorRequirements: Requirements needed to graduate with a given minor
        MinorCourses: Stores required courses for each minor as well as which requirements they fulfill
        Prerequisites: Stores which courses have prerequisites
        Specializations: Specialization information
        SpecializationRequirements: Requirements for each specialization
        SpecializationCourses Stores required courses for each specialization as well as which requirements they fulfill
        Terms: Stores term-specific course information
    
    """
    conn = sqlite3.connect(db_path)
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
            max_units INTEGER NOT NULL,
            repeatability TEXT,
            grading_option TEXT,
            corequisites TEXT
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
            PRIMARY KEY (section_code, year, quarter),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            FOREIGN KEY (building_id) REFERENCES Buildings(building_id)
        );
                         
        CREATE TABLE IF NOT EXISTS PrerequisitesOR (
            course_id TEXT,
            prereq_id TEXT,
            parent TEXT,
            PRIMARY KEY (course_id, prereq_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            FOREIGN KEY (prereq_id) REFERENCES Courses(course_id),
            FOREIGN KEY (parent) REFERENCES Courses(course_id) 
        );
                         
        CREATE TABLE IF NOT EXISTS PrerequisitesAND (
            course_id TEXT,
            prereq_id TEXT,
            parent TEXT,
            PRIMARY KEY (course_id, prereq_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            FOREIGN KEY (prereq_id) REFERENCES Courses(course_id),
            FOREIGN KEY (parent) REFERENCES Courses(course_id)         
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
                         
        CREATE TABLE IF NOT EXISTS MajorRequirements (
            major_id TEXT,
            requirement_type TEXT,
            requirement_label TEXT,
            requirement_count INTEGER,
            parent_label TEXT,
            PRIMARY KEY (major_id, requirement_label),
            FOREIGN KEY (major_id) REFERENCES Majors(major_id)
            FOREIGN KEY (parent_label) REFERENCES MajorRequirements(requirement_label)
        );
                         
        CREATE TABLE IF NOT EXISTS SchoolRequirements (
            major_id TEXT,
            requirement_name TEXT,
            PRIMARY KEY (major_id, requirement_name)
            FOREIGN KEY (major_id) REFERENCES Majors(major_id)
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
            FOREIGN KEY (requirement_label) REFERENCES MajorRequirements (requirement_label)
        );

        CREATE TABLE IF NOT EXISTS Minors (
            minor_id TEXT,
            minor_name TEXT NOT NULL
        );
                         
        CREATE TABLE IF NOT EXISTS MinorRequirements (
            minor_id TEXT,
            requirement_type TEXT,
            requirement_label TEXT,
            requirement_count INTEGER,
            parent_label TEXT,
            PRIMARY KEY (minor_id, requirement_label)
            FOREIGN KEY (minor_id) REFERENCES Minors(minor_id)
            FOREIGN KEY (parent_label) REFERENCES MinorRequirements(requirement_label)
        );
                         
        CREATE TABLE IF NOT EXISTS MinorCourses (
            minor_id TEXT,
            course_id TEXT,
            requirement_label TEXT,
            course_count INTEGER,
            group_label TEXT,
            PRIMARY KEY (minor_id, course_id, requirement_label, group_label),
            FOREIGN KEY (minor_id) REFERENCES Majors(minor_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id),
            FOREIGN KEY (requirement_label) REFERENCES MinorRequirements(requirement_label)
        );
                         
        CREATE TABLE IF NOT EXISTS Specializations (
            specialization_id TEXT PRIMARY KEY,
            specialization_name TEXT NOT NULL,
            major_id TEXT NOT NULL,
            FOREIGN KEY (major_id) REFERENCES Majors(major_id) 
        );
                         
        CREATE TABLE IF NOT EXISTS SpecializationRequirements (
            specialization_id TEXT,
            requirement_type TEXT,
            requirement_label TEXT,
            requirement_count INTEGER,
            parent_label TEXT,
            PRIMARY KEY (specialization_id, requirement_label),
            FOREIGN KEY (specialization_id) REFERENCES Specializations(specialization_id)
            FOREIGN KEY (parent_label) REFERENCES SpecializationRequirements(requirement_label)
        );
                         
        CREATE TABLE IF NOT EXISTS SpecializationCourses (
            specialization_id TEXT,
            course_id TEXT,
            requirement_label TEXT,
            course_count INTEGER,
            group_label TEXT, 
            PRIMARY KEY (specialization_id, course_id, requirement_label, group_label),
            FOREIGN KEY (specialization_id) REFERENCES Majors(specialization_id),
            FOREIGN KEY (course_id) REFERENCES Courses(course_id)
            FOREIGN KEY (requirement_label) REFERENCES SpecializationRequirements(requirement_label)
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
        c_id = course["id"]
        c_dep = course["department"]
        c_number = course["courseNumber"]
        c_title = course["title"]
        c_min_units = course["minUnits"]
        c_max_units = course["maxUnits"]
        c_repeatability = course["repeatability"]
        c_grading_option = course["gradingOption"]
        c_coreqs = course["corequisites"]
        cursor.execute('''
            INSERT OR REPLACE INTO Courses(course_id, department, 
                                           course_number, course_title,
                                           min_units, max_units,
                                           repeatability, grading_option,
                                           corequisites)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (c_id, c_dep, c_number, c_title, c_min_units, c_max_units, 
              c_repeatability, c_grading_option, c_coreqs))    

        for ge in course["geList"]:
            ge_id = GE_CATEGORIES[ge]
            cursor.execute('''
                INSERT OR REPLACE INTO GenEdRequirements(course_id, ge_category, ge_id)
                VALUES (?, ?, ?)       
            ''', (c_id, ge, ge_id))

        # for prereq in course["prerequisites"]:
        #     prereq_id = prereq["id"]
        #     cursor.execute('''
        #         INSERT OR REPLACE INTO Prerequisites(course_id, prereq_id)
        #         VALUES (?, ?)
        #     ''', (c_id, prereq_id))
    
    print("Processing Major Requirement Data")
    for major in major_data:
        insert_major(major, cursor=cursor, db_path=db_path)

    print("Processing Minor Requirement Data")
    for minor in minor_data:
        insert_minor(minor, cursor=cursor, db_path=db_path)

    print("Processing Specialization Requirements")
    for specialization in specialization_data:
        insert_specialization(specialization, cursor=cursor, db_path=db_path)

    terms = data_collection.fetch_terms()
    if (n_terms is not None):
        n_terms = min(n_terms, len(terms))
        terms = terms[:n_terms]
    for term in terms:
        year, quarter = term
        print(f"Inserting into term {quarter} {year}")
        insert_term(year, quarter, db_path, cursor=cursor, update=False)
        
    conn.commit()
    print("Database created at", db_path)
    return conn

def insert_major(major: dict, db_path, cursor=None):
    if (cursor is None):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    maj_id = major["id"]
    maj_name = major["name"]
    maj_type = major["type"]
    maj_division = major["division"]
    maj_requirements = major["requirements"]["requirements"]
    school_requirements = major["requirements"]["schoolRequirements"]

    cursor.execute('''
        INSERT OR REPLACE INTO Majors(major_id, major_name, type, division)
        VALUES (?, ?, ?, ?)
    ''', (maj_id, maj_name, maj_type, maj_division))

    for req in maj_requirements:
        insert_major_requirement(maj_id, req, db_path, cursor=cursor)

    # TODO: COMPLETE SCHOOL REQUIREMENT INSERTION INTO DATABASE
    # if (school_requirements):
    #     for school_req in school_requirements:
    #         insert_major_requirement(maj_id, school_req, cursor, db_path)

def insert_major_requirement(major: str, requirement: dict, db_path, parent_label=None, cursor=None):
    if (cursor is None):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    req_label = requirement["label"]
    req_type = requirement["requirementType"]
    if (req_type == "Group"):
        req_count = requirement["requirementCount"]
        cursor.execute('''
            INSERT OR REPLACE INTO MajorRequirements(major_id, requirement_type, 
                                                     requirement_label, requirement_count,
                                                     parent_label)
            VALUES (?, ?, ?, ?, ?)
        ''', (major, req_type, req_label, req_count, parent_label))
        
        for recursive_req in requirement["requirements"]:
            insert_major_requirement(major, recursive_req, db_path, req_label, cursor)


    elif (req_type == "Marker"):
        cursor.execute('''
            INSERT OR REPLACE INTO MajorRequirements(major_id, requirement_type, requirement_label, parent_label)
            VALUES (?, ?, ?, ?)
        ''', (major, req_type, req_label, parent_label))


    elif (req_type == "Unit"):
        unit_count = requirement["unitCount"]
        cursor.execute('''
            INSERT OR REPLACE INTO MajorRequirements(major_id, requirement_type, 
                                                     requirement_label, requirement_count, 
                                                     parent_label)
            VALUES (?, ?, ?, ?, ?)
        ''', (major, req_type, req_label, unit_count, parent_label))

        for course in requirement["courses"]:
            cursor.execute('''
                INSERT OR REPLACE INTO MajorCourses(major_id, course_id, requirement_label)
                VALUES (?, ?, ?)
            ''', (major, course, req_label))

    elif (req_type == "Course"):
        course_count = requirement["courseCount"]
        courses = requirement["courses"]
        if (len(courses) == 0):
            cursor.execute('''
                INSERT OR REPLACE INTO MajorCourses(major_id, course_id, requirement_label,
                                                    course_count, group_label)
                VALUES (?, ?, ?, ?, ?)
            ''', (major, None, parent_label, course_count, req_label))
            
        else:
            for course in requirement["courses"]:
                cursor.execute('''
                    INSERT OR REPLACE INTO MajorCourses(major_id, course_id, requirement_label,
                                                        course_count, group_label)
                    VALUES (?, ?, ?, ?, ?)
                ''', (major, course, parent_label, course_count, req_label))

    return

def insert_minor(minor: dict, db_path, cursor=None):
    if (cursor is None):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

    min_id = minor["id"]
    min_name = minor["name"]
    min_requirements = minor["requirements"]["requirements"]

    cursor.execute('''
        INSERT OR REPLACE INTO Minors(minor_id, minor_name)
        VALUES (?, ?)
    ''', (min_id, min_name))

    for req in min_requirements:
        insert_minor_requirement(min_id, req, cursor=cursor, db_path=db_path)
    

def insert_minor_requirement(minor: str, requirement: dict, db_path, parent_label=None, cursor=None):
    if (cursor is None):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    req_label = requirement["label"]
    req_type = requirement["requirementType"]
    if (req_type == "Group"):
        req_count = requirement["requirementCount"]
        cursor.execute('''
            INSERT OR REPLACE INTO MinorRequirements(minor_id, requirement_type, 
                                                     requirement_label, requirement_count,
                                                     parent_label)
            VALUES (?, ?, ?, ?, ?)
        ''', (minor, req_type, req_label, req_count, parent_label))
        
        for recursive_req in requirement["requirements"]:
            insert_minor_requirement(minor, recursive_req, db_path, req_label, cursor)

    elif (req_type == "Unit"):
        unit_count = requirement["unitCount"]
        cursor.execute('''
            INSERT OR REPLACE INTO MinorRequirements(minor_id, requirement_type, 
                                                     requirement_label, requirement_count,
                                                     parent_label)
            VALUES (?, ?, ?, ?, ?)
        ''', (minor, req_type, req_label, unit_count, parent_label))

        for course in requirement["courses"]:
            cursor.execute('''
                INSERT OR REPLACE INTO MinorCourses(minor_id, course_id, requirement_label)
                VALUES (?, ?, ?)
            ''', (minor, course, req_label))

    elif (req_type == "Course"):
        course_count = requirement["courseCount"]
        courses = requirement["courses"]
        if (len(courses) == 0):
            cursor.execute('''
                INSERT OR REPLACE INTO MinorCourses(minor_id, course_id, requirement_label,
                                                    course_count, group_label)
                VALUES (?, ?, ?, ?, ?)
            ''', (minor, None, parent_label, course_count, req_label))
            
        else:
            for course in requirement["courses"]:
                cursor.execute('''
                    INSERT OR REPLACE INTO MinorCourses(minor_id, course_id, requirement_label,
                                                        course_count, group_label)
                    VALUES (?, ?, ?, ?, ?)
                ''', (minor, course, parent_label, course_count, req_label))

    return

def insert_specialization(specialization: dict, db_path, cursor=None):
    if (cursor is None):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    spec_id = specialization["id"]
    spec_major = specialization["majorId"]
    spec_name = specialization["name"]
    spec_requirements = specialization["requirements"]["requirements"]
    
    cursor.execute('''
        INSERT OR REPLACE INTO Specializations(specialization_id, specialization_name, major_id)
        VALUES (?, ?, ?)
    ''', (spec_id, spec_name, spec_major))

    for req in spec_requirements:
        insert_specialization_requirement(spec_id, req, db_path, cursor=cursor)

def insert_specialization_requirement(specialization: str, requirement: dict, db_path, parent_label=None, cursor=None):
    if (cursor is None):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    req_label = requirement["label"]
    req_type = requirement["requirementType"]
    if (req_type == "Group"):
        req_count = requirement["requirementCount"]
        cursor.execute('''
            INSERT OR REPLACE INTO SpecializationRequirements(specialization_id, requirement_type, 
                                                     requirement_label, requirement_count,
                                                     parent_label)
            VALUES (?, ?, ?, ?, ?)
        ''', (specialization, req_type, req_label, req_count, parent_label))
        
        for recursive_req in requirement["requirements"]:
            insert_specialization_requirement(specialization, recursive_req, db_path, req_label, cursor)

    elif (req_type == "Unit"):
        unit_count = requirement["unitCount"]
        cursor.execute('''
            INSERT OR REPLACE INTO SpecializationRequirements(specialization_id, requirement_type, 
                                                     requirement_label, requirement_count, parent_label)
            VALUES (?, ?, ?, ?, ?)
        ''', (specialization, req_type, req_label, unit_count, parent_label))

        for course in requirement["courses"]:
            cursor.execute('''
                INSERT OR REPLACE INTO SpecializationCourses(specialization_id, course_id, requirement_label)
                VALUES (?, ?, ?)
            ''', (specialization, course, req_label))

    elif (req_type == "Course"):
        course_count = requirement["courseCount"]
        courses = requirement["courses"]
        if (len(courses) == 0):
            cursor.execute('''
                INSERT OR REPLACE INTO SpecializationCourses(specialization_id, course_id, requirement_label,
                                                    course_count, group_label)
                VALUES (?, ?, ?, ?, ?)
            ''', (specialization, None, parent_label, course_count, req_label))
            
        else:
            for course in requirement["courses"]:
                cursor.execute('''
                    INSERT OR REPLACE INTO SpecializationCourses(specialization_id, course_id, requirement_label,
                                                        course_count, group_label)
                    VALUES (?, ?, ?, ?, ?)
                ''', (specialization, course, parent_label, course_count, req_label))

    return

def insert_major_course(major, parent_label, course_requirement, cursor):
    course_count = course_requirement["courseCount"]
    group_label = course_requirement["label"]
    for course in course_requirement["courses"]:
        cursor.execute('''
            INSERT OR REPLACE INTO MajorCourses(major_id, course_id, requirement_label,
                                                course_count, group_label)
            VALUES (?, ?, ?, ?, ?)
        ''', (major, course, parent_label, course_count, group_label))


def insert_term(year: int, quarter: str, db_path, *, cursor=None, update=False):
    quarter_lower = quarter.lower()
    conn = None
    if (quarter_lower in QUARTERS.keys()):
        quarter = QUARTERS[quarter_lower]
    if (cursor is None):
        assert(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    term = data_collection.fetch_term_info(year, quarter)
    if (update):
        query = """
            UPDATE Terms
            SET building_id = ?,
                room_number = ?,
                start_time = ?,
                end_time = ?,
                days = ?,
                restrictions = ?,
                maxCapacity = ?,
                num_currently_enrolled = ?,
                num_on_waitlist = ?,
                is_cancelled = ?
            WHERE section_code = ? AND year = ? AND quarter = ?;
        """

        for course in term:
            start_time = course["startTime"]
            end_time = course["endTime"]
            
            if (start_time is not None):
                start_time = hour_minute_to_time(start_time["hour"], start_time["minute"])
            else:
                start_time = "TBA"

            if (end_time is not None):
                end_time = hour_minute_to_time(end_time["hour"], end_time["minute"])
            else:
                end_time = "TBA"

            days = course["days"]
            if (days is None):
                days = "TBA"
            restrictions = course["restrictions"]
            max_capacity = course["maxCapacity"]
            currently_enrolled = course["numCurrentlyEnrolled"]["totalEnrolled"]
            waitlist_cap = course["numWaitlistCap"]
            num_on_waitlist = course["numOnWaitlist"]
            is_cancelled = int(course["isCancelled"])

            args = ( course["buildingCode"], course["roomNumber"], start_time, 
                    end_time, days, restrictions, max_capacity, currently_enrolled, 
                    waitlist_cap, num_on_waitlist, is_cancelled)
            
            cursor.execute(query, args)


    else:
        query = """
            INSERT OR REPLACE INTO TERMS(course_id, section_code, section_type, 
                                        year, quarter, building_id, room_number,
                                        start_time, end_time, days,restrictions, 
                                        max_capacity, num_currently_enrolled,
                                        waitlist_capacity, num_on_waitlist,
                                        is_cancelled)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        for course in term:
            course_id = "".join(course["department"].split()) + course["courseNumber"]
            start_time = course["startTime"]
            end_time = course["endTime"]

            if (start_time is not None):
                start_time = hour_minute_to_time(start_time["hour"], start_time["minute"])
            else:
                start_time = "TBA"

            if (end_time is not None):
                end_time = hour_minute_to_time(end_time["hour"], end_time["minute"])
            else:
                end_time = "TBA"
            
            days = course["days"]
            if (days is None):
                days = "TBA"
            restrictions = course["restrictions"]
            max_capacity = course["maxCapacity"]
            currently_enrolled = course["numCurrentlyEnrolled"]["totalEnrolled"]
            waitlist_cap = course["numWaitlistCap"]
            num_on_waitlist = course["numOnWaitlist"]
            is_cancelled = int(course["isCancelled"])

            args = (course_id, course["sectionCode"], course["sectionType"], 
                    year, quarter, course["buildingCode"], course["roomNumber"],
                    start_time, end_time, days, restrictions, max_capacity, 
                    currently_enrolled, waitlist_cap, num_on_waitlist, 
                    is_cancelled)
            
            cursor.execute(query, args)
        if (conn):
            conn.commit()


# def main(n_terms=20):
#     courses_file =  open("all_course_data.json", "r")
#     majors_file = open("all_major_data.json", "r")
#     minors_file = open("all_minor_data.json", "r")
#     specializations_file = open("all_specialization_data.json")
#     all_course_data = json.load(courses_file)
#     all_major_data = json.load(majors_file)
#     all_minor_data = json.load(minors_file)
#     all_spec_data = json.load(specializations_file)
#     create_index(DB_PATH, all_course_data, all_major_data, 
#                  all_minor_data, all_spec_data, n_terms)
#     courses_file.close()
#     majors_file.close()
#     minors_file.close()
#     specializations_file.close()


# if __name__ == "__main__":
    
#     main(3)
    
    # spring_2026 = filter_course_term(2026, "Spring")
    # for course in spring_2026:
    #     print(course[0])