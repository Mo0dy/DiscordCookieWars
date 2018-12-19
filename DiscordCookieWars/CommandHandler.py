"""the command handler takes user input validates it cand calls the correct bot method."""
import Building
import Unit


class CommandHandler(object):

    async def handle_message(self, message, bot):
        """handles the message"""
        if message.content.startswith(bot.command_prefix):  # check if this message is meant for this bot
            author = message.author
            channel = message.channel
            # extract the commands (separated by whitespace)
            com_list = message.content[len(bot.command_prefix):].split()
            if com_list:
                command = com_list[0]
            else:
                return  # just a question mark

            param = com_list[1:]

            mentions = message.mentions

            # a list of all commands and the functions they invoke
            commands = {
                "menu": self.build(bot.start_menu, (author, channel)),
                "help": self.build(bot.print_help, [channel]),
                "town": self.build(bot.print_town, (author, channel)),
                "resources": self.build(bot.print_resources, (author, channel)),
                "buildable": self.build(bot.print_buildable, (author, channel)),
                "upgradable": self.build(bot.print_upgrades, (author, channel)),
                "threads": self.build(bot.print_threads, (author, channel)),
                "print_units": self.build(bot.print_units, (author, channel)),
                "requirements": self.print_requirements(author, param, bot, channel),
                "building_threads": self.print_building_threads(author, param, bot, channel),
                "building_prepared": self.print_building_prepared(author, param, bot, channel),
                "start_building_prepared": self.start_building_prepared(author, param, bot, channel),
                "build": self.build_building(author, param, bot, channel),
                "upgrade": self.upgrade_building(author, param, bot, channel),
                "prep_units": self.prep_units(author, param, bot, channel),
                "rally_troops": self.rally_troops(author, param, bot, channel),
            }

            admin_commands = {

            }

            # special cases:
            if command == "join":
                await bot.join(author, channel)
            elif command in commands:  # general case
                # check if user is new else print: ?join
                if author.id not in bot.players.keys():
                    # user is new
                    await bot.send_message(channel, "to join the game type: \"%sjoin\"" % bot.command_prefix)
                    return
                await commands[command]()  # call the event
            elif command in admin_commands:
                if message.author.server_permissions.administrator:
                    await admin_commands[command](author, mentions, channel, com_list[1:])
                else:
                    await bot.send_message(channel, "%s incorrect permissions" % bot.get_mention(author))

    @staticmethod
    def build(f, args, check=None):
        """returns a function that can be called without arguments that will then use the args provided here"""
        return lambda: f(*args)

    # all functions that need special checks for parameters first

    @staticmethod
    def print_requirements(author, param, bot, channel):
        async def f():
            if not param:
                await bot.send_message(channel, "wrong parameters")
                return

            building_str = param[0].lower()
            if not building_str in Building.buildings_table.keys():
                await bot.send_message(channel, "no such building")
                return
            building = Building.buildings_table[building_str]

            player = bot.get_player(author)

            player_b = player.get_building(building)
            await bot.print_requirements(channel, player_b)
        return f

    @staticmethod
    def print_building_threads(author, param, bot, channel):
        """prints the threads of a specific building if the parameters are correct"""
        async def f():
            player_b = await CommandHandler.check_valid_military_building_param(author, param, channel, bot)
            if not player_b:
                return
            await bot.print_building_threads(channel, player_b)
        return f

    @staticmethod
    def print_building_prepared(author, param, bot, channel):
        async def f():
            player_b = await CommandHandler.check_valid_military_building_param(author, param, channel, bot)
            if not player_b:
                return
            await bot.print_building_prepared(channel, player_b)
        return f

    @staticmethod
    def start_building_prepared(author, param, bot, channel):
        async def f():
            player_b = await CommandHandler.check_valid_military_building_param(author, param, channel, bot)
            if not player_b:
                return
            await bot.print_building_prepared(author, channel, player_b)
        return f

    @staticmethod
    def build_building(author, param, bot, channel):
        """start building a building"""
        async def f():
            if not param:
                await bot.send_message(channel, "%s wrong parameters for ?build" % bot.get_mention(author))
                return
            if not param[0].lower() in Building.buildings_table:
                await bot.send_message(channel, "%s no such building." % bot.get_mention(author))
                return

            building = Building.buildings_table[param[0].lower()]
            await bot.build(author, channel, building)
        return f

    @staticmethod
    def upgrade_building(author, param, bot, channel):
        """start building a building"""
        async def f():
            if not param:
                await bot.send_message(channel, "%s wrong parameters for ?build" % bot.get_mention(author))

            if not param[0].lower() in Building.buildings_table:
                await bot.send_message(channel, "%s no such building." % bot.get_mention(author))
                return

            building = Building.buildings_table[param[0].lower()]
            player_b = bot.get_player(author).get_building(building)
            if not player_b:
                await bot.send_message(channel, "you don't have this building yet")
                return
            await bot.upgrade(author, channel, building)
        return f

    @staticmethod
    def prep_units(author, param, bot, channel):
        """prepare some units to build in a military institution"""
        # command: <prefix><command> <building><unit>
        async def f():
            if len(param) < 2:
                await bot.send_message(channel, "%s wrong parameters for ?upgrade" % bot.get_mention(author))
            building_str = param[0]
            unit_str = param[1]
            player = bot.get_player(author)
            building = player.get_building(Building.buildings_table[building_str])
            if not building:
                await bot.send_message(channel, "you don't have the building required")
                return
            if not issubclass(building.__class__, Building.Military):
                await bot.send_message(channel, "this is not a military building")
                return
            if unit_str not in Unit.units_table:
                await bot.send_message(channel, "no such unit")
                return
            unit = Unit.units_table[unit_str]

            # try to get the amount from the parameters
            amount = None
            if len(param) > 2 and param[2].isdigit():
                amount = int(param[2])

            # parameters are correct
            print("FUNCTION NOT DONE. DOES NOT CHECK LEVEL")
            # bot.prep_units(author, channel, building, unit, amount)

    @staticmethod
    def rally_troops(author, param, bot, channel):
        pass

    # utility ====================================================

    @staticmethod
    async def check_valid_military_building_param(author, param, channel, bot):
        """checks if the parameters are generally acceptable for a command of type: ?<command> <m_building>"""
        if await bot.ifnew(author, bot.get_message_func(channel)):
            return
        player = bot.get_player(author)
        if not param[0]:
            await bot.send_message(channel, "wrong parameters")
            return
        if param[0] not in Building.buildings_table:
            await bot.send_message(channel, "no such building")
            return
        building = Building.buildings_table[param[0]]
        player_b = player.get_building(building)
        if not player_b:
            await bot.send_message(channel, "you don't have this building")
            return
        if not issubclass(player_b.__class__, Building.Military):
            await bot.send_message(channel, "this is not a military building")
            return
        return player_b