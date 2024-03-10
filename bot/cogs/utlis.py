import functools
from typing import List

import discord
from discord.ext import commands


def check_roles(ctx: commands.Context, roles: List[str]):
    getter = functools.partial(discord.utils.get, ctx.author.roles)
    if any(
        (
            getter(id=item) is not None
            if isinstance(item, int)
            else getter(name=item) is not None
        )
        for item in roles
    ):
        return True
    return False
