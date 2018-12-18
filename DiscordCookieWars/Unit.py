import inspect


class Unit(object):
    name = "Unit"
    command_name = "unit"
    unit_type = ""  # the building the unit can be build in
    emoji = ""  # the emoji for reactions
    strengths = []  # a list of the names of units this one is strong against
    price_list = {}  # the price per level
    damage_list = {}  # the damage per level
    speed_list = {}  # the speed per level
    time_list = {}  # the time it takes to build the unit per level
    requirements_list = {}  # the requirements list. a unit needs requirements for EVERY level

    def __init__(self, level):
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
    }
    damage_list = {
        1: 5,
    }
    speed_list = {
        1: 5,
    }
    requirements_list = {
        1: {
            "barracks": 1
        },
    }
    time_list = {
        1: 1,
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
    speed_list = {
        1: 5,
    }
    requirements_list = {
        1: {
            "archery": 1
        }
    }
    time_list = {
        1: 1,
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
    speed_list = {
        1: 25,
    }
    requirements_list = {
        1: {
            "stables": 1
        }
    }
    time_list = {
        1: 1,
    }


class Trebuchet(Unit):
    name = "Trebuchet"
    command_name = "trebuchet"
    strengths = ["citywall"]
    unit_type = "workshop"
    emoji = "⚙"
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
    speed_list = {
        1: 1,
    }
    requirements_list = {
        1: {
            "workshop": 1
        }
    }
    time_list = {
        1: 1,
    }


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
