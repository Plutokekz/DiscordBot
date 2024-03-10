import os

from dotenv import load_dotenv

from bot.cogs.shared.schemas import Config


def load_config():
    load_dotenv()
    return Config(**os.environ)


loaded = False
config = None

if not loaded:
    config = load_config()
    loaded = True
