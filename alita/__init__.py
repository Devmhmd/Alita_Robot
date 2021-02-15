# Copyright (C) 2020 - 2021 Divkix. All rights reserved. Source code available under the AGPL.
#
# This file is part of Alita_Robot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from datetime import datetime
from importlib import import_module as imp_mod
from logging import INFO, WARNING, FileHandler, StreamHandler, basicConfig, getLogger
from os import environ, mkdir, path
from sys import exit as sysexit
from sys import stdout, version_info
from time import time

from aioredis import create_redis_pool

LOG_DATETIME = datetime.now().strftime("%d_%m_%Y-%H_%M_%S")
LOGDIR = f"{__name__}/logs"

# Make Logs directory if it does not exixts
if not path.isdir(LOGDIR):
    mkdir(LOGDIR)

LOGFILE = f"{LOGDIR}/{__name__}_{LOG_DATETIME}.txt"

file_handler = FileHandler(filename=LOGFILE)
stdout_handler = StreamHandler(stdout)

basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=INFO,
    handlers=[file_handler, stdout_handler],
)

getLogger("pyrogram").setLevel(WARNING)
LOGGER = getLogger(__name__)

# if version < 3.6, stop bot.
if version_info[0] < 3 or version_info[1] < 7:
    LOGGER.error(
        (
            "You MUST have a Python Version of at least 3.7!\n"
            "Multiple features depend on this. Bot quitting."
        ),
    )
    sysexit(1)  # Quit the Script

# the secret configuration specific things
try:
    if environ.get("ENV"):
        from alita.vars import Config
    else:
        from alita.vars import Development as Config
except Exception as ef:
    LOGGER.error(ef)  # Print Error
    sysexit(1)

redis_client = None


# Redis Cache
async def setup_redis():
    global redis_client
    redis_client = await create_redis_pool(
        address=(Config.REDIS_HOST, Config.REDIS_PORT),
        db=0,
        password=Config.REDIS_PASS,
    )
    try:
        await redis_client.ping()
        return redis_client
    except Exception as ef:
        LOGGER.error(f"Cannot connect to redis\nError: {ef}")
        return False


# Account Related
TOKEN = Config.TOKEN
APP_ID = Config.APP_ID
API_HASH = Config.API_HASH

# General Config
MESSAGE_DUMP = Config.MESSAGE_DUMP
SUPPORT_GROUP = Config.SUPPORT_GROUP
SUPPORT_CHANNEL = Config.SUPPORT_CHANNEL

# Users Config
OWNER_ID = Config.OWNER_ID
DEV_USERS = Config.DEV_USERS
SUDO_USERS = Config.SUDO_USERS
WHITELIST_USERS = Config.WHITELIST_USERS
SUPPORT_STAFF = list(
    dict.fromkeys([OWNER_ID] + SUDO_USERS + DEV_USERS + WHITELIST_USERS),
)  # Remove duplicates!

# Plugins, DB and Workers
DB_URI = Config.DB_URI
NO_LOAD = Config.NO_LOAD
WORKERS = Config.WORKERS

# Prefixes
PREFIX_HANDLER = Config.PREFIX_HANDLER
DEV_PREFIX_HANDLER = Config.DEV_PREFIX_HANDLER
ENABLED_LOCALES = Config.ENABLED_LOCALES
VERSION = Config.VERSION

HELP_COMMANDS = {}  # For help menu
UPTIME = time()  # Check bot uptime
BOT_USERNAME = ""
BOT_NAME = ""
BOT_ID = 0


async def get_self(c):
    global BOT_USERNAME, BOT_NAME, BOT_ID
    getbot = await c.get_me()
    BOT_NAME = getbot.first_name
    BOT_USERNAME = getbot.username
    BOT_ID = getbot.id
    return getbot


async def load_cmds(ALL_PLUGINS):
    for single in ALL_PLUGINS:
        imported_module = imp_mod("alita.plugins." + single)
        if not hasattr(imported_module, "__PLUGIN__"):
            imported_module.__PLUGIN__ = imported_module.__name__

        if not imported_module.__PLUGIN__.lower() in HELP_COMMANDS:
            if hasattr(imported_module, "__help__") and imported_module.__help__:
                HELP_COMMANDS[
                    imported_module.__PLUGIN__.lower()
                ] = imported_module.__help__
            else:
                continue
        else:
            raise Exception(
                "Can't have two plugins with the same name! Please change one",
            )

    return ", ".join(list(HELP_COMMANDS.keys()))