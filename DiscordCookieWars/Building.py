from Process import Process
from Unit import units_table
import inspect


class Building(object):
    build_cost = None
    build_requirements = None
    build_time = None
    name = "Building"
    command_name = "building"
    emoji = "🏠"

    upgrade_prices = {}  # the price for every update
    upgrade_requirements = {}  # the requirements for an upgrade (in text form)
    upgrade_times = {}

    def __init__(self):
        self.level = 1

    def next_price(self):
        if self.level + 1 in self.upgrade_prices.keys():
            return self.upgrade_prices[self.level + 1]
        else:
            print("ERROR CAN'T UPDATE ANYMORE")

    def upgrade(self, player):
        self.level += 1

    # gets called every unit time
    def update(self, player):
        print("UPDATE: %s" % self.name)

    def can_upgrade(self):
        """return True if you can upgrade this building further"""
        return self.level + 1 in self.upgrade_prices.keys()

    def next_requirements(self):
        if self.level + 1 in self.upgrade_requirements:
            return self.upgrade_requirements[self.level + 1]
        else:
            return None

    def next_cost(self):
        return self.upgrade_prices[self.level + 1]

    def next_time(self):
        return self.upgrade_times[self.level + 1]


# resources Buildings ====================================================

class RGenerator(Building):
    """This type of building creates recources"""
    resource_type = "none"

    def __init__(self):
        super().__init__()
        self.resources_per_unit_time = 2  # the resources generated every time it gets updated

    def update(self, player):
        super(RGenerator, self).update(player)
        # increase resources but limit to storage capacity
        player.resources[self.resource_type] = min(player.resources[self.resource_type] + self.resources_per_unit_time, player.storage_capacity)

    def upgrade(self, player):
        super(RGenerator, self).upgrade(player)
        self.resources_per_unit_time = 2 * self.level  # formula for resources per level


class Pipeline(RGenerator):
    name = "Chocolate Pipeline"
    command_name = "pipeline"
    resource_type = "chocolate"
    emoji = "☕"
    upgrade_requirements = {
        2: {
            "Manor": 2,
        },
        4: {
            "Manor": 3,
        }
    }
    upgrade_prices = {
        2: {
            "chocolate": 20,
            "gingerbread": 20,
        },
        3: {
            "chocolate": 40,
            "gingerbread": 40,
        },
        4: {
            "chocolate": 80,
            "gingerbread": 80,
            "candy": 40,
        },
        5: {
            "chocolate": 160,
            "gingerbread": 160,
            "candy": 80,
        },
    }
    upgrade_times = {
        2: 8,
        3: 8,
        4: 8,
        5: 8,
    }


class Mine(RGenerator):
    name = "Gingerbread Mines"
    command_name = "mine"
    resource_type = "gingerbread"
    emoji = "⛏"
    upgrade_requirements = {
        2: {
            "Manor": 2,
        },
        4: {
            "Manor": 3,
        }
    }
    upgrade_prices = {
        2: {
            "chocolate": 20,
            "gingerbread": 20,
        },
        3: {
            "chocolate": 40,
            "gingerbread": 40,
        },
        4: {
            "chocolate": 80,
            "gingerbread": 80,
            "candy": 40,
        },
        5: {
            "chocolate": 160,
            "gingerbread": 160,
            "candy": 80,
        },
    }
    upgrade_times = {
        2: 8,
        3: 8,
        4: 8,
        5: 8,
    }


class Farm(RGenerator):
    name = "Cotton Candy Farm"
    command_name = "farm"
    resource_type = "cottoncandy"
    emoji = "☁"
    build_cost = {
        "gingerbread": 10,
        "chocolate": 10,
    }
    build_requirements = {
        "Mine": 1,
        "Pipeline": 1,
    }
    build_time = 8

    upgrade_requirements = {
        2: {
            "Manor": 2,
        },
        4: {
            "Manor": 3,
        }
    }
    upgrade_prices = {
        2: {
            "chocolate": 20,
            "gingerbread": 20,
        },
        3: {
            "chocolate": 40,
            "gingerbread": 40,
        },
        4: {
            "chocolate": 80,
            "gingerbread": 80,
            "cottoncandy": 40,
        },
        5: {
            "chocolate": 160,
            "gingerbread": 160,
            "cottoncandy": 80,
        },
    }
    upgrade_times = {
        2: 8,
        3: 8,
        4: 8,
        5: 8,
    }


class Factory(RGenerator):
    name = "Candy Factory"
    command_name = "factory"
    resource_type = "candy"
    emoji = "🍬"
    build_cost = {
        "gingerbread": 10,
        "chocolate": 10,
    }
    build_requirements = {
        "Mine": 1,
        "Pipeline": 1,
    }
    build_time = 8

    upgrade_requirements = {
        2: {
            "Manor": 2,
        },
        4: {
            "Manor": 3,
        }
    }
    upgrade_prices = {
        2: {
            "chocolate": 20,
            "gingerbread": 20,
        },
        3: {
            "chocolate": 40,
            "gingerbread": 40,
        },
        4: {
            "chocolate": 80,
            "gingerbread": 80,
            "cottoncandy": 40,
        },
        5: {
            "chocolate": 160,
            "gingerbread": 160,
            "cottoncandy": 80,
        },
    }
    upgrade_times = {
        2: 8,
        3: 8,
        4: 8,
        5: 8,
    }


# Military Buildings ====================================================

class Military(Building):
    def __init__(self):
        super().__init__()
        self.workforce = 1
        self.build_threads = []
        self.build_prep = {}  # the units you want to build can be prepared here

    def update(self, player):
        super(Military, self).update(player)
        # update build_threads and remove finished ones
        self.build_threads = list(filter(lambda x: x.update(), self.build_threads))

    def clear_build_prep(self):
        self.build_prep = {}

    async def build_units(self, player, send_message):
        """starts the currently prepared build thread"""
        cost = self.total_cost()
        # enough free threads and the player has the resources
        if len(self.build_threads) < self.workforce and await player.can_build(cost, None, send_message):
            player.use_resources(cost)
            self.build_threads.append(Process(self.total_time(), self.add_prep_to_player_func(player), self.name))
            return True
        return False

    def add_prep_to_player_func(self, player):
        """returns a function that will add a dictionary of units to the players units"""
        def f():
            for unit, amount in self.build_prep.items():
                if unit in player.units:
                    player.units[unit] += amount
                else:
                    player.units[unit] = amount
        return f

    def prep_units(self, unit, amount):
        """add the amount of units to the build prep dict"""
        if unit in self.build_prep:
            self.build_prep[unit] += amount
        else:
            self.build_prep[unit] = amount

    def total_time(self):
        time = 0
        for unit, amount in self.build_prep.items():
            time += unit.time * amount
        return time

    def total_cost(self):
        """returns the total cost of the currently prepared units"""
        cost = {}
        for unit, amount in self.build_prep.items():
            for resource, r_amount in unit.price.items():
                if resource in cost.keys():
                    cost[resource] += amount * r_amount
                else:
                    cost[resource] = amount * r_amount
        return cost


class CityWall(Building):
    name = "Candy Wall"
    command_name = "citywall"
    emoji = "🏯"
    build_requirements = {
        "Manor": 2,
    }
    build_cost = {
        "chocolate": 50,
        "gingerbread": 100,
        "candy": 10,
    }
    build_time = 8

    upgrade_requirements = {
        2: {
            "Manor": 3,
        }
    }
    upgrade_prices = {
        2: {
            "chocolate": 400,
            "gingerbread": 700,
            "candy": 600,
        },
    }
    upgrade_times = {
        2: 8,
    }


class Barracks(Military):
    name = "Barracks"
    command_name = "barracks"
    emoji = "⚔"
    build_requirements = {
        "Manor": 2,
    }
    build_cost = {
        "chocolate": 50,
        "gingerbread": 75,
        "candy": 25,
    }
    build_time = 8

    upgrade_requirements = {
        2: {
            "Manor": 3,
        }
    }
    upgrade_prices = {
        2: {
            "chocolate": 100,
            "gingerbread": 150,
            "candy": 50,
        }
    }
    upgrade_times = {
        2: 8,
    }


class Archery(Military):
    name = "Archery"
    command_name = "archery"
    emoji = "🏹"
    build_requirements = {
        "Manor": 2,
    }
    build_cost = {
        "chocolate": 100,
        "gingerbread": 150,
        "cottoncandy": 50,
    }
    build_time = 8


class Stables(Military):
    name = "Stables"
    command_name = "stables"
    emoji = "🦄"
    build_requirements = {
        "Manor": 4,
    }
    build_cost = {
        "chocolate": 400,
        "gingerbread": 700,
        "cottoncandy": 1000,
    }
    build_time = 8


class Workshop(Military):
    name = "Workshop"
    command_name = "workshop"
    emoji = "🔨"
    build_requirements = {
        "Manor": 4,
    }
    build_cost = {
        "chocolate": 500,
        "gingerbread": 800,
        "candy": 1200,
    }
    build_time = 8


# Other Buildings ========================================================

class Manor(Building):
    name = "Candy Manor"
    command_name = "manor"
    emoji = "🏰"

    workforce_per_level = {
        3: 2,
    }

    upgrade_prices = {
        2: {
            "gingerbread": 100,
            "chocolate": 100,
            "candy": 50,
            "cottoncandy": 50,
        },
        3: {
            "gingerbread": 300,
            "chocolate": 300,
            "candy": 150,
            "cottoncandy": 150,
        },
        4: {
            "gingerbread": 1000,
            "chocolate": 1000,
            "candy": 500,
            "cottoncandy": 500,
        },
    }
    upgrade_requirements = {
        2: {
            "Mine": 1,
            "Farm": 1,
        },
        3: {
            "Barracks": 1,
        },
        4: {
            "Barracks": 2,
        }
    }
    upgrade_times = {
        2: 8,
        3: 8,
        4: 8,
    }

    def upgrade(self, player):
        super(Manor, self).upgrade(player)
        if self.level in self.workforce_per_level.keys():
            player.workforce = self.workforce_per_level[self.level]


class Storage(Building):
    name = "Storage"
    command_name = "storage"
    emoji = "📦"

    storage_per_level = {
        2: 200,
        3: 400,
        4: 800,
        5: 1600,
    }

    upgrade_prices = {
        2: {
            "chocolate": 70,
            "gingerbread": 70,
            "candy": 20
        },
        3: {
            "chocolate": 150,
            "gingerbread": 150,
            "candy": 50,
        },
        4: {
            "chocolate": 300,
            "gingerbread": 300,
            "candy": 120,
            "cottoncandy": 80,
        },
        5: {
            "chocolate": 300,
            "gingerbread": 300,
            "candy": 240,
            "cottoncandy": 160,
        },
    }
    upgrade_requirements = {
        2: {
            "Manor": 2,
        },
        4: {
            "Manor": 3,
        },
    }
    upgrade_times = {
        2: 8,
        3: 8,
        4: 8,
        5: 8,
    }

    def upgrade(self, player):
        super(Storage, self).upgrade(player)
        player.storage_capacity = self.storage_per_level[self.level]


buildings_table = {}
# these buildings will be ignored
exclude_buildings = [
    Building,
    RGenerator,
    Military,
]

# connect the names of the buildings with the buildings in a dictionary
for b_str in dir():
    b = globals()[b_str]
    if inspect.isclass(b) and issubclass(b, Building):
        if b not in exclude_buildings:
            buildings_table[b.command_name] = b
