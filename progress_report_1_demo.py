import sqlite3
import json
from pathlib import Path

import sql_index
import data_collection

"""
    Demo script for progress report #1
"""

if __name__ == "__main__":
    #########################################################
    # Comment out the lines below if you have already 
    # collected the api data and created the database
    #
    db_path = Path(sql_index.DB_PATH)
    db_path.unlink(missing_ok=True)
    course_json = Path("all_course_data.json")
    course_json.unlink(missing_ok=True)
    data_collection.main()
    #
    #
    #########################################################

    sql_index.main()
    conn = sqlite3.connect(sql_index.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Majors(major_id, major_name, type, division) 
        VALUES ("BS-201", "Major in Computer Science", "B.S.", "Undergraduate");
    ''')     
    cursor.execute(''' 
       INSERT INTO MajorCourses(major_id, course_id)
        VALUES ("BS-201", "I&CSCI31");
    ''')
    cursor.execute('''           
        INSERT INTO MajorCourses(major_id, course_id)
        VALUES ("BS-201", "I&CSCI32");
    ''')
    cursor.execute('''
        INSERT INTO Majors(major_id, major_name, type, division) 
        VALUES ("BS-540", "Major in Mathematics", "B.S.", "Undergraduate");
    ''')   
    cursor.execute('''        
        INSERT INTO MajorCourses(major_id, course_id)
        VALUES ("BS-540", "MATH2A");
    ''')   
    cursor.execute('''            
        INSERT INTO MajorCourses(major_id, course_id)
        VALUES ("BS-540", "MATH2B");
    ''')
    conn.commit()

    cs_id = "BS-201"
    math_id = "BS-540"
    course_search = sql_index.CourseSearch()
    course_search.add_major(cs_id)
    course_search.add_prerequisite("MATH1B")
    res = course_search.search(2026, "Spring")
    print("Courses for CS Major in Spring 2026:")
    for course in res:
        print(course)
    course_search.add_major(math_id)
    res = course_search.search(2026, "Spring")
    print("\nCourses for CS and Math Double Major in Spring 2026")
    for course in res:
        print(course)

    course_search.add_prerequisite("I&CSCI31")
    res = course_search.search(2026, "Spring")
    print("\nCourses after prerequisites completed: I&CSCI31")
    for course in res:
        print(course)