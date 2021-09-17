import logging
import discord

from redbot.core import commands
from redbot.core.bot import Red

from .game import CodenamesGame
from .menus import get_menu

class Codenames(commands.Cog):
    """A game of codenames"""

    __version__ = "0.0.1"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    @commands.command()
    async def codenames(self, ctx: commands.Context):
        """This does stuff!"""

        # Start typing indicator to let users know that we are processing the message
        await ctx.trigger_typing()

        codenames = CodenamesGame()

        await codenames.start_game()
        menu = get_menu()
        codenames_color = discord.Color(0xE8BC90)
        await menu(codenames, codenames_color).start(ctx)