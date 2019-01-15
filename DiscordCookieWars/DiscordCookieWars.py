import discord
import asyncio
from Bot import Bot
from Player import Player
from CommandHandler import CommandHandler
import time
from aiohttp.errors import ClientOSError
from Utility import load_custom_emojis

special_command = ".cmd"


# seconds per unit of time. The game will update with every unit and every time measurement in game will have to be in
# multiples of this e.g. a time of 3 would mean 3 * unit_time seconds
unit_time = 15 * 60


token = open('debug.token', 'r').readlines()[0].strip()  # load the bot token
client = discord.Client()  # create the client class
c_handler = CommandHandler()  # create a new command handler


# a list of all bots. This is used to pass messages the client receives to the bots. there is one bot per server
# the key is the server id
bots = {}


def get_unit_time():
    return unit_time


# allow all bot and player classes to get unit time
Bot.unit_time_f = get_unit_time
Player.unit_time_f = get_unit_time


def run_client():
    """launches the client"""
    loop = asyncio.get_event_loop()
    while True:
        try:
            loop.run_until_complete(client.start(token))
        except ClientOSError as e:
            print("Error", e)
            print("wait until restart")
            time.sleep(60)  # try once a minute to reconnect


@client.event
async def on_resumed():
    print("resumed")


@client.event
async def on_ready():
    """when the client is logged in and ready this will be called. It prepares everything the bot needs"""
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")

    # create one bot per server
    for s in client.servers:
        bots[s.id] = Bot(client, s.id)
    # load custom emojis
    load_custom_emojis(client)
    while True:
        # starts the update loop. this will only return if there is an error
        await update_loop()  # start the update loop
        print("ERROR THE UPDATE LOOP FAILED")


@client.event
async def on_message(message):
    global unit_time
    # special commands can only be used my #Mo0dy#5444
    if message.content.startswith(special_command) and message.author.id == "159065682137317376":
        command_list = message.content[len(special_command):].split()
        command = command_list[0]
        if command == "set_unit_time":
            if len(command_list) > 1:
                unit_time = float(command_list[1])
        return

    """relays the message to the correct bot"""
    if message.server:
        server_id = message.server.id
    else:
        if message.author != client.user:
            print("received private message:\n%s" % message.content)
        return

    # if there is no bot on this server create a new bot
    if not server_id in bots.keys():
        bots[server_id] = Bot(client, server_id)

    # relay the message to the correct bot
    await c_handler.handle_message(message, bots[server_id])
    # await bots[server_id].handle_message(message)


async def update_loop():
    """This is the main update loop. It will call the bots update functions ever unit of time"""
    while True:
        update_calls = max(1, int(unit_time / 5))  # one update call every 5 seconds and at least one
        for _ in range(update_calls):
            for b in bots.values():
                await b.fast_update()
            await asyncio.sleep(unit_time / update_calls)

        for b in bots.values():
            await b.update()

# start the bot
run_client()
