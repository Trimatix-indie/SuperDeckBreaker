import discord
import traceback
from datetime import datetime

from . import commandsDB as botCommands
from .. import botState, lib

from . import util_help


async def dev_cmd_dev_help(message: discord.Message, args: str, isDM: bool):
    """dev command printing help strings for dev commands

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    await util_help.util_autohelp(message, args, isDM, 3)

botCommands.register("dev-help", dev_cmd_dev_help, 3, signatureStr="**dev-help** *[page number, section or command]*",
                        shortHelp="Display information about developer-only commands.\nGive a specific command for " +
                                    "detailed info about it, or give a page number or give a section name for brief info.",
                        longHelp="Display information about developer-only commands.\nGive a specific command for " +
                                    "detailed info about it, or give a page number or give a section name for brief info " +
                                    "about a set of commands. These are the currently valid section names:\n- Miscellaneous")


async def dev_cmd_sleep(message: discord.Message, args: str, isDM: bool):
    """developer command saving all data to JSON and then shutting down the bot

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    botState.shutdown = botState.ShutDownState.shutdown
    await message.channel.send("shutting down.")
    await botState.client.shutdown()

botCommands.register("bot-sleep", dev_cmd_sleep, 3, allowDM=True, useDoc=True)


async def dev_cmd_save(message: discord.Message, args: str, isDM: bool):
    """developer command saving all databases to JSON

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    try:
        botState.client.saveAllDBs()
    except Exception as e:
        print("SAVING ERROR", e.__class__.__name__)
        print(traceback.format_exc())
        await message.channel.send("failed!")
        return
    print(datetime.now().strftime("%H:%M:%S: Data saved manually!"))
    await message.channel.send("saved!")

botCommands.register("save", dev_cmd_save, 3, allowDM=True, useDoc=True)


async def dev_cmd_say(message: discord.Message, args: str, isDM: bool):
    """developer command sending a message to the same channel as the command is called in

    :param discord.Message message: the discord message calling the command
    :param str args: string containing the message to broadcast
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    if args == "":
        await message.channel.send("provide a message!")
    else:
        await message.channel.send(**lib.discordUtil.messageArgsFromStr(args))

botCommands.register("say", dev_cmd_say, 3, forceKeepArgsCasing=True, allowDM=True, useDoc=True)


async def dev_cmd_reset_has_poll(message : discord.Message, args : str, isDM : bool):
    """developer command resetting the poll ownership of the calling user, or the specified user if one is given.

    :param discord.Message message: the discord message calling the command
    :param str args: string, can be empty or contain a user mention
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # reset the calling user's cooldown if no user is specified
    if args == "":
        botState.usersDB.getUser(message.author.id).pollOwned = False
        # otherwise get the specified user's discord object and reset their cooldown.
        # [!] no validation is done.
    else:
        botState.usersDB.getUser(int(args.lstrip("<@!").rstrip(">"))).pollOwned = False
    await message.channel.send("Done!")

botCommands.register("reset-has-poll", dev_cmd_reset_has_poll, 2, allowDM=True, useDoc=True)