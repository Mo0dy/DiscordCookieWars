import Building
from Building import buildings_table
from Process import Process
from copy import deepcopy
from FightSimulation import attack


class SaveObject(object):
    """used to extract the 'savable' information from the player"""
    def __init__(self, player):
        self.owner = player.owner
        self.workforce = player.workforce
        self.storage_capacity = player.storage_capacity

        self.buildings = deepcopy(player.buildings)

        # clear buildthreads to avoid error while saving
        for b in self.buildings:
            if issubclass(b.__class__, Building.Military):
                b.build_threads = []

        self.resources = player.resources
        self.units = deepcopy(player.units)
        # add rallied units as well
        for u, n in player.rallied_units.items():
            if u in self.units.keys():
                self.units[u] += n
            else:
                self.units[u] = n

    def restore(self, player):
        player.owner = self.owner
        player.workforce = self.workforce
        player.storage_capacity = self.storage_capacity

        player.buildings = self.buildings
        player.resources = self.resources
        player.units = self.units
        return player


class Player(object):
    def __init__(self, owner):
        self.owner = owner
        self.workforce = 1
        self.storage_capacity = 100
        self.buildings = [
            Building.Pipeline(),
            Building.Mine(),
            Building.Manor(),
            Building.Storage(),
        ]

        self.resources = {
            "gingerbread": 20,
            "cottoncandy": 20,
            "candy": 20,
            "chocolate": 20,
        }

        self.units = {}
        self.rallied_units = {}

        self.build_threads = []

        # all attack actions going on from this player
        self.attack_threads = []
        # all returning troop actions going on from this player
        self.return_threads = []

    # functions =============================
    async def update(self):
        self.build_threads = list(filter(lambda x: x.update(), self.build_threads))  # update build_threads and remove finished ones

        print("\nTHREADS: \n%s" % "\n".join([str(t) for t in self.build_threads]))  # print build threads
        for b in self.buildings:
            b.update(self)

        self.attack_threads = list(filter(lambda x: x.update(), self.attack_threads))
        print("\n attacks:")
        print("\n".join(str(t) for t in self.attack_threads))

        print("\n returns:")
        self.return_threads = list(filter(lambda x: x.update(), self.return_threads))
        print("\n".join(str(t) for t in self.return_threads))

    async def attack(self, target_p, target_name, send_message, time):
        units_list = "\n".join(["{:<10}({:<4}):  lvl {:<10}x{:<2}".format(u.name, u.emoji, u.level, amount) for u, amount in self.rallied_units.items()])
        self.attack_threads.append(Process(time, self.build_attack_function(target_p, time), "attack %s" % target_name))
        await send_message("you send out your troops:\n====================\n%s\n====================\nagainst %s" % (units_list, target_name))

    def build_attack_function(self, target_p, time):
        u = deepcopy(self.rallied_units)  # these are the units that will return again.
        self.rallied_units = {}  # the rallied units are used now

        def f():
            loot = attack(u, target_p)
            self.return_units(u, loot, time)
        return f

    def return_units(self, units, loot, time):
        if units:  # only return if there are units left
            def f():
                for u, amount in units.items():
                    self.add_troops(u, amount, self.units)
                for r, amount in loot.items():
                    self.resources[r] += amount
            self.return_threads.append(Process(time, f, "returning units"))

    async def upgrade(self, player_b, send_message):
        if not player_b:
            await send_message("you haven't build %s yet" % player_b.name)
            return
        new_level = player_b.level + 1
        # check if there is information for this level
        if not player_b.can_upgrade():
            await send_message("already max level")
            return

        if await self.can_build(player_b.next_cost(), player_b.next_requirements(), send_message):
            self.use_resources(player_b.next_cost())
            await self.new_build(player_b.next_time(), self.build_upgrade_function(player_b.upgrade), player_b.name + " lvl %i" % new_level, send_message, player_b.__class__)

    async def build(self, building, send_message):
        # check if it can be build at all
        if self.get_building(building):
            await send_message("you already have this building")
            return

        if await self.can_build(building.build_cost, building.build_requirements, send_message):
            def b_func():
                self.buildings.append(building())
            self.use_resources(building.build_cost)
            await self.new_build(building.build_time, b_func, building.name, send_message, building)

    def build_upgrade_function(self, upgrade_function):
        def f():
            upgrade_function(self)
        return f

    def use_resources(self, resources):
        for type, amount in resources.items():
            if self.resources[type] < amount:
                print("ERROR CAN'T BUILD. NOT ENOUGH RESOURCES")
                self.resources[type] = 0
            else:
                self.resources[type] -= amount

    async def new_build(self, time, func, name, send_message, building=None):
        if len(self.build_threads) >= self.workforce:  # can't add another thread
            await send_message("you cannot build more things simultaneously")
        else:
            self.build_threads.append(Process(time, func, "building %s" % name, building))
            await send_message("you started building %s" % name)

    def met_requirements(self, requirements):
        for building, lvl in requirements.items():
            b = self.get_building(buildings_table[building.lower()])
            if not b or b.level < lvl:  # no building
                return False
        return True

    async def can_build(self, cost, requirements, send_message):
        """returns true if the requirements are met and there are enough resources. else prints response"""
        if requirements:
            if not self.met_requirements(requirements):
                return False
        if cost:
            for resource, amount in cost.items():
                if self.resources[resource] < amount:
                    await send_message("you don't have enough resources")
                    return False
        return True

    def get_building(self, building):
        for b in self.buildings:
            if isinstance(b, building):
                return b

    async def rally_troops(self, player_u, amount, send_message):
        """cally some of your troops to send out for an attack"""
        if player_u in self.units and self.units[player_u] >= amount:
            # move units
            self.subtract_troops(player_u, amount, self.units)
            self.add_troops(player_u, amount, self.rallied_units)
            await send_message("you rallied %i %s%s" % (amount, player_u.name, "" if amount == 1 else "s"))
        else:
            await send_message("you don't have enough %ss" % player_u.name)

    def clear_rallied(self):
        for u, amount in self.rallied_units.items():
            self.add_troops(u, amount, self.units)
        self.rallied_units = {}

    def add_troops(self, player_u, amount, target):
        if not type(amount) == int:
            print("ERROR PLAYER add_troops: amount not integer")
        if player_u in target:
            target[player_u] += amount
        else:
            target[player_u] = amount
        if target[player_u] <= 0:  # you can't have 0 or negative troops
            del target[player_u]

    def subtract_troops(self, player_u, amount, target=None):
        self.add_troops(player_u, -amount, target)

    # properties ====================================================

    @property
    def gingerbread(self):
        return self.resources["gingerbread"]

    @gingerbread.setter
    def gingerbread(self, value):
        self.resources["gingerbread"] = value

    @property
    def cottoncandy(self):
        return self.resources["cottoncandy"]

    @cottoncandy.setter
    def cottoncandy(self, value):
        self.resources["cottoncandy"] = value

    @property
    def candy(self):
        return self.resources["candy"]

    @candy.setter
    def candy(self, value):
        self.resources["candy"] = value

    @property
    def chocolate(self):
        return self.resources["chocolate"]

    @chocolate.setter
    def chocolate(self, value):
        self.resources["chocolate"] = value

