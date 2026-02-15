import requests
import json

""" Load data from Anteater API into json file """

BASE_URL = "https://anteaterapi.com/v2/rest/coursesCursor" # load API url
TAKE = 100 # load data in batches

def fetch_courses(cursor=None, take=TAKE):
    params = {}
    params["take"] = take

    if cursor is not None:
        params["cursor"] = cursor

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    response_data = response.json()
    data = response_data.get("data")

    # check if data exists --> prevent crashes
    if data is None:
        items = []
        next_cursor = None
    # extract items and nextCursor if data exists
    else:
        items = data.get("items", [])
        next_cursor = data.get("nextCursor")

    return items, next_cursor

def main():
    cursor = None
    batch_number = 1
    all_course_data = []

    while True:
        items, cursor = fetch_courses(cursor)

        # print batch info
        print(f"Batch {batch_number}: Fetched {len(items)} courses")

        # store course data
        for item in items:
            all_course_data.append(item)
        
        batch_number += 1

        if not cursor:
            print("All courses fetched.")
            break

    # write all course data to json file
    with open("all_course_data.json", "w") as f:
        json.dump(all_course_data, f)

    print(f"Total courses saved to all_course_data.json: {len(all_course_data)}")

if __name__ == "__main__":
    main()