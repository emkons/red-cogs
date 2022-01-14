import re
import base64
import logging
import datetime
import discord
import asyncio
from asyncio import TimeoutError as AsyncTimeoutError
from io import BytesIO

from mcstatus import MinecraftServer

from redbot.core import commands
from redbot.core.config import Config
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as chat

log = logging.getLogger("red.emkons.minecraft")

class Minecraft(commands.Cog):

    __version__ = "0.0.1"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, identifier=0xd3eeeabdcf06d6744c5bc496fa26fd65)
        self.config.register_guild(channel = None, message=None, server_ip = None)
        self.loop = self.bot.loop.create_task(self.update_loop())

    async def update_loop(self):
        await self.bot.wait_until_ready()
        while True:
            await asyncio.sleep(datetime.timedelta(minutes=1).total_seconds())
            await self.update_loop()

    @commands.group()
    async def minecraft(self, ctx):
        """Get Minecraft-Related data"""
        pass

    async def message_updater(self):
        data = await self.config.all_guilds()
        for guild_id in data:
            try:
                guild = self.bot.get_guild(int(guild_id)) # type: discord.Guild
                if guild is None:
                    log.debug("Guild %d not found", guild)
                    continue
                channel = guild.get_channel(data[guild_id]['channel']) # type: discord.TextChannel
                if channel is None:
                    log.debug("Channel %d not found", channel)
                    continue
                message = channel.fetch_message(data[guild_id]['message']) # type: discord.Message
                if message is None:
                    log.debug("Message %d not found", message)
                    continue
                server_ip = data[guild_id]['server_ip']
                if server_ip is None:
                    log.debug("Server ip npt set")
                    continue
                embed = await self.create_embed(server_ip)
                await message.edit(embed=embed)
            except Exception as e:
                log.exception(e)
        pass

    @minecraft.command(usage="<server IP>[:port]")
    @commands.bot_has_permissions(embed_links=True)
    @commands.admin()
    async def server(self, ctx, server_ip: str):
        """Get info about server"""
        embed = await self.create_embed(server_ip)
        message = await ctx.send(embed=embed) # type: discord.Message
        await self.config.guild(ctx.guild).message.set(message.id)
        await self.config.guild(ctx.guild).channel.set(message.channel.id)
        await self.config.guild(ctx.guild).server_ip.set(server_ip)

    async def create_embed(self, server_ip):
        error_embed = discord.Embed(
            title="",
            color=discord.Colour(0x00ff00)
        )
        try:
            server: MinecraftServer = await self.bot.loop.run_in_executor(
                None, MinecraftServer.lookup, server_ip
            )
        except Exception as e:
            # await ctx.send(chat.error("Unable to resolve IP: {}".format(e)))
            error_embed.title = "Unable to resolve IP: {}".format(e)
            return error_embed
        # async with ctx.channel.typing():
        try:
            status = await server.async_status()    
        except OSError as e:
            # await ctx.send(chat.error("Unable to get server's status: {}".format(e)))
            error_embed.title = "Unable to get server's status: {}".format(e)
            return error_embed
        except AsyncTimeoutError:
            # await ctx.send(chat.error("Unable to get server's status: Timed out"))
            error_embed.title = "Unable to get server's status: Timed out"
            return error_embed
        
        embed = discord.Embed(
            title=f"{server.host}:{server.port}",
            description=chat.box(await self.clear_mcformatting(status.description)),
            color=discord.Colour(0x00ff00),
        )
        embed.add_field(name="Latency", value=f"{status.latency} ms")
        embed.add_field(
            name="Version",
            value="{}\nProtocol: {}".format(status.version.name, status.version.protocol),
        )
        embed.add_field(
            name="Players",
            value="{0.players.online}/{0.players.max}\n{1}".format(
                status,
                chat.box(
                    list(
                        chat.pagify(
                            await self.clear_mcformatting(
                                "\n".join([p.name for p in status.players.sample])
                            ),
                            page_length=992,
                        )
                    )[0]
                )
                if status.players.sample
                else "",
            ),
            inline=False
        )
        return embed

    async def clear_mcformatting(self, formatted_str) -> str:
        """Remove Minecraft-formatting"""
        if not isinstance(formatted_str, dict):
            return re.sub(r"\xA7[0-9A-FK-OR]", "", formatted_str, flags=re.IGNORECASE)
        clean = ""
        async for text in self.gen_dict_extract("text", formatted_str):
            clean += text
        return re.sub(r"\xA7[0-9A-FK-OR]", "", clean, flags=re.IGNORECASE)
    
    async def gen_dict_extract(self, key: str, var: dict):
        if not hasattr(var, "items"):
            return
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                async for result in self.gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    async for result in self.gen_dict_extract(key, d):
                        yield result