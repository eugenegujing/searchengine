
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

QUARTERS = {

    "fall": "Fall",
    "spring": "Spring",
    "summer1": "Summer1",
    "summer2": "Summer2",
    "summer10wk": "Summer10wk",
    "winter": "Winter"
}


def hour_minute_to_time(hour, minute):
    if (minute == 0 or minute == "0"):
        minute = "00"
    return f"{hour}:{minute}"

def time_to_hour_minute(time):
    time = time.split(":")
    return {"hour": int(time[0]), "minute": int(time[1])}

def query_result_to_list(query_result):
    """
    used for results from queries only selecting one item
        [("X",), ("Y",), ("Z"),] => ["X", "Y", "Z"]
    """
    res = []
    for result in query_result:
        res.append(result[0])
    return res