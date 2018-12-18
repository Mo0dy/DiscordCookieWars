import Building
from Building import buildings_table
from Process import Process


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

        self.units = {

        }

        self.build_threads = []

    # functions =============================
    async def update(self):
        self.build_threads = list(filter(lambda x: x.update(), self.build_threads))  # update build_threads and remove finished ones

        print("\nTHREADS: \n%s" % "\n".join([str(t) for t in self.build_threads])) # print build threads
        for b in self.buildings:
            b.update(self)

    async def upgrade(self, building, send_message):
        b = self.get_building(building)
        if not b:
            await send_message("you haven't build %s yet" % building.name)
            return
        new_level = b.level + 1
        # check if there is information for this level
        if not b.can_upgrade():
            await send_message("already max level")
            return

        if await self.can_build(b.next_cost(), b.next_requirements(), send_message):
            self.use_resources(b.next_cost())
            await self.new_build(b.next_time(), self.build_upgrade_function(b.upgrade), building.name + " lvl %i" % new_level, send_message, building)

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

