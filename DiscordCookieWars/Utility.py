unit_time = 1


def get_time_str(t):
    """returns a time in real world units rounded appropriately"""
    t_units = [
        ("day", 60 * 60 * 24),
        ("hour", 60 * 60),
        ("minute", 60),
        ("second", 1),
    ]
    for t_str, t_amount in t_units:
        if t < t_amount:
            continue
        time_str = "%.1f" % (t / t_amount)
        return "{} {}{}".format(time_str if int(time_str[-1]) else time_str[:-2], t_str, "" if time_str == "1.0" else "s")
    return "0s"


def get_resource_str(resources, detail=False):
    emojilist = {
        "gingerbread": "🍫",
        "cottoncandy": "☁",
        "candy": "🍭",
        "chocolate": "🍩",
    }
    trans = {
        "gingerbread": "Gingerbread",
        "cottoncandy": "Cotton Candy",
        "candy": "Candy",
        "chocolate": "Chocolate",
    }
    if detail:
        return "\n".join(["{} ({}): {}".format(emojilist[r], trans[r], amount) for r, amount in resources.items()])
    return ", ".join(["{}: {}".format(emojilist[r], amount) for r, amount in resources.items()])
