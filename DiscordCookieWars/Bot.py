import RecourceManager
import Player
import os
import Building
from Building import buildings_table
from Unit import units_per_building, units_table
import Menu


# the paths the playersaves will be saved at. The save method will append the name of the server the bot is running on.
savepath = os.path.join("Saves", "players")


class Bot(object):
    """The main bot that handles all the messages and holds all the information"""
    def __init__(self, client, server, unit_time_f):
        self.unit_time_f = unit_time_f  # a function to get unit_time
        self.command_prefix = "?"
        self.client = client  # the client that can be used to interact with discord

        # the player classes. the key is the id of the user owning the player
        self.players = {}
        # this is used for saving and loading information. it is the id of the server this bot is running for
        self.server = server
        self.load_players()

    async def update(self):
        """gets called about twice a minute and is used for timed events"""

        # call the update method of all players
        print("\nUPDATE BOT %s ========================" % self.server)
        for p in self.players.values():
            print("Player: %s ===========" % p.owner)
            await p.update()
        self.save_players()

    async def send_message(self, channel, content):
        """send a message to a channel on a server"""
        await self.client.send_message(channel, content)

    # commands =============================================================
    async def join(self, author, channel):
        """a new user joins the game"""
        if author.id not in self.players.keys():
            self.players[author.id] = Player.Player(author.id)  # add a new player to the list of players
            await self.send_message(channel, "%s you joined the cookie wars! type %shelp to get started" % (self.get_mention(author), self.command_prefix))
        else:
            await self.send_message(channel, "you already joined the cookie wars. type %shelp to get started" % self.command_prefix)

    async def start_menu(self, author, channel):
        """starts a menu process"""
        menu = Menu.Menu(self.client, channel, author)  # create the menu object
        self.main_menu(menu)  # fill the menu object with the content for the main menu
        await menu.start()  # start the menu

    async def print_help(self, channel):
        help_str = """
        Your goal is to upgrade your hometown and raid your foes for resources (and pleasure).
        
        You can upgrade your building to produce more resources, better units and unlock new buildpaths.
        
        There are four basic resources:
        > gingerbread
        > chocolate
        > cotton candy
        > candy
        
        These will be used to build everything and are produced by the:
        > gingerbread mine
        > chocolate pipeline
        > cotton candy farm
        > candy factory
        
        They are stored in the Storage.
        
        Most new buildings including your first Barracks will be unlocked by upgrading the Candy Manor. 
        """
        await self.send_message(channel, help_str)

    async def print_town(self, author, channel):
        """prints information about the town"""
        await self.send_message(channel, 'buildings: \n%s\n' % '\n'.join(["{:<5}{:<20}{}".format(b.emoji, b.name, b.level) for b in self.get_player(author).buildings]))

    async def print_resources(self, author, channel):
        """prints the amount of resources the player has"""
        await self.send_message(channel, 'resources: ```%s\n```' % '\n'.join(["{:<14}{}".format(r, a) for r, a in self.get_player(author).resources.items()]))

    async def print_buildable(self, author, channel):
        """prints all the buildings the player has fulfilled requirements for"""
        lines = [b.name for b in self.get_buildable(author)]
        await self.send_message(channel, "\nyou can build:\n" + "\n".join(lines))

    async def print_upgrades(self, author, channel):
        """prints all the upgrade options for the buildings the player has"""
        lines = []

        player = self.get_player(author)
        for b in buildings_table.values():
            player_b = player.get_building(b)
            if player_b:
                upgrade_level = player_b.level + 1
                if player_b.can_upgrade():  # there is a price so there is another level
                    if upgrade_level in b.upgrade_requirements.keys():
                        if player.met_requirements(b.upgrade_requirements[upgrade_level]):
                            lines.append("{:<20} | {}".format(b.name, "met"))
                        else:
                            lines.append("{:<20} | {}".format(b.name, " | ".join(["{}: level: {}".format(b, lvl) for b, lvl in b.upgrade_requirements[upgrade_level].items()])))
                    else:  # no special requirements
                        lines.append("{:<20} | {}".format(b.name, "met"))

        await self.send_message(channel, ".\n{:<20}   {}\n".format("building", "requirements") + "\n".join(lines))

    async def print_threads(self, author, channel):
        """prints the current build threads"""
        player = self.get_player(author)
        await self.send_message(channel, "currently building:\n %s" % "\n".join([self.get_process_str(t) for t in player.build_threads]))

    async def print_units(self, author, channel):
        """prints all units a player has"""
        player = self.get_player(author)
        if not player.units:
            await self.send_message(channel, "you have no units")
            return
        units_list = "\n".join(["{:<10}({:<4}):  lvl {:<10}x{:<2}".format(u.name, u.emoji, u.level, amount) for u, amount in player.units.items()])
        await self.send_message(channel, "your units:\n================\n%s\n================" % units_list)

    async def print_requirements(self, channel, player_b):
        """print the requirements to build a specific building"""
        if player_b:  # we need to get the upgrade
            if player_b.can_upgrade():
                requirements = player_b.next_requirements()
            else:
                await self.send_message(channel, "building is already max level")
        else:  # we need to get the build requirements
            requirements = player_b.build_requirements

        await self.send_message(channel, " \nthe requirements are:\n" "\n".join("{:<15} lvl {}".format(b, lvl) for b, lvl in requirements.items()))

    async def print_building_threads(self, channel, player_b):
        """prints the threads of a specific building"""
        await self.send_message(channel, "currently building:\n %s" % "\n".join([self.get_process_str(t) for t in player_b.build_threads]))

    async def print_building_prepared(self, channel, player_b):
        """prints the prepared units in a building"""
        # empty dictionary
        if not player_b.build_prep:
            await self.send_message(channel, "noting prepped")
            return

        units_list = "\n".join(["{:<10}({:<4}):  lvl {:<10}x{:<2}".format(u.name, u.emoji, u.level, amount) for u, amount in player_b.build_prep.items()])
        cost_list = "\n".join(["{:<10} x{:<4}".format(resource, amount) for resource, amount in player_b.total_cost().items()])

        await self.send_message(channel, "%s prepped units:\n=====================\n%s\n=========\ncost:\n%s\n=====================" % (player_b.name, units_list, cost_list))

    async def start_building_prepped(self, author, channel, player_b):
        """starts the prepped build of a military building if the user has the resources"""
        started_build = await player_b.build_units(self.get_player(author), self.get_message_func(channel))
        if not started_build:
            await self.send_message(channel, "you don't have enough resources")
        else:
            await self.send_message(channel, "you started the prepepd build")

    async def build(self, author, channel, building):
        """build a new building"""
        await self.get_player(author).build(building, self.get_message_func(channel))

    async def upgrade(self, author, channel, player_b):
        """upgrade an existing building"""
        await self.get_player(author).upgrade(player_b, self.get_message_func(channel))

    async def prep_units(self, author, channel, building, unit, amount=None):
        """prepare to build some units in a military institution"""

        print("BOT PREPPING UNITS recieved", unit)

        # ask for the amount if there is none given
        if not amount:
            amount = await self.ask_amount(author, channel)
            if not amount:
                return

        # add the unit to the building prep
        building.prep_units(unit, amount)
        await self.send_message(channel, "your units have been added to the prep queue")

    async def rally_troops(self, author, channel, unit, amount=None):
        """collect some of your troops to fight"""
        pass

    # utility functions ===========================================================
    def get_resource_str(self, resources, detail=False):
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

    def get_process_str(self, process):
        return "{}: {} left and {}% done".format(process.name, self.get_time_str(process.time), round(process.time / process.total_time * 100))

    def get_time_str(self, time_units):
        """returns a time in real world units rounded appropriately"""
        t = time_units * self.unit_time
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

    async def ask_amount(self, author, channel):
        """asks the author for a positive integer value"""
        await self.client.send_message(channel, "how many units do you want to create")
        answer = await self.client.wait_for_message(timeout=60, author=author, channel=channel, check=lambda x: x.content.isdigit())
        amount = int(answer.content)
        if amount <= 0:
            await self.send_message(channel, "the amount can not be 0")
            return
        return amount

    def get_upgradable(self, user):
        """returns all buildings the user can upgrade"""
        player = self.get_player(user)
        upgradable = []
        for b in buildings_table.values():
            player_b = player.get_building(b)
            if player_b and not b in [t.building for t in player.build_threads]:
                upgrade_level = player_b.level + 1
                if player_b.can_upgrade():  # there is a price so there is another level
                    if upgrade_level in b.upgrade_requirements.keys():
                        if player.met_requirements(b.upgrade_requirements[upgrade_level]):
                            upgradable.append(player_b)
                    else:
                        upgradable.append(player_b)
        return upgradable

    def get_buildable(self, user):
        """returns all buildings the user can build"""
        buildable = []
        player = self.get_player(user)
        for b in buildings_table.values():
            player_b = player.get_building(b)
            if not player_b and not b in [t.building for t in player.build_threads]:
                # the player doesn't yet have the building
                if player.met_requirements(b.build_requirements):
                    buildable.append(b)
        return buildable

    def get_buildable_units(self, user, building):
        """returns all units the user can build in a specific building"""
        buildable = []
        player = self.get_player(user)
        for u in units_per_building[building.command_name]:  # every unit that can be build in this building
            # get the highest level possible units to build
            # sort requirements per level
            requirements_list = [(key, value) for key, value in u.requirements_list.items()]
            requirements_list.sort(key=lambda x: x[0], reverse=True)  # sort the list from high to low level

            # check for the highest level that can be build by the player
            unit_level = 0
            for level, requirements in requirements_list:
                if player.met_requirements(requirements):
                    unit_level = level
                    break
            if unit_level:
                buildable.append(u(unit_level))
        return buildable

    def get_player(self, user):
        """returns a Player from a user id"""
        return self.players[user.id]

    # the save and load functions are buggy and ignore current build threads
    def load_players(self):
        """load the player information from file"""
        # self.players = RecourceManager.load_object(savepath + "_%s" % self.server)
        # if not self.players:
        #     self.players = {}
        save_objs = RecourceManager.load_object(savepath + "_%s" % self.server)
        if not save_objs:
            self.players = {}
            return
        self.players = {key: value.restore(Player.Player("")) for key, value in save_objs.items()}

    def save_players(self):
        """save the player information to file"""
        save_objs = {key: Player.SaveObject(value) for key, value in self.players.items()}
        RecourceManager.save_object(save_objs, savepath + "_%s" % self.server)
        # RecourceManager.save_object(self.players, savepath + "_%s" % self.server)

    @staticmethod
    def get_mention(user):
        """returns either a mention or the user in BOLD depending on the bot settings"""
        return '**%s**' % user.name

    def get_message_func(self, channel):
        """builds and returns a message function that can send a message to this channel"""
        async def f(content):
            await self.send_message(channel, content)
        return f

    def main_menu(self, menu):
        main_menu = {
            "🍭": Menu.Menupoint("Candy Manor", self.candy_manor_menu, submenu=True),
            "⚔": Menu.Menupoint("Military District", self.military_menu, submenu=True),
            "❓": Menu.Menupoint("Help", menu.build_f(self.print_help, [menu.channel]))
        }
        menu.header = self.get_resource_str(self.get_player(menu.author).resources, detail=True)
        menu.change_menu(main_menu)

    def candy_manor_menu(self, menu):
        m = {
            "🛠": Menu.Menupoint("build", self.build_menu, submenu=True),
            "⬆": Menu.Menupoint("upgrade", self.upgrade_menu, submenu=True),
            "🍪": Menu.Menupoint("resources", menu.build_f(self.print_resources, (menu.author, menu.channel))),
            "👷": Menu.Menupoint("currently building", menu.build_f(self.print_threads, (menu.author, menu.channel))),
            "🗺": Menu.Menupoint("town overview", menu.build_f(self.print_town, (menu.author, menu.channel))),
            "⬅": Menu.Menupoint("return", self.main_menu, submenu=True),
        }
        menu.header = self.get_resource_str(self.get_player(menu.author).resources)
        menu.change_menu(m)

    def resource_menu(self, menu):
        m = {
            "🍪": Menu.Menupoint("resources", menu.build_f(self.print_resources, (menu.author, menu.channel))),
            "⬅": Menu.Menupoint("return", self.main_menu, submenu=True),
        }
        menu.header = self.get_resource_str(self.get_player(menu.author).resources)
        menu.change_menu(m)

    def military_menu(self, menu):
        military_menu = {}
        player = self.get_player(menu.author)
        for player_b in player.buildings:
            if issubclass(player_b.__class__, Building.Military):
                f = self.get_building_menu(player_b)
                military_menu[player_b.emoji] = Menu.Menupoint(player_b.name, f, submenu=True)
        military_menu["🎖"] = Menu.Menupoint("units", menu.build_f(self.print_units, (menu.author, menu.channel)))
        military_menu["⬅"] = Menu.Menupoint("return", self.main_menu, submenu=True)
        menu.header = self.get_resource_str(self.get_player(menu.author).resources, detail=True)
        menu.change_menu(military_menu)

    def build_menu(self, menu):
        build_menu = {}
        for b in self.get_buildable(menu.author):
            f = menu.build_f(self.build, (menu.author, menu.channel, b))
            build_menu[b.emoji] = Menu.Menupoint(b.name + "\t cost:" + self.get_resource_str(b.build_cost), menu.get_recall_wrapper(f, self.build_menu))
        build_menu["⬅"] = Menu.Menupoint("return", self.candy_manor_menu, submenu=True)
        menu.header = self.get_resource_str(self.get_player(menu.author).resources, detail=True)
        menu.change_menu(build_menu)

    def upgrade_menu(self, menu):
        upgrade_menu = {}
        for b in self.get_upgradable(menu.author):
            f = menu.build_f(self.upgrade, (menu.author, menu.channel, b))
            upgrade_menu[b.emoji] = Menu.Menupoint(b.name + "\t cost:" + self.get_resource_str(b.next_price()), menu.get_recall_wrapper(f, self.upgrade_menu))
        upgrade_menu["⬅"] = Menu.Menupoint("return", self.candy_manor_menu, submenu=True)
        menu.header = self.get_resource_str(self.get_player(menu.author).resources, detail=True)
        menu.change_menu(upgrade_menu)

    def military_building_menu(self, menu, player_b):
        """prints the menu for a military building. DO NOT USE DIRECTLY. use get_building_menu to create"""
        building_menu = {}
        for u in self.get_buildable_units(menu.author, player_b):
            f = menu.build_f(self.prep_units, (menu.author, menu.channel, player_b, u))
            building_menu[u.emoji] = Menu.Menupoint(u.name + "\tcost: " + self.get_resource_str(u.price), f)
        building_menu["🏃"] = Menu.Menupoint("prepped", menu.build_f(self.print_building_prepared, (menu.channel, player_b)))
        building_menu["👍"] = Menu.Menupoint("start training", menu.build_f(self.start_building_prepped, (menu.author, menu.channel, player_b)))
        building_menu["👷"] = Menu.Menupoint("currently building", menu.build_f(self.print_building_threads, (menu.channel, player_b)))
        building_menu["⬅"] = Menu.Menupoint("return", self.military_menu, submenu=True)
        menu.header = self.get_resource_str(self.get_player(menu.author).resources, detail=True)
        menu.change_menu(building_menu)

    def get_building_menu(self, player_b):
        """returns a function that will create the correct menu for the building and only need the menu as parameter"""
        def f(menu):
            self.military_building_menu(menu, player_b)
        return f

    # properties
    @property
    def unit_time(self):
        return self.unit_time_f()
