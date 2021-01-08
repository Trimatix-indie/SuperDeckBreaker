#!/usr/bin/env python3
import sys
import bot
from bot.cfg.configurator import loadCfg

if len(sys.argv) > 1:
    loadCfg(sys.argv[1])

bot.bot.run()