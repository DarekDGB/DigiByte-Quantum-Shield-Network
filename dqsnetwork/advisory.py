def to_level(score):
    v = score.value

    if v < 0.25:
        return "NORMAL"
    if v < 0.5:
        return "ELEVATED"
    if v < 0.75:
        return "CRITICAL_LOCAL"
    return "CRITICAL_GLOBAL"
