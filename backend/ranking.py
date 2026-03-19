import re


def compute_match_score(course_id, user_profile, completed, ge_needed, keywords=None, course=None, major_course_ids=None, prereq_map=None):
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
        score -= 100  # already taken
        reasons.append("Course already completed")
        return max(score, 0), reasons

    # major requirement
    if course_id in major_course_ids:
        score += 30
        reasons.append("Required for your major")

    # prerequisite bonus: if user completed a prereq for this course, +10
    prereqs = prereq_map.get(course_id, set())
    if prereqs and completed:
        met = prereqs & completed
        if met:
            score += 10
            reasons.append("Prerequisite completed")

    # ge needs
    if course and ge_needed:
        matching_ge = [g for g in course.get("ge", []) if g in ge_needed]
        if matching_ge:
            score += 20
            reasons.append(f"Satisfies GE need: {', '.join(matching_ge)}")

    # preferred time
    preferred_time = user_profile.get("preferred_time", "any")
    course_time = course.get("time", "") if course else ""
    if preferred_time != "any":
        if _check_time_preference(preferred_time.lower(), course_time):
            score += 15
            reasons.append(f"Matches {preferred_time} preference")

    # workload/units
    max_units = user_profile.get("max_units", 4)
    if isinstance(max_units, str):
        max_units = int(max_units) if max_units.isdigit() else 4
    if course and course.get("units", 4) <= max_units:
        score += 10
        reasons.append(f"Units <= {max_units}")

    # course format
    course_format = course.get("format", "in-person") if course else "in-person"
    preferred_format = user_profile.get("course_format", "any")
    if preferred_format == "any" or preferred_format == course_format:
        score += 10
        reasons.append(f"Preferred format: {course_format}")

    # workload preference
    workload = (user_profile.get("workload") or "balanced").lower()
    course_units = course.get("units", 4) if course else 4
    if workload == "light" and course_units <= 3:
        score += 10
        reasons.append("Light workload course")
    elif workload == "heavy" and course_units >= 4:
        score += 5

    return max(score, 0), reasons


def _check_time_preference(preference, time_str):
    """
    Check if a course time matches a time-of-day preference.
    DB stores times in 24h format like '10:00', '14:30' (no am/pm),
    so we extract the hour with regex.
    """
    if not time_str or time_str == "TBA":
        return False

    match = re.search(r'(\d{1,2}):(\d{2})', time_str)
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
