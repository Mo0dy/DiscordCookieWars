import inspect


class Unit(object):
    name = "Unit"
    command_name = "unit"
    unit_type = ""  # the building the unit can be build in
    emoji = ""  # the emoji for reactions
    # an attack against a target the unit is strong again will be multiplied with this value
    strength_damage_multiplier = 1.1
    strengths = []  # a list of the names of units this one is strong against
    price_list = {}  # the price per level
    damage_list = {}  # the damage per level
    health_list = {}  # the health per level
    speed_list = {}  # the speed per level
    time_list = {}  # the time it takes to build the unit per level
    requirements_list = {}  # the requirements list. a unit needs requirements for EVERY level
    carrying_capacity_list = {}

    def __init__(self, level=1):
        if level in self.price_list.keys():  # check that this unit has the level
            self.level = level
        else:
            self.level = max(self.price_list.keys())

    @property
    def damage(self):
        if self.level in self.damage_list:
            return self.damage_list[self.level]
        else:
            # find the highest level below the current level
            return self.last_level_items(self.damage_list)

    @property
    def carrying_capacity(self):
        if self.level in self.damage_list:
            return self.carrying_capacity_list[self.level]
        else:
            # find the highest level below the current level
            return self.last_level_items(self.carrying_capacity_list)

    @property
    def price(self):
        if self.level in self.price_list:
            return self.price_list[self.level]
        else:
            # find the highest level below the current level
            return self.last_level_items(self.price_list)

    @property
    def speed(self):
        if self.level in self.speed_list:
            return self.speed_list[self.level]
        else:
            # find the highest level below the current level
            return self.last_level_items(self.speed_list)

    @property
    def time(self):
        if self.level in self.time_list:
            return self.time_list[self.level]
        else:
            # find the highest level below the current level
            return self.last_level_items(self.time_list)

    @property
    def health(self):
        if self.level in self.health_list:
            return self.health_list[self.level]
        else:
            # find the highest level below the current level
            return self.last_level_items(self.health_list)

    @property
    def requirements(self):
        if self.level in self.requirements_list:
            return self.requirements_list[self.level]
        else:
            # find the highest level below the current level
            return self.last_level_items(self.requirements_list)

    def last_level_items(self, my_dict):
        """returns the value of the item with the highest level below level"""
        return my_dict[max([key for key in my_dict if key < self.level])]

    def __eq__(self, other):
        """override equal so that same level units be found"""
        return isinstance(other, self.__class__) and other.level == self.level

    def __hash__(self):
        """override hash so that equal units can be stacked in the dictionary"""
        return (
            self.name,
            self.level
        ).__hash__()


class Soldier(Unit):
    name = "Soldier"
    command_name = "soldier"
    unit_type = "barracks"
    emoji = "⚔"
    price_list = {
        1: {
            "candy": 10,
            "cottoncandy": 10
        },
        2: {
            "candy": 15,
            "cottoncandy": 10,
        }
    }
    damage_list = {
        1: 10,
    }
    health_list = {
        1: 12,
    }
    speed_list = {
        1: 6,
    }
    carrying_capacity_list = {
        1: 10,
        2: 50,
    }
    requirements_list = {
        1: {
            "barracks": 1,
        },
        2: {
            "barracks": 2,
        }
    }
    time_list = {
        1: 2,
        2: 2,
    }


class Archer(Unit):
    name = "Archer"
    command_name = "archer"
    strengths = ["soldier"]
    unit_type = "archery"
    emoji = "🏹"
    price_list = {
        1: {
            "candy": 10,
            "cottoncandy": 20,
            "gingerbread": 10,
        },
    }
    damage_list = {
        1: 10,
    }
    health_list = {
        1: 7,
    }
    speed_list = {
        1: 5,
    }
    carrying_capacity_list = {
        1: 5,
        2: 25,
    }
    requirements_list = {
        1: {
            "archery": 1
        }
    }
    time_list = {
        1: 2,
    }


class Cavalry(Unit):
    name = "Cavalry"
    command_name = "cavalry"
    strengths = ["archer", "soldier"]
    unit_type = "stables"
    emoji = "🦄"
    price_list = {
        1: {
            "candy": 20,
            "cottoncandy": 50,
            "gingerbread": 10,
        },
    }
    damage_list = {
        1: 20,
    }
    health_list = {
        1: 20,
    }
    speed_list = {
        1: 25,
    }
    carrying_capacity_list = {
        1: 75,
    }
    requirements_list = {
        1: {
            "stables": 1
        }
    }
    time_list = {
        1: 3,
    }


class Trebuchet(Unit):
    name = "Trebuchet"
    command_name = "trebuchet"
    strengths = ["citywall"]
    unit_type = "workshop"
    emoji = "⚙"
    strength_damage_multiplier = 4  # only effective against buildings
    price_list = {
        1: {
            "candy": 500,
            "cottoncandy": 50,
            "gingerbread": 300,
            "chocolate": 300,
        },
    }
    damage_list = {
        1: 10,
    }
    health_list = {
        1: 50,
    }
    speed_list = {
        1: 1,
    }
    carrying_capacity_list = {
        1: 200,
    }
    requirements_list = {
        1: {
            "workshop": 1
        }
    }
    time_list = {
        1: 40,
    }


def get_units_str(unit_dict):
    """returns a nice formated string that displays what units you have what amount of in this dictionary"""
    return "\n".join(["{:<10}({:<4}):  lvl {:<10}x{:<2}".format(u.name, u.emoji, u.level, amount) for u, amount in unit_dict.items()])


# a table where the command name is key and the unit value
units_table = {}
# a table where the building name is key and the value is a list of all units this building can produce
units_per_building = {}

exclude_units = [
    Unit,
]

for u_str in dir():
    u = globals()[u_str]
    if inspect.isclass(u) and issubclass(u, Unit):
        if u not in exclude_units:
            units_table[u.command_name] = u
            if u.unit_type in units_per_building.keys():
                units_per_building[u.unit_type].append(u)
            else:
                units_per_building[u.unit_type] = [u]
