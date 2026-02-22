import requests
import json
import time

""" Load data from Anteater API into json files """

COURSEDATA_URL = "https://anteaterapi.com/v2/rest/coursesCursor" # load API url
MAJOR_URL = "https://anteaterapi.com/v2/rest/programs/majors"
MINOR_URL = "https://anteaterapi.com/v2/rest/programs/minors"
TERM_URL = "https://anteaterapi.com/v2/rest/websoc/terms"

TAKE = 100 # load data in batches
SLEEP_TIME = 0.5 # avoid overloading api

def fetch_courses(cursor=None, take=TAKE):
    batch_number = 1
    all_courses = []

    while True:
        params = {"take": take}

        if cursor is not None:
            params["cursor"] = cursor

        response = requests.get(COURSEDATA_URL, params=params)
        response.raise_for_status()
        data = response.json().get("data")

        # check if data exists --> prevent crashes
        if data is None:
            items = []
            cursor = None
        # extract items and nextCursor if data exists
        else:
            items = data.get("items", [])
            cursor = data.get("nextCursor")

        # store batch
        all_courses.extend(items)

        print(f"Batch {batch_number}: Fetched {len(items)} courses")
        batch_number += 1

        # stop if no more data
        if not cursor:
            break

    # normalize terms
    for course in all_courses:
        if course.get("terms") and isinstance(course["terms"][0], str):
            course["terms"] = [{"term": t, "sections": []} for t in course["terms"]]

    # save initial course data --> term data will be added later
    with open("all_course_data.json", "w") as f:
        json.dump(all_courses, f, indent=2)

    print(f"Total courses saved to course_information.json: {len(all_courses)}")

    return all_courses

def fetch_majors():
    response = requests.get(MAJOR_URL)
    response.raise_for_status()
    majors = response.json().get("data", [])

    # check if data exists
    if majors is None:
        return []
    
    # fetch requirements for each major
    all_major_data = []

    # retrieve all major ids and extract data from api
    for major in majors:
        program_id = major["id"]
        URL = f"https://anteaterapi.com/v2/rest/programs/major?programId={program_id}"
        response = requests.get(URL)
        response.raise_for_status()
        requirements = response.json().get("data", [])

        # merge major information with requirements
        major_copy = major.copy()
        major_copy["requirements"] = requirements

        all_major_data.append(major_copy)
        time.sleep(SLEEP_TIME)  # sleep 100ms between requests --> avoid client error
    
    # write to json file
    with open("all_major_data.json", "w") as f:
        json.dump(all_major_data, f, indent=2)

    print(f"Saved {len(all_major_data)} majors.")

def fetch_minors():
    response = requests.get(MINOR_URL)
    response.raise_for_status()
    minors = response.json().get("data", [])

    # check if data exists
    if not minors:
        return []
    
    # fetch requirements for each minor
    all_minor_data = []

    # retrieve all minor ids and extract data from api
    for minor in minors:
        program_id = minor["id"]
        URL = f"https://anteaterapi.com/v2/rest/programs/minor?programId={program_id}"
        response = requests.get(URL)
        response.raise_for_status()
        requirements = response.json().get("data", [])

        # merge minor information with requirements
        minor_copy = minor.copy()
        minor_copy["requirements"] = requirements

        all_minor_data.append(minor_copy)
        time.sleep(SLEEP_TIME)  # sleep 100ms between requests --> avoid client error
    
    # write to json file
    with open("all_minor_data.json", "w") as f:
        json.dump(all_minor_data, f, indent=2)

    print(f"Saved {len(all_minor_data)} minors.")

def fetch_specializations():
    pass

def fetch_terms():
    response = requests.get(TERM_URL)
    response.raise_for_status()
    term_list = response.json().get("data", [])

    terms = []

    # fetch year and quarter from all valid terms 
    # will be used to query into Websoc for specific building info, start and end times
    for term in term_list:
        short_name = term.get("shortName", "")
        
        if short_name:
            year, quarter = short_name.split()
            terms.append((year, quarter))
    
    return terms

def fetch_term_info(year, quarter):
    # query websoc
    URL = f"https://anteaterapi.com/v2/rest/websoc?year={year}&quarter={quarter}"
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json().get("data", [])

    extracted = []

    # websoc structure: schools --> depts --> courses --> sections --> meeting info
    for school in data.get("schools", []):
        for dept in school.get("departments", []):
            dept_code = dept.get("deptCode")
            for course in dept.get("courses", []):
                for section in course.get("sections", []):
                    for meeting in section.get("meetings", []):
                        extracted.append({
                            "department": dept_code, 
                            "courseNumber": course.get("courseNumber"),
                            "sectionCode": section.get("sectionCode"),
                            "building": meeting.get("building"),
                            "room": meeting.get("room"),
                            "startTime": meeting.get("startTime"),
                            "endTime": meeting.get("endTime"),
                            "days": meeting.get("days"),
                            "term": f"{year} {quarter}"
                        })

    return extracted

def build_course_lookup(all_courses):
    lookup = {}
    for course in all_courses:
        key = (course["department"], course["courseNumber"])
        lookup[key] = course
    return lookup

def merge_offerings(all_courses, offerings):
    course_lookup = build_course_lookup(all_courses)

    for offering in offerings:
        key = (offering["department"], offering["courseNumber"])

        if key not in course_lookup:
            continue

        course = course_lookup[key]
        term_string = offering["term"]

        # find matching term object
        for term in course["terms"]:
            if term["term"] == term_string:
                term["sections"].append({
                    "sectionCode": offering["sectionCode"],
                    "building": offering["building"],
                    "room": offering["room"],
                    "startTime": offering["startTime"],
                    "endTime": offering["endTime"],
                    "days": offering["days"]
                })
                break

if __name__ == "__main__":
    fetch_majors()
    fetch_minors()

    all_courses = fetch_courses()
    # with open("all_course_data.json", "r") as f:
    #     all_courses = json.load(f)
    terms = fetch_terms()

    # fetch websoc offering per term and merge information into all_course_data
    for year, quarter in terms:
        print(f"Fetching WebSOC for {year} {quarter}")
        offerings = fetch_term_info(year, quarter)
        merge_offerings(all_courses, offerings)
        time.sleep(0.6)

    with open("all_course_data.json", "w") as f:
       json.dump(all_courses, f, indent=2)
