unit_time = 1
from discord.utils import get


emojilist = {
    "gingerbread": "🍫",
    "cottoncandy": "☁",
    "candy": "🍭",
    "chocolate": "🍩",
}


def load_custom_emojis(client):
    """loads the custom emojis from the client

    :param client:
    :return:
    """
    custom_emojis = {
        "528210030382678037": "gingerbread",
        "528210031183790111": "candy",
        "528210030516764682": "cottoncandy",
        "528210030562902036": "chocolate",
    }
    for e in client.get_all_emojis():
        if e.id in custom_emojis.keys():
            emojilist[custom_emojis[e.id]] = e


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
    trans = {
        "gingerbread": "Gingerbread",
        "cottoncandy": "Cotton Candy",
        "candy": "Candy",
        "chocolate": "Chocolate",
    }
    if detail:
        return "\n".join(["{} ({}): {}".format(emojilist[r], trans[r], amount) for r, amount in resources.items()])
    return ", ".join(["{}: {}".format(emojilist[r], amount) for r, amount in resources.items()])
