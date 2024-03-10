import os

from dotenv import load_dotenv

from bot.cogs.shared.schemas import Config


def load_config():
    load_dotenv()
    return Config(**os.environ)


LOADED = False
config = None  # pylint: disable=invalid-name

if not LOADED:
    config = load_config()
    LOADED = True
