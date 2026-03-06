import unittest

import sqlite3
import sys
import index.sql_index as sql_index
import data_collection
from pathlib import Path
from Tests.helpers import *
from index.index_search import *
import json

TEST_DB_PATH = "Tests/test.db"
CREATE_TEST_DB = True
N_TERMS = 5

"""
TO RUN TESTS:

In the backend folder run:
    all tests: python -m Tests.index_query_tests
    specific test: python -m unittest Tests.index_query_tests.[testClass].[testName]
"""

class TestSQLIndex(unittest.TestCase):

    def test_term_query(self):
        query_results = filter_course_term(2025, "Fall", TEST_DB_PATH)
        api_results = data_collection.fetch_term_info(2025, "Fall")
        for query_result in query_results:
            raise_assertion = True
            for api_result in api_results:
                course_id = "".join(api_result["department"].split()) + api_result["courseNumber"]
                section_code = int(api_result["sectionCode"])
                if ((query_result[0] == course_id) and (query_result[1] == section_code)):
                    api_results.remove(api_result)
                    raise_assertion = False
                    break
            if (raise_assertion):
                raise AssertionError
            
    def test_course_query(self):
        course = "I&CSCI31"
        query_results = get_course_data(course, TEST_DB_PATH)[0]
        self.assertEqual(query_results[0], course)
        self.assertEqual(query_results[1], "I&C SCI")
        self.assertEqual(query_results[2], "31")
        self.assertEqual(query_results[3], "Introduction to Programming")
        self.assertEqual(query_results[4], 4)
        self.assertEqual(query_results[5], 4)

    def test_course_term_query(self):
        course = "COMPSCI125"
        query_results = get_course_data_from_term(course, 2026, "Winter", TEST_DB_PATH)[0]
        self.assertEqual(query_results[0], course)
        self.assertEqual(query_results[1], 34080)
        self.assertEqual(query_results[2], "Lec")
        self.assertEqual(query_results[3], 2026)
        self.assertEqual(query_results[4], "Winter")
        self.assertEqual(query_results[5], "EH")
        self.assertEqual(query_results[6], "1200")
        self.assertEqual(query_results[7], "9:30")
        self.assertEqual(query_results[8], "10:50")
        self.assertEqual(query_results[9], "TuTh")

    def test_filter_course_major(self):
        major = "BS-201"
        self.maxDiff = None
        major_courses = set(ALL_CS_MAJOR_COURSES)
        query_results = query_result_to_list(filter_course_major(major, TEST_DB_PATH))
        for course in query_results:
            self.assertIn(course, major_courses)
        self.assertCountEqual(major_courses, set(query_results))
    
    def test_filter_course_minor(self):
        minor = "459"
        minor_courses = set(ALL_CS_MINOR_COURSES)
        query_results = query_result_to_list(filter_course_minor(minor, TEST_DB_PATH))
        for course in query_results:
            self.assertIn(course, minor_courses)
        self.assertCountEqual(minor_courses, set(query_results))

    def test_filter_specializations(self):
        specialization = "BS-201F"
        spec_courses = set(ALL_CS_INFORMATION_SPECIALIZATION_COURSES)
        query_results = query_result_to_list(filter_specialization(specialization, TEST_DB_PATH))
        for course in query_results:
            self.assertIn(course, spec_courses)
        self.assertCountEqual(spec_courses, set(query_results))

    def test_major_requirements(self):
        major = "BS-201"
        completed = ["I&CSCIH32", "I&CSCI33", "I&CSCI6B"]
        major_courses = set(ALL_CS_MAJOR_COURSES)
        for course in completed:
            major_courses.remove(course)
        major_courses.remove("I&CSCI31")
        major_courses.remove("I&CSCI32")
        query_results = filter_major_requirements(TEST_DB_PATH, major, completed)
        # for course in query_results:
        #     self.assertIn(course, major_courses)
        # self.assertCountEqual(major_courses, set(query_results))

    def test_more_major_requirements(self):
        major = "BS-201"
        completed = ["I&CSCIH32", "I&CSCI33", "I&CSCI6B",
                     "I&CSCI6D", "I&CSCI6N", "IN4MATX43",
                     "I&CSCI45C", "I&CSCI46", "I&CSCI51",
                     "I&CSCI53", "MATH2B", "STATS67",
                     "MATH2A", "COMPSCI161", "COMPSCI171",
                     "COMPSCI178", "COMPSCI125"]
        completed_reqs, in_progress, not_started = filter_major_requirements(TEST_DB_PATH, major, completed)
        self.assertIn('I&CSCI H32, 33', completed_reqs)
        self.assertIn('I&CSCI 31, 32, 33', in_progress)
        self.assertIn('Select I&CSCI 31-32-33 or I&CSCI H32-33', completed_reqs)
        self.assertIn('I&CSci 6B', completed_reqs)
        self.assertIn('I&CSci 6D', completed_reqs)
        self.assertIn('I&CSci 6N or Math 3A', completed_reqs)
        self.assertIn('In4matx 43', completed_reqs)
        self.assertIn('Math 2A', completed_reqs)
        self.assertIn('Math 2B', completed_reqs)
        self.assertIn('Stats 67', completed_reqs)
        self.assertIn('CompSci 161', completed_reqs)
        self.assertIn('I&CSci 45C', completed_reqs)
        self.assertIn('I&CSci 46', completed_reqs)
        self.assertIn('I&CSci 51', completed_reqs)
        self.assertIn('I&CSci 53', completed_reqs)
        self.assertIn('2 Project Courses', in_progress)
        self.assertIn('11 Upper-Div Electives', in_progress)
        self.assertIn('2 GE II courses (except ECON, MATH, School of Engineering or School of ICS courses)', not_started)
    
    def test_all_major_requirements(self):
        major = "BS-201"
        completed = ALL_CS_MAJOR_COURSES
        completed_reqs, in_progress, not_started = filter_major_requirements(TEST_DB_PATH, major, completed)
        self.assertEqual(len(in_progress), 0)
        self.assertEqual(len(not_started), 1) # Select a specialization

    def test_major_requirements_no_progress(self):
        major = "BS-201"
        completed_reqs, in_progress, not_started = filter_major_requirements(TEST_DB_PATH, major, [])
        self.assertEqual(len(completed_reqs), 0)
        self.assertEqual(len(in_progress), 0)
        self.assertIn('I&CSCI H32, 33', not_started)
        self.assertIn('I&CSCI 31, 32, 33', not_started)
        self.assertIn('Select I&CSCI 31-32-33 or I&CSCI H32-33', not_started)
        self.assertIn('I&CSci 6B', not_started)
        self.assertIn('I&CSci 6D', not_started)
        self.assertIn('I&CSci 6N or Math 3A', not_started)
        self.assertIn('In4matx 43', not_started)
        self.assertIn('Math 2A', not_started)
        self.assertIn('Math 2B', not_started)
        self.assertIn('Stats 67', not_started)
        self.assertIn('CompSci 161', not_started)
        self.assertIn('I&CSci 45C', not_started)
        self.assertIn('I&CSci 46', not_started)
        self.assertIn('I&CSci 51', not_started)
        self.assertIn('I&CSci 53', not_started)
        self.assertIn('2 Project Courses', not_started)
        self.assertIn('11 Upper-Div Electives', not_started)
        self.assertIn('2 GE II courses (except ECON, MATH, School of Engineering or School of ICS courses)', not_started)

    def test_unit_requirements(self):
        major = "BS-277"
        completed = ["ENGRMAE108", "ENGRMAE110"]
        completed_reqs, in_progress, not_started = filter_major_requirements(TEST_DB_PATH, major, completed)
        self.assertTrue("4 Add'l units in Upper-Div School of ENGR courses" in completed_reqs)
        self.assertTrue("8 units of Upper-Div ENGRMAE Courses" in completed_reqs)

    def test_unit_requirements_no_progress(self):
        major = "BS-277"
        completed_reqs, in_progress, not_started = filter_major_requirements(TEST_DB_PATH, major, [])
        self.assertEqual(len(completed_reqs), 0)
        self.assertEqual(len(in_progress), 0)
        

    def test_minor_requirements(self):
        minor = "459"
        completed = ["I&CSCIH32", "I&CSCI33", "I&CSCI6B",
                     "I&CSCI6D", "I&CSCI45C", "I&CSCI46", 
                     "I&CSCI51", "COMPSCI161"]
        completed_reqs, in_progress, not_started = filter_minor_requirements(TEST_DB_PATH, minor, completed)
        self.assertIn('I&CSCI 31+32 or I&CSCI H32', completed_reqs)
        # self.assertIn('I&CSCI 31+32', completed_reqs)
        self.assertIn('I&C Sci H32', completed_reqs)
        self.assertIn('I&C Sci 6D', completed_reqs)
        self.assertIn('I&C Sci 45C', completed_reqs)
        self.assertIn('I&C Sci 46', completed_reqs)
        self.assertIn('I&C Sci 51 or IN4MATX 43', completed_reqs)
        self.assertIn('2 upper-div courses from list', in_progress)

    def test_specialization_requirements(self):
        specialization = "BS-294D"
        completed = ["ENGRCEE164", "CBE176"]
        completed_reqs, in_progress, not_started = filter_specialization_requirements(TEST_DB_PATH, specialization, completed)
        # print(completed_reqs)
        # print(in_progress)
        # print(not_started)
        self.assertIn("One course (4 units) from CBE 176, 199, or MSE 141", completed_reqs)
        self.assertIn("7 units from Energy and the Environment Specialization courses", in_progress)
        self.assertIn("Minimum 11 units from Energy and the Environment Specializaion courses", in_progress)
        self.assertIn("Additional Technical Electives", not_started)
        

class TestCourseSearch(unittest.TestCase):
    def test_course_search_major_requirements(self):
        majors = ["BS-201", "BS-277"]
        course_search = CourseSearch(TEST_DB_PATH)
        for major in majors:
            course_search.add_major(major)
        completed = ["I&CSCIH32", "I&CSCI33", "I&CSCI6B",
                     "I&CSCI6D", "I&CSCI6N", "IN4MATX43",
                     "I&CSCI45C", "I&CSCI46", "I&CSCI51",
                     "I&CSCI53", "MATH2B", "STATS67",
                     "MATH2A", "COMPSCI161", "COMPSCI171",
                     "COMPSCI178", "COMPSCI125", 
                     "ENGRMAE108", "ENGRMAE110"]
        for course in completed:
            course_search.add_prerequisite(course)
        res = course_search.get_all_major_requirement_completion()
        completed_reqs, in_progress, not_started = res[majors[0]]
        self.assertIn('I&CSCI H32, 33', completed_reqs)
        self.assertIn('I&CSCI 31, 32, 33', in_progress)
        self.assertIn('I&CSci 6B', completed_reqs)
        self.assertIn('I&CSci 6D', completed_reqs)
        self.assertIn('I&CSci 6N or Math 3A', completed_reqs)
        self.assertIn('In4matx 43', completed_reqs)
        self.assertIn('Math 2A', completed_reqs)
        self.assertIn('Math 2B', completed_reqs)
        self.assertIn('Stats 67', completed_reqs)
        self.assertIn('CompSci 161', completed_reqs)
        self.assertIn('I&CSci 51', completed_reqs)
        self.assertIn('I&CSci 53', completed_reqs)
        self.assertIn('2 Project Courses', in_progress)
        self.assertIn('11 Upper-Div Electives', in_progress)
        self.assertIn('2 GE II courses (except ECON, MATH, School of Engineering or School of ICS courses)', not_started)
        
        completed_reqs, in_progress, not_started = res[majors[1]]
        self.assertTrue("4 Add'l units in Upper-Div School of ENGR courses" in completed_reqs)
        self.assertTrue("8 units of Upper-Div ENGRMAE Courses" in completed_reqs)

    def test_course_search_major_and_minor_requirements(self):
        major = "BS-277"
        minor = "459"
        completed = ["I&CSCIH32", "I&CSCI33", "I&CSCI6B",
                     "I&CSCI6D", "I&CSCI45C", "I&CSCI46", 
                     "I&CSCI51", "COMPSCI161","ENGRMAE108", 
                     "ENGRMAE110"]
        course_search = CourseSearch(TEST_DB_PATH)
        course_search.add_major(major)
        course_search.add_minor(minor)
        for course in completed:
            course_search.add_prerequisite(course)
        
        completed_reqs, in_progress, not_started = course_search.get_major_requirement_completion(major)
        self.assertTrue("4 Add'l units in Upper-Div School of ENGR courses" in completed_reqs)
        self.assertTrue("8 units of Upper-Div ENGRMAE Courses" in completed_reqs)
        
        completed_reqs, in_progress, not_started = course_search.get_minor_requirement_completion(minor)
        self.assertIn('I&CSCI 31+32 or I&CSCI H32', completed_reqs)
        self.assertIn('I&C Sci H32', completed_reqs)
        self.assertIn('I&C Sci 6D', completed_reqs)
        self.assertIn('I&C Sci 45C', completed_reqs)
        self.assertIn('I&C Sci 46', completed_reqs)
        self.assertIn('I&C Sci 51 or IN4MATX 43', completed_reqs)
        self.assertIn('2 upper-div courses from list', in_progress)

    def test_course_search_specialization_incomplete(self):
        major = "BS-201"
        specialization = "BS-201F"
        completed = ["I&CSCIH32", "I&CSCI33", "I&CSCI6B",
                     "I&CSCI6D", "I&CSCI6N", "IN4MATX43",
                     "I&CSCI45C", "I&CSCI46", "I&CSCI51",
                     "I&CSCI53", "MATH2B", "STATS67",
                     "MATH2A", "COMPSCI161", "COMPSCI171",
                     "COMPSCI178", "COMPSCI125", "COMPSCI121", 
                     "COMPSCI122A", "COMPSCI122B"]

        course_search = CourseSearch(TEST_DB_PATH)
        course_search.add_major(major)
        course_search.add_specialization(specialization)
        for course in completed:
            course_search.add_prerequisite(course)
        completed_reqs, in_progress, not_started = course_search.get_major_requirement_completion(major)
        self.assertIn('I&CSCI H32, 33', completed_reqs)
        self.assertIn('I&CSCI 31, 32, 33', in_progress)
        self.assertIn('I&CSci 6B', completed_reqs)
        self.assertIn('I&CSci 6D', completed_reqs)
        self.assertIn('I&CSci 6N or Math 3A', completed_reqs)
        self.assertIn('In4matx 43', completed_reqs)
        self.assertIn('Math 2A', completed_reqs)
        self.assertIn('Math 2B', completed_reqs)
        self.assertIn('Stats 67', completed_reqs)
        self.assertIn('CompSci 161', completed_reqs)
        self.assertIn('I&CSci 51', completed_reqs)
        self.assertIn('I&CSci 53', completed_reqs)
        self.assertIn('2 Project Courses', completed_reqs)
        self.assertIn('11 Upper-Div Electives', in_progress)
        self.assertIn('2 GE II courses (except ECON, MATH, School of Engineering or School of ICS courses)', not_started)

        completed_reqs, in_progress, not_started = course_search.get_specialization_requirement_completion(specialization)
        self.assertIn("CompSci 122B, 122C, 122D, 125, or 179", completed_reqs)
        self.assertIn("CompSci 122A", completed_reqs)
        self.assertIn("CompSci 121", completed_reqs)
        self.assertIn("CompSci 178", completed_reqs)
        self.assertIn("3 Add'l classes from list", in_progress)
        

    def test_course_search_specialization_complete(self):
        completed = ["I&CSCIH32", "I&CSCI33", "I&CSCI6B",
                     "I&CSCI6D", "I&CSCI6N", "IN4MATX43",
                     "I&CSCI45C", "I&CSCI46", "I&CSCI51",
                     "I&CSCI53", "MATH2B", "STATS67",
                     "MATH2A", "COMPSCI161", "COMPSCI171",
                     "COMPSCI178", "COMPSCI125", "COMPSCI121", 
                     "COMPSCI122A", "COMPSCI122B", "COMPSCI141",
                     "COMPSCI179"]
        major = "BS-201"
        specialization = "BS-201F"
        course_search = CourseSearch(TEST_DB_PATH)
        course_search.add_major(major)
        course_search.add_specialization(specialization)
        for course in completed:
            course_search.add_prerequisite(course)
        completed_reqs, in_progress, not_started = course_search.get_major_requirement_completion(major)
        self.assertIn('I&CSCI H32, 33', completed_reqs)
        self.assertIn('I&CSCI 31, 32, 33', in_progress)
        self.assertIn('I&CSci 6B', completed_reqs)
        self.assertIn('I&CSci 6D', completed_reqs)
        self.assertIn('I&CSci 6N or Math 3A', completed_reqs)
        self.assertIn('In4matx 43', completed_reqs)
        self.assertIn('Math 2A', completed_reqs)
        self.assertIn('Math 2B', completed_reqs)
        self.assertIn('Stats 67', completed_reqs)
        self.assertIn('CompSci 161', completed_reqs)
        self.assertIn('I&CSci 51', completed_reqs)
        self.assertIn('I&CSci 53', completed_reqs)
        self.assertIn('2 Project Courses', completed_reqs)
        self.assertIn('11 Upper-Div Electives', in_progress)
        self.assertIn('2 GE II courses (except ECON, MATH, School of Engineering or School of ICS courses)', not_started)

        completed_reqs, in_progress, not_started = course_search.get_specialization_requirement_completion(specialization)
        self.assertIn("CompSci 122B, 122C, 122D, 125, or 179", completed_reqs)
        self.assertIn("CompSci 122A", completed_reqs)
        self.assertIn("CompSci 121", completed_reqs)
        self.assertIn("CompSci 178", completed_reqs)
        self.assertIn("3 Add'l classes from list", completed_reqs)

if __name__ == "__main__":
    if (CREATE_TEST_DB):
        courses_file =  open("all_course_data.json", "r")
        majors_file = open("all_major_data.json", "r")
        minors_file = open("all_minor_data.json", "r")
        specializations_file = open("all_specialization_data.json")
        all_course_data = json.load(courses_file)
        all_major_data = json.load(majors_file)
        all_minor_data = json.load(minors_file)
        all_spec_data = json.load(specializations_file)
        sql_index.create_index(TEST_DB_PATH, all_course_data, 
                               all_major_data, all_minor_data, 
                               all_spec_data, N_TERMS)
        courses_file.close()
        majors_file.close()
        minors_file.close()
        specializations_file.close()
            
    unittest.main()