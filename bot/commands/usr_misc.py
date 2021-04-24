from bot import botState
from bot.cfg import versionInfo
import discord
from datetime import datetime, timedelta
import operator

from . import commandsDB as botCommands
from . import util_help
from .. import lib
from ..cfg import versionInfo, cfg
from ..reactionMenus import reactionPollMenu
from ..scheduling.timedTask import TimedTask


TROPHY_ICON = "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/248/trophy_1f3c6.png"


async def cmd_help(message: discord.Message, args: str, isDM: bool):
    """Print the help strings as an embed.
    If a command is provided in args, the associated help string for just that command is printed.

    :param discord.Message message: the discord message calling the command
    :param str args: empty, or a single command name
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    await util_help.util_autohelp(message, args, isDM, 0)

botCommands.register("help", cmd_help, 0, allowDM=True, signatureStr="**help** *[page number, section or command]*",
                     shortHelp="Show usage information for available commands.\nGive a specific command for detailed info " +
                                "about it, or give a page number or give a section name for brief info.",
                     longHelp="Show usage information for available commands.\nGive a specific command for detailed info " +
                                "about it, or give a page number or give a section name for brief info about a set of " +
                                "commands. These are the currently valid section names:\n- Miscellaneous",
                     useDoc=False)


async def cmd_source(message: discord.Message, args: str, isDM: bool):
    """Print a short message with information about the bot's source code.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    srcEmbed = lib.discordUtil.makeEmbed(authorName="Source Code",
                                         col=discord.Colour.purple(),
                                         icon="https://image.flaticon.com/icons/png/512/25/25231.png",
                                         footerTxt="Bot Source",
                                         footerIcon="https://i.imgur.com/7SMgF0t.png")
    srcEmbed.add_field(name="Uptime",
                       value=lib.timeUtil.td_format_noYM(datetime.utcnow() - botState.client.launchTime))
    srcEmbed.add_field(name="Author",
                       value="Trimatix#2244 & sHiiNe#4265")
    srcEmbed.add_field(name="API",
                       value="[Discord.py " + discord.__version__ + "](https://github.com/Rapptz/discord.py/)")
    srcEmbed.add_field(name="BASED",
                       value="[BASED " + versionInfo.BASED_VERSION + "](https://github.com/Trimatix/BASED)")
    srcEmbed.add_field(name="GitHub",
                       value="[Trimatix-indie/SuperDeckBreaker](https://github.com/Trimatix-indie/SuperDeckBreaker)")
    srcEmbed.add_field(name="Invite",
                       value="No public invite currently.")
    await message.channel.send(embed=srcEmbed)

botCommands.register("source", cmd_source, 0, allowDM=True, signatureStr="**source**",
                     shortHelp="Show links to the project's GitHub page.")


async def cmd_leaderboard(message : discord.Message, args : str, isDM : bool):
    """display leaderboards for different statistics
    if no arguments are given, display the local leaderboard for rounds won.
    if `global` is given, display the appropriate leaderbaord across all guilds
    if `wins` is given, display the leaderboard for game wins

    :param discord.Message message: the discord message calling the command
    :param str args: string containing the arguments the user passed to the command
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # across all guilds?
    globalBoard = False
    # stat to display
    stat = "round wins"
    # "global" or the local guild name
    boardScope = message.guild.name
    # user friendly string for the stat
    boardTitle = "Rounds Won"
    # units for the stat
    boardUnit = "Round"
    boardUnits = "Rounds"
    boardDesc = "*Total number of rounds won"

    if isDM:
        prefix = cfg.defaultCommandPrefix
    else:
        prefix = botState.guildsDB.getGuild(message.guild.id).commandPrefix

    # change leaderboard arguments based on the what is provided in args
    if args != "":
        argsSplit = args.split(" ")
        
        if len(argsSplit) > 3:
            await message.channel.send(":x: Too many arguments! Please only specify one leaderboard. E.g: `" + prefix \
                                        + "leaderboard global wins`")
            return
        for arg in argsSplit:
            if arg not in ["wins", "round wins", "global"]:
                await message.channel.send(":x: Unknown argument: '**" + arg + "**'. Please refer to `" + prefix \
                                            + "help leaderboard`")
                return
        if "wins" in argsSplit:
            stat = "game wins"
            boardTitle = "Games Won"
            boardUnit = "Game"
            boardUnits = "Games"
            boardDesc = "*Total number of games won"
        if "global" in argsSplit:
            globalBoard = True
            boardScope = "Global Leaderboard"
            boardDesc += " across all servers"

    boardDesc += ".*"

    # get the requested stats and sort users by the stat
    inputDict = {}
    for user in botState.usersDB.getUsers():
        if (globalBoard and botState.client.get_user(user.id) is not None) or \
                (not globalBoard and message.guild.get_member(user.id) is not None):
            inputDict[user.id] = user.getStatByName(stat)
    sortedUsers = sorted(inputDict.items(), key=operator.itemgetter(1))[::-1]

    # build the leaderboard embed
    leaderboardEmbed = lib.discordUtil.makeEmbed(titleTxt=boardTitle, authorName=boardScope,
                                                    icon=TROPHY_ICON, col=discord.Colour.random(), desc=boardDesc)

    # add all users to the leaderboard embed with places and values
    externalUser = False
    first = True
    for place in range(min(len(sortedUsers), 10)):
        # handling for global leaderboards and users not in the local guild
        if globalBoard and message.guild.get_member(sortedUsers[place][0]) is None:
            leaderboardEmbed.add_field(value="*" + str(place + 1) + ". " \
                                            + str(botState.client.get_user(sortedUsers[place][0])),
                                        name=("⭐ " if first else "") + str(sortedUsers[place][1]) + " " \
                                            + (boardUnit if sortedUsers[place][1] == 1 else boardUnits), inline=False)
            externalUser = True
            if first:
                first = False
        else:
            leaderboardEmbed.add_field(value=str(place + 1) + ". " + message.guild.get_member(sortedUsers[place][0]).mention,
                                        name=("⭐ " if first else "") + str(sortedUsers[place][1]) + " " \
                                            + (boardUnit if sortedUsers[place][1] == 1 else boardUnits), inline=False)
            if first:
                first = False
    # If at least one external use is on the leaderboard, give a key
    if externalUser:
        leaderboardEmbed.set_footer(
            text="An * indicates a user that is from another server.")
    # send the embed
    await message.channel.send(embed=leaderboardEmbed)

botCommands.register("leaderboard", cmd_leaderboard, 0, allowDM=False, signatureStr="**leaderboard** *[global] [wins]*",
                        longHelp="Show the leaderboard for total number of rounds won. Give `global` for the global leaderboard, " \
                            + "not just this server.\n> Give `wins` for the total *game* wins leaderboard.")


async def cmd_poll(message : discord.Message, args : str, isDM : bool):
        """Run a reaction-based poll, allowing users to choose between several named options.
        Users may not create more than one poll at a time, anywhere.
        Option reactions must be either unicode, or custom to the server where the poll is being created.

        args must contain a poll subject (question) and new line, followed by a newline-separated list of emoji-option pairs, where each pair is separated with a space.
        For example: 'Which one?\n0️⃣ option a\n1️⃣ my second option\n2️⃣ three' will produce three options:
        - 'option a'         which participants vote for by adding the 0️⃣ reaction
        - 'my second option' which participants vote for by adding the 1️⃣ reaction
        - 'three'            which participants vote for by adding the 2️⃣ reaction
        and the subject of the poll is 'Which one?'
        The poll subject is optional. To not provide a subject, simply begin args with a new line.

        args may also optionally contain the following keyword arguments, given as argname=value
        - multiplechoice : Whether or not to allow participants to vote for multiple poll options. Must be true or false.
        - days           : The number of days that the poll should run for. Must be at least one, or unspecified.
        - hours          : The number of hours that the poll should run for. Must be at least one, or unspecified.
        - minutes        : The number of minutes that the poll should run for. Must be at least one, or unspecified.
        - seconds        : The number of seconds that the poll should run for. Must be at least one, or unspecified.

        :param discord.Message message: the discord message calling the command
        :param str args: A comma-separated list of space-separated emoji-option pairs, and optionally any kwargs as specified
                            in this function's docstring
        :param bool isDM: Whether or not the command is being called from a DM channel
        """
        if botState.usersDB.idExists(message.author.id) and botState.usersDB.getUser(message.author.id).pollOwned:
            await message.channel.send(":x: You can only make one poll at a time!")
            return

        pollOptions = {}
        kwArgs = {}
        callingBGuild = botState.guildsDB.getGuild(message.guild.id)

        argsSplit = args.split("\n")
        if len(argsSplit) < 2:
            await message.reply(":x: Invalid arguments! Please provide your poll subject, followed by a new line, " \
                                    + "then a new line-separated series of poll options.\nFor more info, see `" \
                                    + callingBGuild.commandPrefix + "help poll`")
            return
        pollSubject = argsSplit[0]
        argPos = 0
        for arg in argsSplit[1:]:
            if arg == "":
                continue
            arg = arg.strip()
            argSplit = arg.split(" ")
            argPos += 1
            try:
                optionName, dumbReact = arg[arg.index(" ")+1:], lib.emojis.BasedEmoji.fromStr(argSplit[0], rejectInvalid=True)
            except (ValueError, IndexError):
                for kwArg in ["days=", "hours=", "seconds=", "minutes=", "multiplechoice="]:
                    if arg.lower().startswith(kwArg):
                        kwArgs[kwArg[:-1]] = arg[len(kwArg):]
                        break
            except lib.exceptions.UnrecognisedCustomEmoji:
                await message.reply(":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) \
                                        + " emoji!\nYou can only use built in emojis, or custom emojis that are in this server.")
                return
            except TypeError:
                await message.reply(":x: Invalid emoji: " + argSplit[1])
                return
            else:
                if dumbReact.sendable == "None":
                    await message.reply(":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) \
                                                + " emoji!\nYou can only use built in emojis, or custom emojis that are in this server.")
                    return
                if dumbReact is None:
                    await message.reply(":x: Invalid emoji: " + argSplit[1])
                    return
                elif dumbReact.isID:
                    localEmoji = False
                    for localEmoji in message.guild.emojis:
                        if localEmoji.id == dumbReact.id:
                            localEmoji = True
                            break
                    if not localEmoji:
                        await message.reply(":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) \
                                                + " emoji!\nYou can only use built in emojis, or custom emojis that are in this server.")
                        return

                if dumbReact in pollOptions:
                    await message.reply(":x: Cannot use the same emoji for two options!")
                    return

                pollOptions[dumbReact] = optionName

        if len(pollOptions) == 0:
            await message.reply(":x: You need to give some options to vote on!\nFor more info, see `" \
                                    + callingBGuild.commandPrefix + "help poll`")
            return
        
        timeoutDict = {}

        for timeName in ["days", "hours", "minutes", "seconds"]:
            if timeName in kwArgs:
                if not lib.stringTyping.isInt(kwArgs[timeName]) or int(kwArgs[timeName]) < 1:
                    await message.reply(":x: Invalid number of " + timeName + " before timeout!")
                    return

                timeoutDict[timeName] = int(kwArgs[timeName])

        multipleChoice = True
        if "multiplechoice" in kwArgs:
            if kwArgs["multiplechoice"].lower() in ["off", "no", "false", "single", "one"]:
                multipleChoice = False
            elif kwArgs["multiplechoice"].lower() not in ["on", "yes", "true", "multiple", "many"]:
                await message.reply("Invalid `multiplechoice` setting: '" + kwArgs["multiplechoice"] \
                                        + "'\nPlease use either `multiplechoice=yes` or `multiplechoice=no`")
                return

        timeoutTD = lib.timeUtil.timeDeltaFromDict(timeoutDict if timeoutDict else cfg.timeouts.defaultPollLength)
        maxTimeout = lib.timeUtil.timeDeltaFromDict(cfg.timeouts.maxPollLength)
        if timeoutTD > maxTimeout:
            await message.reply(":x: Invalid poll length! The maximum poll length is **" \
                                    + lib.timeUtil.td_format_noYM(maxTimeout) + ".**")
            return

        menuMsg = await message.channel.send("‎")

        timeoutTT = TimedTask(expiryDelta=timeoutTD, expiryFunction=reactionPollMenu.showResultsAndExpirePoll,
                                expiryFunctionArgs=menuMsg.id)
        botState.taskScheduler.scheduleTask(timeoutTT)

        menu = reactionPollMenu.ReactionPollMenu(menuMsg, pollOptions, timeoutTT, pollStarter=message.author,
                                                    multipleChoice=multipleChoice, desc=pollSubject)
        await menu.updateMessage()
        botState.reactionMenusDB[menuMsg.id] = menu
        botState.usersDB.getOrAddID(message.author.id).pollOwned = True

botCommands.register("poll", cmd_poll, 0, forceKeepArgsCasing=True, allowDM=False,
                        signatureStr="**poll** *<subject>*\n**<option1 emoji> <option1 name>**\n...    ...\n*[kwargs]*",
                        shortHelp="Start a reaction-based poll. Each option must be on its own new line, as an emoji, " \
                            + "followed by a space, followed by the option name.",
                        longHelp="Start a reaction-based poll. Each option must be on its own new line, as an emoji, " \
                            + "followed by a space, followed by the option name. The `subject` is the question that users " \
                            + "answer in the poll and is optional, to exclude your subject simply give a new line.\n\n" \
                            + "__Optional Arguments__\nOptional arguments should be given by `name=value`, with each arg " \
                                + "on a new line.\n" \
                            + "- Give `multiplechoice=no` to only allow one vote per person (default: yes).\n" \
                            + "- You may specify the length of the poll, with each time division on a new line. Acceptable " \
                                + "time divisions are: `seconds`, `minutes`, `hours`, `days`. (default: minutes=5)")
