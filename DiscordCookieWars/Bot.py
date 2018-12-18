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
    def __init__(self, client, server):
        self.command_prefix = "?"
        self.client = client  # the client that can be used to interact with discord

        # the player classes. the key is the id of the user owning the player
        self.players = {}
        # this is used for saving and loading information. it is the id of the server this bot is running for
        self.server = server

    async def update(self):
        """gets called about twice a minute and is used for timed events"""

        # call the update method of all players
        print("\nUPDATE BOT %s ========================" % self.server)
        for p in self.players.values():
            print("Player: %s ===========" % p.owner)
            await p.update()

    async def send_message(self, channel, content):
        """send a message to a channel on a server"""
        await self.client.send_message(channel, content)

    async def handle_message(self, message):
        """handle the message input"""
        if message.content.startswith(self.command_prefix):  # check if this message is meant for this bot
            author = message.author
            channel = message.channel
            com_list = message.content[len(self.command_prefix):].split()  # extract the commands (seperated by whitespace)
            if com_list:
                command = com_list[0]
            else:
                return  # just a questionmark

            mentions = message.mentions

            # a list of all commands and the functions they invoke
            commands = {
                "join": self.join,
                "town": self.print_town,
                "build": self.build,
                "upgrade": self.upgrade,
                "resources": self.print_resources,
                "upgradable": self.print_upgradable,
                "buildable": self.print_buildable,
                "requirements": self.print_requirements,
                "building": self.print_threads,
                "menu": self.start_menu,
            }

            admin_commands = {

            }

            if command in commands:
                await commands[command](author, mentions, channel, com_list[1:])  # call the event
            elif command in admin_commands:
                if message.author.server_permissions.administrator:
                    await admin_commands[command](author, mentions, channel, com_list[1:])
                else:
                    self.send_message(channel, "%s incorrect permissions" % self.get_mention(author))

    # commands =============================================================
    async def join(self, author, mentions, channel, param):
        """a new user joins the game"""
        if author.id not in self.players.keys():
            self.players[author.id] = Player.Player(author.id)  # add a new player to the list of players
            await self.send_message(channel, "%s you joined the cookie wars!" % self.get_mention(author))
        else:
            await self.send_message(channel, "% you already joined the cookie wars.")

    async def start_menu(self, author, mentions, channel, param):
        if await self.ifnew(author, self.get_message_func(channel)):
            return
        menu = Menu.Menu(self.client, channel, author)
        self.main_menu(menu)
        await menu.start()

    async def print_town(self, author, mentions, channel, param):
        """prints information about the town"""
        if await self.ifnew(author,self.get_message_func(channel)):
            return
        await self.send_message(channel, 'buildings: \n%s\n' % '\n'.join(["{:<5}{:<20}{}".format(b.emoji, b.name, b.level) for b in self.get_player(author).buildings]))

    async def print_resources(self, author, mentions, channel, param):
        """prints the amount of resources the player has"""
        if await self.ifnew(author, self.get_message_func(channel)):
            return
        await self.send_message(channel, 'resources: ```%s\n```' % '\n'.join(["{:<14}{}".format(r, a) for r, a in self.get_player(author).resources.items()]))

    async def print_buildable(self, author, mentions, channel, param):
        """prints all the buildings the player has fulfilled requirements for"""
        if await self.ifnew(author,self.get_message_func(channel)):
            return

        lines = []
        for b in self.get_buildable(author):
            lines.append(b.name)

        await self.send_message(channel, "\nyou can build:\n" + "\n".join(lines))

    async def print_upgradable(self, author, mentions, channel, param):
        """prints all the upgrades the player has fulfilled requirements for"""
        if await self.ifnew(author, self.get_message_func(channel)):
            return

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

    async def print_requirements(self, author, mentions, channel, param):
        if await self.ifnew(author, self.get_message_func(channel)):
            return
        if not param:
            await self.send_message(channel, "wrong parameters")
            return

        building_str = param[0].lower()
        if not building_str in buildings_table.keys():
            await self.send_message(channel, "no such building")
            return
        building = buildings_table[building_str]

        player = self.get_player(author)

        player_b = player.get_building(building)
        if player_b: # we need to get the upgrade
            if player_b.can_upgrade():
                requirements = player_b.next_requirements()
            else:
                await self.send_message(channel, "building is already max level")
        else:  # we need to get the build requirements
            requirements = building.build_requirements

        await self.send_message(channel, " \nthe requirements are:\n" "\n".join("{:<15} lvl {}".format(b, lvl) for b, lvl in requirements.items()))

    async def print_threads(self, author, mentions, channel, param):
        if await self.ifnew(author, self.get_message_func(channel)):
            return
        player = self.get_player(author)

        await self.send_message(channel, "currently building:\n %s" % "\n".join([str(t) for t in player.build_threads]))

    async def print_building_threads(self, author, mentions, channel, param):
        player_b = await self.check_valid_military_building_command(author, param, channel)
        if not player_b:
            return

        await self.send_message(channel, "currently building:\n %s" % "\n".join([str(t) for t in player_b.build_threads]))

    async def print_prepared(self, author, mentions, channel, param):
        """prints the prepared units in a building"""
        player_b = await self.check_valid_military_building_command(author, param, channel)
        if not player_b:
            return

        # empty dictionary
        if not player_b.build_prep:
            await self.send_message(channel, "noting prepped")
            return

        units_list = "\n".join(["{:<10}({:<4}):  lvl {:<10}x{:<2}".format(u.name, u.emoji, u.level, amount) for u, amount in player_b.build_prep.items()])
        cost_list = "\n".join(["{:<10} x{:<4}".format(resource, amount) for resource, amount in player_b.total_cost().items()])

        await self.send_message(channel, "%s prepped units:\n=====================\n%s\n=========\ncost:\n%s\n=====================" % (param[0], units_list, cost_list))

    async def start_prepped_build(self, author, mention, channel, param):
        """starts the prepped build of a military building if the user has the resources"""
        player_b = await self.check_valid_military_building_command(author, param, channel)
        if not player_b:
            return
        started_build = await player_b.build_units(self.get_player(author), self.get_message_func(channel))
        if not started_build:
            await self.send_message(channel, "you don't have enough resources")
        else:
            await self.send_message(channel, "you started the prepepd build")

    async def print_units(self, author, mentions, channel, param):
        if await self.ifnew(author, self.get_message_func(channel)):
            return
        player = self.get_player(author)
        if not player.units:
            await self.send_message(channel, "you have no units")
            return

        units_list = "\n".join(["{:<10}({:<4}):  lvl {:<10}x{:<2}".format(u.name, u.emoji, u.level, amount) for u, amount in player.units.items()])

        await self.send_message(channel, "your units:\n================\n%s\n================" % units_list)

    async def build(self, author, mentions, channel, param):
        """build a new building"""
        if await self.ifnew(author,self.get_message_func(channel)):
            return
        if not param:
            await self.send_message(channel, "%s wrong parameters for ?build" % self.get_mention(author))

        if param[0].lower() in buildings_table:
            await self.get_player(author).build(buildings_table[param[0].lower()], self.get_message_func(channel))
        else:
            await self.send_message(channel, "%s no such building." % self.get_mention(author))

    async def upgrade(self, author, mentions, channel, param):
        """upgrade an existing building"""
        if await self.ifnew(author, self.get_message_func(channel)):
            return
        if not param:
            await self.send_message(channel, "%s wrong parameters for ?upgrade" % self.get_mention(author))

        if param[0].lower() in buildings_table:
            await self.get_player(author).upgrade(buildings_table[param[0].lower()], self.get_message_func(channel))
        else:
            await self.send_message(channel, "%s no such building." % self.get_mention(author))

    async def prep_units(self, author, mentions, channel, param):
        if await self.ifnew(author, self.get_message_func(channel)):
            return
        if len(param) < 2:
            await self.send_message(channel, "%s wrong parameters for ?upgrade" % self.get_mention(author))

        unit_type = param[0]
        unit_str = param[1]

        player = self.get_player(author)
        building = player.get_building(buildings_table[unit_type])
        if not building:
            await self.send_message(channel, "you don't have the building required")
            return
        if not issubclass(building.__class__, Building.Military):
            await self.send_message(channel, "this is not a military building")
            return

        if not unit_str in units_table:
            await self.send_message(channel, "no such unit")
            return

        # get the highest possible level of the unit
        requirements_list = [(key, value) for key, value in units_table[unit_str].requirements_list.items()]
        requirements_list.sort(key=lambda x: x[0], reverse=True)  # sort the list from high to low level

        unit_level = 0
        for level, requirements in requirements_list:
            if await player.can_build(None, requirements, self.send_message):
                unit_level = level

        if not unit_level:
            await self.send_message(channel, "you have not yet met all the requirements")

        unit = units_table[unit_str](unit_level)

        if len(param) > 2 and param[2].isdigit():
            amount = int(param[2])
        else:
            await self.client.send_message(channel, "how many units do you want to create")
            answer = await self.client.wait_for_message(timeout=60, author=author, channel=channel, check=lambda x: x.content.isdigit())
            amount = int(answer.content)
        if amount <= 0:
            await self.send_message("the amount can not be 0")
            return

        # add the unit to the building prep
        building.prep_units(unit, amount)
        await self.send_message(channel, "your units have been added to the prep queue")

    # utility functions ===========================================================
    async def check_valid_military_building_command(self, user, param, channel):
        """checks for a command if the parameters are valid"""
        if await self.ifnew(user, self.get_message_func(channel)):
            return
        player = self.get_player(user)
        if not param[0]:
            await self.send_message(channel, "wrong parameters")
            return
        if param[0] not in buildings_table:
            await self.send_message(channel, "no such building")
            return
        building = buildings_table[param[0]]
        player_b = player.get_building(building)
        if not player_b:
            await self.send_message(channel, "you don't have this building")
            return
        if not issubclass(player_b.__class__, Building.Military):
            await self.send_message(channel, "this is not a military building")
            return
        return player_b

    def get_upgradable(self, user):
        player = self.get_player(user)
        upgradable = []
        for b in buildings_table.values():
            player_b = player.get_building(b)
            if player_b and not b in [t.building for t in player.build_threads]:
                upgrade_level = player_b.level + 1
                if player_b.can_upgrade():  # there is a price so there is another level
                    if upgrade_level in b.upgrade_requirements.keys():
                        if player.met_requirements(b.upgrade_requirements[upgrade_level]):
                            upgradable.append(b)
                    else:
                        upgradable.append(b)
        return upgradable

    def get_buildable(self, user):
        buildable = []
        player = self.get_player(user)
        for b in buildings_table.values():
            player_b = player.get_building(b)
            if not player_b and not b in [t.building for t in player.build_threads]:
                # the player doesn't yet have the building
                if player.met_requirements(b.build_requirements):
                    buildable.append(b)
        return buildable

    def get_buildable_units(self, user, unit_type):
        buildable = []
        player = self.get_player(user)
        for u in units_per_building[unit_type]:  # every unit that can be build in this building
            if player.met_requirements(u.requirements_list[1]):  # if the requirements for at least the first level are met
                buildable.append(u)
        return buildable

    def get_player(self, user):
        """returns a Player from a user id"""
        return self.players[user.id]

    async def ifnew(self, user, send_message):
        """checks if a user has joined the game or not"""
        if user.id in self.players.keys():
            return False
        else:
            await send_message("to join the game type: \"%sjoin\"" % self.command_prefix)
            return True

    def load_players(self):
        """load the player information from file"""
        self.players = RecourceManager.load_object(savepath + "_%s" % self.server)
        if not self.players:
            self.players = {}

    def save_players(self):
        """save the player information to file"""
        RecourceManager.save_object(self.players, savepath + "_%s" % self.server)

    def get_mention(self, user):
        """returns either a mention or the user in BOLD depending on the bot settings"""
        return '**%s**' % user.name

    def get_message_func(self, channel):
        """builds and returns a message function that can send a message to this channel"""
        async def f(content):
            await self.send_message(channel, content)
        return f

    def main_menu(self, menu):
        main_menu = {
            # "🛠": Menu.Menupoint("buildable", menu.get_command_wrapper(self.print_buildable)),
            "🛠": Menu.Menupoint("build", self.build_menu, submenu=True),
            # "⬆": Menu.Menupoint("upgradable", menu.get_command_wrapper(self.print_upgradable)),
            "⬆": Menu.Menupoint("upgrade", self.upgrade_menu, submenu=True),
            "⚔": Menu.Menupoint("military", self.military_menu, submenu =True),
            "🍪": Menu.Menupoint("resources", menu.get_command_wrapper(self.print_resources)),
            "👷": Menu.Menupoint("currently building", menu.get_command_wrapper(self.print_threads)),
            "🗺": Menu.Menupoint("town", menu.get_command_wrapper(self.print_town)),
        }
        menu.change_menu(main_menu)

    def build_menu(self, menu):
        build_menu = {}
        for b in self.get_buildable(menu.user):
            f = menu.get_command_wrapper(self.build, parameters=[b.command_name])
            build_menu[b.emoji] = Menu.Menupoint(b.name, menu.get_recall_wrapper(f, self.build_menu))
        build_menu["⬅"] = Menu.Menupoint("return", self.main_menu, submenu=True)
        menu.change_menu(build_menu)

    def upgrade_menu(self, menu):
        upgrade_menu = {}
        for b in self.get_upgradable(menu.user):
            f = menu.get_command_wrapper(self.upgrade, parameters=[b.command_name])
            upgrade_menu[b.emoji] = Menu.Menupoint(b.name, menu.get_recall_wrapper(f, self.upgrade_menu))
        upgrade_menu["⬅"] = Menu.Menupoint("return", self.main_menu, submenu=True)
        menu.change_menu(upgrade_menu)

    def military_menu(self, menu):
        military_menu = {}
        player = self.get_player(menu.user)
        for b in player.buildings:
            if issubclass(b.__class__, Building.Military):
                f = self.get_building_menu(b.command_name)
                military_menu[b.emoji] = Menu.Menupoint(b.name, f, submenu=True)
        military_menu["🎖"] = Menu.Menupoint("units", menu.get_command_wrapper(self.print_units))
        military_menu["⬅"] = Menu.Menupoint("return", self.main_menu, submenu=True)
        menu.change_menu(military_menu)

    def military_building_menu(self, menu, name):
        """prints the menu for a military building. DO NOT USE DIRECTLY. use get_building_menu to create"""
        building_menu = {}
        for u in self.get_buildable_units(menu.user, name):
            f = menu.get_command_wrapper(self.prep_units, parameters=[name, u.command_name])
            building_menu[u.emoji] = Menu.Menupoint(u.name, f)
        building_menu["🏃"] = Menu.Menupoint("prepped", menu.get_command_wrapper(self.print_prepared, parameters=[name]))
        building_menu["👍"] = Menu.Menupoint("start training", menu.get_command_wrapper(self.start_prepped_build, parameters=[name]))
        building_menu["👷"] = Menu.Menupoint("currently building", menu.get_command_wrapper(self.print_building_threads, parameters=[name]))
        building_menu["⬅"] = Menu.Menupoint("return", self.military_menu, submenu=True)
        menu.change_menu(building_menu)

    def get_building_menu(self, name):
        """returns a function that will create the correct menu for the building and only need the menu as parameter"""
        def f(menu):
            self.military_building_menu(menu, name)
        return f
