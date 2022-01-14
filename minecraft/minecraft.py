import base64
import logging
import discord
from asyncio import TimeoutError as AsyncTimeoutError
from io import BytesIO

from mcstatus import MinecraftServer

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as chat

class Minecraft(commands.Cog):

    __version__ = "0.0.1"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    @commands.group()
    async def minecraft(self, ctx):
        """Get Minecraft-Related data"""
        pass

    @minecraft.command(usage="<server IP>[:port]")
    @commands.bot_has_permissions(embed_links=True)
    @commands.admin()
    async def server(self, ctx, server_ip: str):
        """Get info about server"""
        try:
            server: MinecraftServer = await self.bot.loop.run_in_executor(
                None, MinecraftServer.lookup, server_ip
            )
        except Exception as e:
            await ctx.send(chat.error("Unable to resolve IP: {}".format(e)))
            return
        async with ctx.channel.typing():
            try:
                status = await server.async_status()
            except OSError as e:
                await ctx.send(chat.error("Unable to get server's status: {}".format(e)))
                return
            except AsyncTimeoutError:
                await ctx.send(chat.error("Unable to get server's status: Timed out"))
                return
        icon_file = None
        icon = (
            discord.File(
                icon_file := BytesIO(base64.b64decode(status.favicon.split(",", 1)[1])),
                filename="icon.png",
            )
            if status.favicon
            else None
        )
        embed = discord.Embed(
            title=f"{server.host}:{server.port}",
            description=chat.box(await self.clear_mcformatting(status.description)),
            color=await ctx.embed_color(),
        )
        if icon:
            embed.set_thumbnail(url="attachment://icon.png")
        embed.add_field(name=_("Latency"), value=f"{status.latency} ms")
        embed.add_field(
            name=_("Players"),
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
        )
        embed.add_field(
            name="Version",
            value="{}\nProtocol: {}".format(status.version.name, status.version.protocol),
        )
        await ctx.send(file=icon, embed=embed)
        if icon_file:
            icon_file.close()
        # TODO: for some reason, producing `OSError: [WinError 10038]` on current version of lib
        # not tested further
        # if query_data:  # Optional[bool]
        #     try:
        #         query = await server.async_query()
        #     except OSError as e:
        #         embed.set_footer(text=chat.error(_("Unable to get query data: {}").format(e)))
        #         await msg.edit(embed=embed)
        #         return
        #     except AsyncTimeoutError:
        #         embed.set_footer(text=chat.error(_("Unable to get query data: Timed out.")))
        #         await msg.edit(embed=embed)
        #         return
        #     embed.add_field(name=_("World"), value=f"{query.map}")
        #     embed.add_field(
        #         name=_("Software"),
        #         value=_("{}\nVersion: {}").format(query.software.brand, query.software.version)
        #         # f"Plugins: {query.software.plugins}"
        #     )
        #     await msg.edit(embed=embed)