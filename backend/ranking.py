def compute_match_score(profile, course):
    score = 0

    # ge needs
    if any(ge in course['ge'] for ge in profile['geNeeded']):
        score += 20
    
    # preferred time
    if profile['preferredTime'] == 'any' or profile['preferredTime'] in course.get('time', ''):
        score += 15
    
    # workload preference
    if course.get('units', 4) <= profile.get('maxUnits', 4):
        score += 10
    
    # format preference
    if profile['courseFormat'] == 'any' or profile['courseFormat'] == course.get('format', 'in-person'):
        score += 10
    
    return score
