# the process of upgrading or building something
from Utility import get_time_str


class Process(object):
    def __init__(self, total_time, func, name, building=None, cost=None):
        if total_time == 0:
            print("PROCESS ERROR: total time can not be 0")
        self.total_time = total_time
        self.time = self.total_time
        self.func = func
        self.name = name
        # if a building is being upgraded or build it gets also stored here. This allows buildings that are currently
        # being build to be excluded from future build commands
        self.building = building
        self.cost = cost  # to save at least the cost of the processes if it gets stopped

    def update(self):
        self.time -= 1
        if not self.time:
            self.func()
            return False
        return True

    def __str__(self):
        return "process: %s | total_time: %i | time left: %i" % (str(self.name), self.total_time, self.time)

    def pretty_str(self, unit_time):
        """a user friendly representation of the information stored here"""
        return "{}: {} left and {}% done".format(self.name, get_time_str(self.time * unit_time), round((self.total_time - self.time) / self.total_time * 100))
