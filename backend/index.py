import json

""" Load data from api.json into separate smaller indexes using course ID: 
    - by department
    - by instructor 
    - by upper/lower division level
    - by GE category """

# open all_course_data.json to read from
with open("all_course_data.json", "r") as f:
    all_course_data = json.load(f)

# for error checking 
# print(f"Total courses loaded: {len(all_course_data)}")

# create department index
""" Department index will be used to recommend major/minor related courses """
dept_index = {}

for c in all_course_data:
    course_id = c["id"]
    dept = c["department"]

    if dept not in dept_index:
        dept_index[dept] = []

    dept_index[dept].append(course_id)

with open("dept_index.json", "w") as f:
    json.dump(dept_index, f, indent=2)

# create instructor index --> map instructor to course
""" Instructor index will be used to choose preferred professors and may recommend classes based on those selected"""
instructor_index = {}

for c in all_course_data:
    course_id = c["id"]
    instructors = c.get("instructors", [])

    for instr in instructors:
        name = instr["name"]

        if name not in instructor_index:
            instructor_index[name] = []
        
        instructor_index[name].append(course_id)

with open("instructor_index.json", "w") as f:
    json.dump(instructor_index, f, indent=2)

# create level index to denote upper/lower division courses 
""" Level index will be used to recommend courses based on class standing """
level_index = {}

for c in all_course_data:
    course_id = c["id"]
    level = c.get("courseLevel", "Unknown")

    if level not in level_index:
        level_index[level] = []
    
    level_index[level].append(course_id)

with open("level_index.json", "w") as f:
    json.dump(level_index, f, indent=2)

# create GE index to organize courses into GE categories
""" GE index will be used to recommend courses based on GE requirements left for graduation """
ge_index = {}

for c in all_course_data:
    course_id = c["id"]

    ge_list = c.get("geList", [])

    if not ge_list:
        continue

    for ge in ge_list:
        if ge not in ge_index:
            ge_index[ge] = []
        
        ge_index[ge].append(course_id)

with open("ge_index.json", "w") as f:
    json.dump(ge_index, f, indent=2)
