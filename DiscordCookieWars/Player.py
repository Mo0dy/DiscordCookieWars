import Building
from Building import buildings_table
from Process import Process
from copy import deepcopy
from FightSimulation import attack
import Unit
from Utility import get_time_str, get_resource_str


class SaveObject(object):
    """used to extract the 'savable' information from the player"""
    def __init__(self, player):
        self.owner = player.owner
        self.workforce = player.workforce
        self.storage_capacity = player.storage_capacity
        self.owner_name = player.owner_name
        self.buildings = deepcopy(player.buildings)
        self.messages = player.messages

        self.resources = deepcopy(player.resources)
        # clear buildthreads to avoid error while saving
        for b in self.buildings:
            if issubclass(b.__class__, Building.Military):
                for t in b.build_threads:
                    if t.cost:
                        for r, amount in t.cost.items():
                            self.resources[r] = min(self.resources[r] + amount, player.storage_capacity)
                b.build_threads = []

        # add the cost from the processes of the player to player resources
        for p in player.build_threads:
            if p.cost:
                for r, amount in p.cost.items():
                    self.resources[r] = min(self.resources[r] + amount, player.storage_capacity)

        self.protection = player.protection
        self.units = deepcopy(player.units)
        # add rallied units as well
        for u, n in player.rallied_units.items():
            if u in self.units.keys():
                self.units[u] += n
            else:
                self.units[u] = n

        # store units
        # store units that are out on attack
        for p in player.attack_threads:
            if p.units:
                for u, amount in p.units.items():
                    if u in self.units:
                        self.units[u] += amount
                    else:
                        self.units[u] = amount

    def restore(self, player):
        player.owner_name = self.owner_name
        player.messages = self.messages
        player.owner = self.owner
        player.workforce = self.workforce
        player.storage_capacity = self.storage_capacity

        player.buildings = self.buildings
        player.resources = self.resources
        player.units = self.units
        player.protection = self.protection
        return player


class Player(object):
    unit_time_f = None  # a function to get unit time from the bot

    def __init__(self, owner, owner_name):
        self.owner = owner
        self.owner_name = owner_name
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
        # a list of messages that will be send to you every fast update
        self.messages = []
        self.protection = True

    # functions =============================
    async def update(self):
        """the update function gets called every game loop"""
        self.build_threads = list(filter(lambda x: x.update(), self.build_threads))  # update build_threads and remove finished ones

        print("\nTHREADS: \n%s" % "\n".join([str(t) for t in self.build_threads]))  # print build threads
        for b in self.buildings:
            b.update(self)

        self.attack_threads = list(filter(lambda x: x.update(), self.attack_threads))

        # log current attacks / returns
        if self.attack_threads:
            print("\n attacks:")
            print("\n".join(str(t) for t in self.attack_threads))
        if self.return_threads:
            print("\n returns:")
            self.return_threads = list(filter(lambda x: x.update(), self.return_threads))
            print("\n".join(str(t) for t in self.return_threads))

    async def attack(self, target_p, send_message, time):
        """initates the attack from one player onto another

        :param target_p: the player that gets attacked
        :param target_name: the name of the player that gets attacked
        :param send_message: a function that can send a message to discord
        :param time: the time the attack will take
        :param attacker_msg_func: a function to privately message the attacker
        :param target_msg_func: a function to privately message the target
        :return:
        """

        target_p.messages.append("**%s** made an aggressive move against you with these units:\n=============\n%s\n=============\nthey will need %s to arrive" % (self.owner_name, Unit.get_units_str(self.rallied_units), get_time_str(time * Player.unit_time_f())))

        await send_message("you send out your troops:\n====================\n%s\n====================\nagainst %s\nIt will take %s" % (Unit.get_units_str(self.rallied_units), target_p.owner_name, get_time_str(time * Player.unit_time_f())))
        attack_units = self.rallied_units.copy()  # self.rallied units will be reset while building the attack function and needs to be stored here

        # add an attack to the attack threads. Also give information about the attacking units for recovery and information printing
        self.attack_threads.append(Process(time, self.build_attack_function(target_p, time), "attack %s" % target_p.owner_name, units=attack_units))

    def build_attack_function(self, target_p, time):
        """builds the function that will be executed when the attack happens"""
        u = deepcopy(self.rallied_units)  # these are the units that will return again.
        self.rallied_units = {}  # the rallied units are used now

        # the function that will be called when the attack happens
        def f():
            loot = attack(u, target_p)
            self.return_units(u, loot, time)  # start a return of the units
            loot_str = "====================\n%s\n====================s" % get_resource_str(loot)
            self.messages.append("you successfully attacked **%s** and looted:\n%s\nYour units will be back in %s" % (target_p.owner_name, loot_str, get_time_str(time * Player.unit_time_f())))
            target_p.messages.append("you got raided by **%s** and he/she looted:\n%s" % (self.owner_name, loot_str))
        return f

    def return_units(self, units, loot, time):
        """starts a return thread to return units back to home"""
        if units:  # only return if there are units left
            def f():
                for u, amount in units.items():
                    self.add_troops(u, amount, self.units)
                for r, amount in loot.items():
                    self.resources[r] += amount
                self.messages.append("your units returned.")
            self.return_threads.append(Process(time, f, "returning units"))

    async def upgrade(self, player_b, send_message):
        """upgrade a player building"""
        # plausibility checks
        if not player_b:
            await send_message("you haven't build %s yet" % player_b.name)
            return
        new_level = player_b.level + 1
        # check if there is information for this level
        if not player_b.can_upgrade():
            await send_message("already max level")
            return
        if len(self.build_threads) >= self.workforce:
            await send_message("you don't have enough workforce to build this many things in parallel")
            return

        if await self.can_build(player_b.next_cost(), player_b.next_requirements(), send_message):
            self.use_resources(player_b.next_cost())
            await self.new_build(player_b.next_time(), self.build_upgrade_function(player_b.upgrade, player_b), player_b.name + " lvl %i" % new_level, send_message, building=player_b.__class__, cost=player_b.next_cost())

    async def build(self, building, send_message):
        # check if it can be build at all
        if self.get_building(building):
            await send_message("you already have this building")
            return

        if await self.can_build(building.build_cost, building.build_requirements, send_message):
            if len(self.build_threads) >= self.workforce:
                await send_message("you don't have enough workforce to build this many things in parallel")
                return

            # the function that will be called when the building is going to be build
            def b_func():
                self.buildings.append(building())  # build the building
                self.messages.append("you finished building the %s %s" % (building.emoji, building.name))

            self.use_resources(building.build_cost)
            await self.new_build(building.build_time, b_func, building.name, send_message, building=building, cost=building.build_cost)

    def build_upgrade_function(self, upgrade_function, player_b):
        def f():
            upgrade_function(self)
            self.messages.append("you finished upgrading the %s %s" % (player_b.emoji, player_b.name))
        return f

    def use_resources(self, resources):
        for type, amount in resources.items():
            if self.resources[type] < amount:
                print("ERROR CAN'T BUILD. NOT ENOUGH RESOURCES")
                self.resources[type] = 0
            else:
                self.resources[type] -= amount

    async def new_build(self, time, func, name, send_message, building=None, cost=None):
        p = Process(time, func, "building %s" % name, building=building, cost=cost)
        self.build_threads.append(p)
        await send_message("you started:\n%s" % p.pretty_str(Player.unit_time_f()))

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

    @staticmethod
    def add_troops(player_u, amount, target):
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

    @property
    def city_wall_health(self):
        """returns the defensive multiplier the city wall gives (bonus on hp)"""
        city_wall = self.get_building(Building.CityWall)
        if not city_wall:
            return 0
        return city_wall.hp
