# the process of upgrading or building something
class Process(object):
    def __init__(self, total_time, func, name, building=None):
        self.total_time = total_time
        self.time = self.total_time
        self.func = func
        self.name = name
        # if a building is being upgraded or build it gets also stored here. This allows buildings that are currently
        # being build to be excluded from future build commands
        self.building = building

    def update(self):
        self.time -= 1
        if not self.time:
            self.func()
            return False
        return True

    def __str__(self):
        return "process: %s | total_time: %i | time left: %i" % (str(self.name), self.total_time, self.time)
