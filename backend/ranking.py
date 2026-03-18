def compute_match_score(course_id, user_profile, completed, ge_needed, keywords=None, course=None):
    """
    Compute a match score for a course given a user profile and optional keywords.
    :param course_id: string course identifier
    :param user_profile: dict of user info (preferredTime, courseFormat, maxUnits, geNeeded)
    :param completed: set of completed course codes
    :param ge_needed: set of GE categories user still needs
    :param keywords: list of keywords to boost score
    :param course: optional dict containing course info (ge list, time, units, format)
    :return: (score:int, reasons:list[str])
    """
    score = 0
    reasons = []

    keywords = keywords or []

    # keywords
    if "easy" in keywords:
        score += 20
        reasons.append("Easy course")
    if "online" in keywords:
        score += 15
        reasons.append("Online format")
    if "morning" in keywords:
        if course and course.get("time", "").lower().find("am") != -1:
            score += 10
            reasons.append("Morning class")
    if "afternoon" in keywords:
        if course and course.get("time", "").lower().find("pm") != -1:
            score += 10
            reasons.append("Afternoon class")
    if "evening" in keywords:
        if course and course.get("time", "").lower().find("pm") != -1:
            score += 10
            reasons.append("Evening class")

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
        if preferred_time.lower() == "morning" and course_time.lower().find("am") != -1:
            score += 15
            reasons.append("Matches morning preference")
        elif preferred_time.lower() == "afternoon" and "pm" in course_time.lower():
            score += 15
            reasons.append("Matches afternoon preference")
        elif preferred_time.lower() == "evening" and "pm" in course_time.lower():
            score += 15
            reasons.append("Matches evening preference")

    # workload/units
    max_units = user_profile.get("max_units", 4)
    if course and course.get("units", 4) <= max_units:
        score += 10
        reasons.append(f"Units <= {max_units}")

    # course format
    course_format = course.get("format", "in-person") if course else "in-person"
    preferred_format = user_profile.get("course_format", "any")
    if preferred_format == "any" or preferred_format == course_format:
        score += 10
        reasons.append(f"Preferred format: {course_format}")

    # penalty for completed courses
    if course_id in completed:
        score -= 100  # already taken
        reasons.append("Course already completed")

    return score, reasons