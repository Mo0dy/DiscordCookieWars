import discord
import asyncio


class Menupoint(object):
    def __init__(self, name, func, submenu=False):
        self.name = name
        self.func = func
        self.submenu = submenu  # if it is a submenu it will be passed the menu object


class Menu(object):
    def __init__(self, client, channel, author):
        self.author = author
        self.client = client
        self.channel = channel
        self.timeout = 30
        self.header = None

        # a dictionary connecting emojis with menupoints
        self.current_menu = {}

    async def start(self):
        m, r = await self.write_menu()
        asyncio.sleep(1)
        while True:
            if not r:  # no early reaction -> wait for reaction
                ret_val = await self.client.wait_for_reaction(user=self.author, timeout=self.timeout, message=m)
                if not ret_val:  # timeout
                    await self.client.delete_message(m)
                    break
                r, _ = ret_val

            await self.client.delete_message(m)
            # change menu according to reaction
            if r.emoji in self.current_menu.keys():
                m_point = self.current_menu[r.emoji]
                if m_point.submenu:  # call func with this menu as argument
                    m_point.func(self)
                else:
                    await m_point.func()
            m, r = await self.write_menu()
        return

    async def write_menu(self):
        """printes the menu and returns the message

        :return: message, reaction (if there has been an early reaction)
        """
        lines = ["======================================="]
        if self.header:
            lines.append(self.header)
        lines.append("========================")
        for e, m_point in self.current_menu.items():
            lines.append("{:<4}: {:<20}".format(e, m_point.name))
        lines.append("=======================================")
        message = await self.client.send_message(self.channel, "**%ss** menu\n%s" % (self.author.name, "\n".join(lines)))

        for e in self.current_menu.keys():
            await self.client.add_reaction(message, e)
            updated_message = await self.client.get_message(message.channel, message.id)
            for r in updated_message.reactions:
                if self.author in await self.client.get_reaction_users(r):
                    return message, r
        return message, None

    @staticmethod
    def build_f(f, args):
        """builds a function that will call f with *args"""
        return lambda: f(*args)

    def get_recall_wrapper(self, function, menu_function, async=True):
        """calls first the function then the menu"""
        if async:
            async def f():
                await function()
                menu_function(self)
        else:
            async def f():
                function()
                menu_function(self)
        return f

    def change_menu(self, menu):
        self.current_menu = menu
