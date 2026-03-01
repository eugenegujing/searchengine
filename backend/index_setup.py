import sqlite3
import json
from pathlib import Path

import Index.sql_index as sql_index
from Index.index_search import *
import data_collection

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

    db_path = Path(DB_PATH)
    db_path.unlink(missing_ok=True)

    sql_index.create_index(DB_PATH, all_course_data, all_major_data, 
                 all_minor_data, all_spec_data, n_terms)
    
def retrieve_api_course_data():
    data_jsons = [

        Path("all_course_data.json"), 
        Path("all_major_data.json"), 
        Path("all_minor_data.json"), 
        Path("all_specialization_data.json")

    ]
    for file in data_jsons:
        file.unlink(missing_ok=True)
    data_collection.fetch_courses()
    data_collection.fetch_majors()
    data_collection.fetch_minors()
    data_collection.fetch_specializations()


if __name__ == "__main__":

    
    #########################################################
    # Comment out the lines below if you have already collected the api data
    #
    retrieve_api_course_data()
    #
    #########################################################

    # Loads the n most recent terms from the API
    n_terms = 10
    setup_index(n_terms)

    
    

    