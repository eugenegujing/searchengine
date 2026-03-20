import sqlite3
import json
from pathlib import Path

import index.sql_index as sql_index
import data_collection
from user_index import create_user_index

"""

    Run this file to load course API information into a database

"""

DB_PATH = "courses.db"

def setup_index(n_terms):
    courses_file =  open("all_course_data.json", "r")
    majors_file = open("all_major_data.json", "r")
    minors_file = open("all_minor_data.json", "r")
    specializations_file = open("all_specialization_data.json")
    all_course_data = json.load(courses_file)
    all_major_data = json.load(majors_file)
    all_minor_data = json.load(minors_file)
    all_spec_data = json.load(specializations_file)
    courses_file.close()
    majors_file.close()
    minors_file.close()
    specializations_file.close()

    all_grade_data = []
    grade_path = Path("all_grade_data.json")
    if grade_path.exists():
        with open(grade_path, "r") as f:
            all_grade_data = json.load(f)

    db_path = Path(DB_PATH)
    db_path.unlink(missing_ok=True)

    conn = sql_index.create_index(DB_PATH, all_course_data, all_major_data,
                                  all_minor_data, all_spec_data,
                                  all_grade_data, n_terms)
    conn.close()
    create_user_index()
    
    
    
def retrieve_api_course_data(force=False):
    data_jsons = [
        Path("all_course_data.json"),
        Path("all_major_data.json"),
        Path("all_minor_data.json"),
        Path("all_specialization_data.json"),
        Path("all_grade_data.json")
    ]

    if not force and all(f.exists() for f in data_jsons):
        print("JSON data files already exist, skipping download. Use --force to re-download.")
        return

    for file in data_jsons:
        try:
            file.unlink(missing_ok=True)
        except PermissionError:
            pass  # file in use — will be overwritten
    data_collection.fetch_courses()
    data_collection.fetch_majors()
    data_collection.fetch_minors()
    data_collection.fetch_specializations()

    # fetch grade data
    data_collection.fetch_grades()


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv

    retrieve_api_course_data(force=force)

    # Loads the n most recent terms from the API
    n_terms = 10
    setup_index(n_terms)
    

    
    

    