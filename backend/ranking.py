import re
from index.index_search import *


def compute_match_score(
        course_id, user_profile, 
        completed, ge_needed, 
        db_path, course_search=None,
        keywords=None, course=None, 
        major_course_ids=None, 
        prereq_map=None):
    """
    Compute a match score for a course given a user profile and optional keywords.
    :param course_id: string course identifier
    :param user_profile: dict of user info (preferredTime, courseFormat, maxUnits, geNeeded)
    :param completed: set of completed course ids
    :param ge_needed: set of GE categories user still needs
    :param keywords: list of keywords to boost score
    :param course: optional dict containing course info (ge list, time, units, format)
    :param major_course_ids: set of course_ids required for the user's major
    :param prereq_map: dict mapping course_id -> set of prereq_course_ids
    :return: (score:int, reasons:list[str])
    """
    score = 0
    reasons = []

    keywords = keywords or []
    if major_course_ids is None:
        major_course_ids = set()
    if prereq_map is None:
        prereq_map = {}

    current_schedule = user_profile.get("current_schedule", []) or []
    preferred_format = (user_profile.get("course_format") or "any").lower()
    preferred_time = (user_profile.get("preferred_time") or "any").lower()
    workload = (user_profile.get("workload") or "balanced").lower()
    major_id = user_profile.get("major")
    standing = user_profile.get("standing")

    course_time = course.get("time", "") if course else ""
    course_days = course.get("days", "") if course else ""
    course_building = course.get("building", "") if course else ""
    course_final_day = course.get("final_day", "") if course else ""
    course_format = (course.get("format", "in-person") if course else "in-person").lower()
    course_units = course.get("units", 4) if course else 4
    course_difficulty = (course.get("difficulty") or "medium").lower()
    course_restrictions = (course.get("restrictions")).split(" and ")
    sections = course.get("sections", []) if course else []

    # keywords
    if "easy" in keywords:
        score += 20
        reasons.append("Easy course")
    if "online" in keywords:
        score += 15
        reasons.append("Online format")
    if "morning" in keywords:
        if course and _check_time_preference("morning", course.get("time", "")):
            score += 10
            reasons.append("Morning class")
    if "afternoon" in keywords:
        if course and _check_time_preference("afternoon", course.get("time", "")):
            score += 10
            reasons.append("Afternoon class")
    if "evening" in keywords:
        if course and _check_time_preference("evening", course.get("time", "")):
            score += 10
            reasons.append("Evening class")

    # penalty for completed courses
    if course_id in completed:
        score -= 1000 # already taken
        reasons.append("Course already completed")
        return max(score, 0), reasons
    
    # cannot take J restricted courses if freshman or sophomore standing
    if "J" in course_restrictions and standing in ("Freshman", "Sophomore"):
        score -= 1000 # already taken
        reasons.append("Upperclassmen restriction")
        return max(score, 0), reasons

    # prerequisite completion
    if check_prerequisites(course_id, completed, db_path):
        score += 15
        reasons.append("Prerequisites completed")
    else:
        score -= 1000
        reasons.append("Prerequisites not satisfied")
    
    if major_id:
        major_rows = filter_course_major(major_id, db_path)
        major_course_set = set(r[0] for r in major_rows)

        course_dependencies = get_dependencies(course_id, db_path)
        useful_dependency_count = 0

        for dep in course_dependencies:
            dep_id = dep[0] if isinstance(dep, tuple) else dep
            if dep_id in major_course_set:
                or_courses = get_or_courses(dep_id, course_id, db_path)
                is_or_satisfied = len(completed.intersection(set(or_courses))) > 0
                if not is_or_satisfied:
                    useful_dependency_count += 1

        if useful_dependency_count > 0:
            dep_bonus = min(useful_dependency_count * 3, 15)
            score += dep_bonus
            reasons.append(f"Unlocks {useful_dependency_count} future major course(s)")

         # major requirement
        if course_search and course_id in course_search.get_remaining_courses():
            score += 30
            reasons.append("Required for your major")
    
    

    # GE needs
    if ge_needed:
        matching_ge = [g for g in course.get("ge", []) if g in ge_needed]
        if matching_ge:
            score += 20
            reasons.append(f"Satisfies GE need: {', '.join(matching_ge)}")

    # preferred time
    if preferred_time != "any" and _check_time_preference(preferred_time, course_time):
        score += 15
        reasons.append(f"Matches {preferred_time} preference")

    # units
    max_units = user_profile.get("max_units", 4)
    if isinstance(max_units, str):
        max_units = int(max_units) if max_units.isdigit() else 4

    if course_units <= max_units:
        score += 10
        reasons.append(f"Units <= {max_units}")

    # course format preference
    if preferred_format == course_format:
        score += 10
        reasons.append(f"Matches preferred format: {course_format}")
    elif preferred_format == "any":
        score += 2

    # workload preference
    if workload == "light" and course_units <= 3:
        score += 10
        reasons.append("Lower-unit course")
    elif workload == "heavy" and course_units >= 4:
        score += 5
        reasons.append("Higher-unit course")

    # grading / difficulty preference
    if workload == "light":
        if course_difficulty == "high":
            score -= 15
            reasons.append("Heavy grading workload")
        elif course_difficulty == "low":
            score += 10
            reasons.append("Light grading workload")
    elif workload == "heavy":
        if course_difficulty == "high":
            score += 5

    # section availability bonus
    # print(sections)
    if sections:
        score += min(len(sections), 5)
        reasons.append(f"{len(sections)} section option(s)")

        open_sections = 0
        low_wait_sections = 0
        for sec in sections:
            enrolled = _safe_int(sec.get("numCurrentlyEnrolled"), default=None)
            cap = _safe_int(sec.get("maxCapacity"), default=None)
            wait = _safe_int(sec.get("numOnWaitlist"), default=None)

            if cap is not None and enrolled is not None and enrolled < cap:
                open_sections += 1
            if wait is not None and wait == 0:
                low_wait_sections += 1

        if open_sections > 0:
            score += min(open_sections, 3) * 2
            reasons.append(f"{open_sections} section(s) with open seats")

        if low_wait_sections > 0:
            score += min(low_wait_sections, 2)
            reasons.append("Low or no waitlist enrollment")

    # contextual schedule penalties
    if _has_time_conflict(course_time, course_days, current_schedule):
        score -= 40
        reasons.append("Time conflict with current schedule")

    if _has_long_walk(course_building, current_schedule):
        score -= 10
        reasons.append("Long walking distance")

    if _has_final_conflict(course_final_day, current_schedule):
        score -= 15
        reasons.append("Finals conflict")



    #     # prerequisite bonus: if user completed a prereq for this course, +10
    #     if check_prerequisites(course_id, completed, db_path) and check_major_requirement_contribution(course_id, user_profile.get("major"), completed, db_path):
    #         score += 10
    #         reasons.append("Prerequisite completed")

    #     else:
    #         score -= 1000
    #         reasons.append("Prerequisite incomplete")

    #     # dependency bonus: if course is a prerequisite for many major courses, increase score
    #     course_dependencies = get_dependencies(course_id, db_path)
    #     for course_dependency in course_dependencies:
    #         if (course_dependency in filter_course_major(user_profile.get("major"), db_path)):
    #             or_courses = get_or_courses(course_dependency[0], course_id, db_path)
    #             if (len(or_courses) > 0):
    #                 is_or_satisfied = len(set(completed).intersection(set(or_courses)))
    #             else:
    #                 is_or_satisfied = 1
    #             if (not is_or_satisfied):
    #                 score += (len(course_dependencies)) / 10
    # course_search = CourseSearch(db_path)
    # course_search.add_major(user_profile.get("major"))
    # course_search.add_prerequisite_list(completed)
    # completed_reqs, in_progress_reqs, not_started_reqs = course_search.get_all_major_requirement_completion()
    # for course_list in completed_reqs.values():
    #     if (course_id in course_list):
        

    # ge needs
    # if course and ge_needed:
    #     matching_ge = [g for g in course.get("ge", []) if g in ge_needed]
    #     if matching_ge:
    #         score += 20
    #         reasons.append(f"Satisfies GE need: {', '.join(matching_ge)}")

    # # preferred time
    # preferred_time = user_profile.get("preferred_time", "any")
    # course_time = course.get("time", "") if course else ""
    # if preferred_time != "any":
    #     if _check_time_preference(preferred_time.lower(), course_time):
    #         score += 15
    #         reasons.append(f"Matches {preferred_time} preference")

    # # workload/units
    # max_units = user_profile.get("max_units", 4)
    # if isinstance(max_units, str):
    #     max_units = int(max_units) if max_units.isdigit() else 4
    # if course and course.get("units", 4) <= max_units:
    #     score += 10
    #     reasons.append(f"Units <= {max_units}")

    # # course format
    # course_format = course.get("format", "in-person") if course else "in-person"
    # preferred_format = user_profile.get("course_format", "any")
    # if preferred_format == "any" or preferred_format == course_format:
    #     score += 10
    #     reasons.append(f"Preferred format: {course_format}")

    # # workload preference
    # workload = (user_profile.get("workload") or "balanced").lower()
    # course_units = course.get("units", 4) if course else 4
    # if workload == "light" and course_units <= 3:
    #     score += 10
    #     reasons.append("Light workload course")
    # elif workload == "heavy" and course_units >= 4:
    #     score += 5

    return min(max(round(score,2), 0), 100), _dedupe_reasons(reasons)

def _check_time_preference(preference, time_str):
    """
    Check if a course time matches a time-of-day preference.
    DB stores times in 24h format like '10:00', '14:30' (no am/pm),
    so we extract the hour with regex.
    """
    if not time_str or time_str == "TBA":
        return False

    match = re.search(r'(\d{1,2}):(\d{2})', str(time_str))
    if not match:
        return False

    hour = int(match.group(1))

    if preference == "morning":
        return hour < 12
    elif preference == "afternoon":
        return 12 <= hour < 17
    elif preference == "evening":
        return hour >= 17

    return False


def _time_overlap(t1, t2):
    if not t1 or not t2:
        return False

    def parse_range(t):
        matches = re.findall(r'(\d{1,2}):(\d{2})', str(t))
        if len(matches) < 2:
            return None
        start = int(matches[0][0]) * 60 + int(matches[0][1])
        end = int(matches[1][0]) * 60 + int(matches[1][1])
        return start, end

    r1 = parse_range(t1)
    r2 = parse_range(t2)

    if not r1 or not r2:
        return False

    return not (r1[1] <= r2[0] or r2[1] <= r1[0])


def _split_days(days_value):
    if not days_value:
        return set()

    text = str(days_value).strip()
    if text == "TBA":
        return set()

    # handles strings like "MWF", "TuTh", "Mon Wed"
    day_tokens = re.findall(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun|M|Tu|W|Th|F|Sa|Su)', text)
    if day_tokens:
        return set(day_tokens)

    return set(text.split())


def _has_time_conflict(course_time, course_days, current_schedule):
    if not course_time or not current_schedule:
        return False

    course_day_set = _split_days(course_days)

    for scheduled in current_schedule:
        scheduled_time = scheduled.get("time", "")
        scheduled_days = scheduled.get("days", "")
        scheduled_day_set = _split_days(scheduled_days)

        if course_day_set and scheduled_day_set and not (course_day_set & scheduled_day_set):
            continue

        if _time_overlap(course_time, scheduled_time):
            return True

    return False


def _estimate_distance(building_a, building_b):
    if not building_a or not building_b:
        return 0
    if building_a == building_b:
        return 0
    return 1


def _has_long_walk(course_building, current_schedule):
    if not course_building or not current_schedule:
        return False

    for scheduled in current_schedule:
        scheduled_building = scheduled.get("building", "")
        dist = _estimate_distance(course_building, scheduled_building)
        if dist > 0:
            return True

    return False


def _has_final_conflict(course_final_day, current_schedule):
    if not course_final_day:
        return False

    for scheduled in current_schedule:
        if scheduled.get("final_day") == course_final_day:
            return True

    return False


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dedupe_reasons(reasons):
    seen = set()
    out = []
    for r in reasons:
        if r not in seen:
            out.append(r)
            seen.add(r)
    return out