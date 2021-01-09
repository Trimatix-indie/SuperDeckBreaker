![BASED Banner](https://i.imgur.com/Nqoq3s4.png)

BASED is a template project for creating advanced discord bots using python.

BASED includes complete implementations for task scheduling, object and database saving with JSON, per-guild command prefixing, and custom access level-based commands handling with help command auto-generation.

BASED also includes a handy and extraordinarily versatile reaction menu implementation, allowing per-menu type saving implementations, advanced per-option menu behaviour, and support for both 'inline' and 'passive' calling styles.

Much more to come, including a game-specific fork with pre-written item and inventory classes.

# How to Make a BASED App
To make use of BASED, fork this repository and build your bot directly over BASED, using `bot.py` as your "main" file. This file is already working as is, with a connected client instance, dynamic commands importing and calling, scheduler and database initialization, and reactionMenu interaction using client events.
BASED is *not* a library, it is a *template* to be used as a starting point for your project.

Before your bot can be used, will need to provide your bot token. There are several ways of doing this.

If you intend to use a config.toml file, you can either:
- provide your bot token directly in the `botToken` config variable, or
- provide the name of an environment variable to fetch the bot token from in the `botToken_envVarName` variable.

If you do not intend to use a config.toml file, should provide your token/env var name in the `cfg.cfg` python module attributes with the same names as defined above.


# Configuring Your Bot
BASED v0.3 adds the ability to configure all of the bot's cfg attributes externally with toml. If no bot token is set in the `cfg.cfg` python module, a toml file containing at least this variable is required.

- A default config file containing all configurable variables and their default values can be generated by running `makeDefaultConfig.py`.
- To run the bot with your config, pass it through command-line arguments. e.g: `python3 main.py path-to-config.toml`
    - This path can be either absolute, or relative to the project root directory.
- All config variables are optional.
- Any emoji variable can be either unicode or custom.
    - give custom emojis as the emoji ID, or unicode emojis as a string containing a single unicode emoji character.
- The bot token can now be given in a config variable, or in an environment variable whose name is specified in config.
    - To give your token directly in the config file, specify it in the `botToken` config var.
    - To give your token in an environment variable, give the name of the environment variable in the `botToken_envVarName`
    - You must give exactly one of these variables.
    

# Running Your Bot
To run your bot, simply run `main.py`.

Alternatively, auto restarting and updating of the bot are provided by using one of the two looping bot launching scripts, `run.bat` and `run.sh`.

By launching your bot from a `run` script, dev_cmd_restart becomes functional. This command will restart the script. The `run` script will also restart your bot if critical errors are encountered, crashing the bot.

By giving the `-g` argument to a `run` script, dev_cmd_update becomes functional. ONLY specify `-g` if you have git installed on your system, and your bot is in a git tree.

Running `dev_cmd_update` will shut down the bot, run `git pull`, and restart the bot again. If conflicts are encountered with merging commits, the pull will be cancelled entirely. This error will not be announced to discord, and you should check your console after running dev_cmd_update to ensure that it was successful (or implement your own bot version checking command)


# How to Update Your BASED Fork
When new versions of BASED are released, assuming you have update checking enabled in `cfg.BASED_checkForUpdates`, you will be notified via console.
To update your BASED fork, create a pull request from the master branch of this repository into your fork.
Beware: conflicts are likely in this merge, especially if you have renamed BASED files, classes, functions or variables.

README unfinished.
