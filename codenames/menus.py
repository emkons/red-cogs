
import logging
import discord
from redbot.core import commands
from redbot.vendored.discord.ext import menus

from typing import List

from .game import CodenamesGame, GameState, Team

log = logging.getLogger(__name__)

try:
    from slashtags import Button, ButtonMenuMixin, ButtonStyle, Component, InteractionButton
except ImportError:
    pass

def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    from https://github.com/flaree/flare-cogs/blob/bf629ec6d8c28519bf08256b2f5132a216d1671e/commandstats/commandstats.py#L17
    """
    for i in range(0, len(l), n):
        yield l[i : i + n]

class CodenamesMenu(ButtonMenuMixin, menus.Menu):
    def __init__(self, game: CodenamesGame, color: discord.Color):
        self.game = game
        self.color = color
        self.num = 1
        self.message = None
        super().__init__(timeout=60, delete_message_after=False, clear_reactions_after=True)

    async def update(self, button):
            await button.defer_update()
            await super().update(button)

    async def send_initial_message(self, ctx: commands.Context, channel: discord.TextChannel):
        self.custom_id = str(ctx.message.id)
        return await self._send(ctx, embed=self.current_state_embed())

    async def edit(self, button, **kwargs):
        await button.update(embed=self.current_state_embed(), components=self._get_components())

    async def send(self, button, content: str = None, **kwargs):
        await button.send(content, **kwargs)

    async def edit_or_send(self, button, **kwargs):
        try:
            if button:
                await button.update(**kwargs)
            else:
                if kwargs.pop("components", None) == []:
                    await self._edit_message_components([])
                await self.message.edit(**kwargs)
        except discord.NotFound:
            await self.ctx.send(**kwargs)
        except discord.Forbidden:
            pass
    
    def _get_emoji(self, button: InteractionButton):
        emoji_string = button.custom_id[len(self.custom_id) + 1 :].split('-')[0]
        return menus._cast_emoji(emoji_string)

    def _get_lobby_buttons(self) -> List[Component]:
        return [
            Button(style=ButtonStyle(1), custom_id=f"{self.custom_id}-blueJoin", label="Join Blue", emoji=None),
            Button(style=ButtonStyle(1), custom_id=f"{self.custom_id}-blueSpy", label="Become Spymaster", emoji=None),
            Button(style=ButtonStyle(4), custom_id=f"{self.custom_id}-redJoin", label="Join Red", emoji=None),
            Button(style=ButtonStyle(4), custom_id=f"{self.custom_id}-redSpy", label="Become Spymaster", emoji=None),
            Button(style=ButtonStyle(3), custom_id=f"{self.custom_id}-begin", label="Start", emoji=None),
        ]
    
    def _get_game_buttons(self) -> List[Component]:
        components = []
        buttons = []
        self.game.revealed_words
        for word in self.game.words:
            buttons.append(Button(
                style=(ButtonStyle(2) if word not in self.game.revealed_words else 
                ButtonStyle(1) if word in self.game.team_words[Team.BLUE] else 
                ButtonStyle(4) if word in self.game.team_words[Team.RED] else ButtonStyle(2)),
                custom_id=f"{self.custom_id}-word-{word}",
                label=word,
                disabled=(True if word in self.game.revealed_words else False)
            ))
        
        for button_chunk in chunks(buttons, 5):
            components.append(Component(components=button_chunk))
        
        # components.append(Component(components=[
        #     Button(style=ButtonStyle(3), custom_id=f"{self.custom_id}-endTurn"),
        #     Button(style=ButtonStyle(3), custom_id=f"{self.custom_id}-spyShow")
        # ]))
        return components

    def _get_components(self) -> List[Component]:
        components = []
        log.error("Getting components. State: %s" % self.game.state)
        if self.game.state == GameState.LOBBY:
            components.append(Component(components=self._get_lobby_buttons()))
        elif self.game.state == GameState.PLAYING:
            components.extend(self._get_game_buttons())
        elif self.game.state == GameState.ENDED:
            components = []

        log.debug(components)
        return components

    @menus.button('blueJoin')
    async def blueJoin(self, payload: discord.RawReactionActionEvent):
        print('blueJoin')
        await self.send_current_state(payload)

    @menus.button('blueSpy')
    async def blueSpy(self, payload: discord.RawReactionActionEvent):
        print('blueSpy')
        await self.send_current_state(payload)

    @menus.button('redJoin')
    async def redJoin(self, payload: discord.RawReactionActionEvent):
        print('redJoin')
        await self.send_current_state(payload)

    @menus.button('redSpy')
    async def redSpy(self, payload: discord.RawReactionActionEvent):
        print('redSpy')
        await self.send_current_state(payload)

    @menus.button('begin')
    async def begin(self, payload: discord.RawReactionActionEvent):
        await self.game.begin_game()
        await self.send_current_state(payload)
    
    @menus.button('word')
    async def word(self, payload: discord.RawReactionActionEvent):
        word = payload.custom_id[len(self.custom_id) + 1 :].split('-')[1]
        await self.game.reveal(payload.author_id, word)
        await self.send_current_state(payload)

    async def send_current_state(self, payload):
        await self.edit(payload, embed=self.current_state_embed())

    def current_state_embed(self):
        if self.game.state == GameState.LOBBY:
            return self.lobby_embed()
        elif self.game.state == GameState.PLAYING:
            return self.game_embed()
        else:
            return self.ended_embed()

    def lobby_embed(self):
        e = discord.Embed(
            color=self.color,
            title=f"Codenames game",
            description="Join some team",
        )
        return e

    def game_embed(self):
        e = discord.Embed(
            color=self.color,
            title=f"Codenames game",
            description="Play the game",
        )
        return e
    
    def ended_embed(self):
        e = discord.Embed(
            color=self.color,
            title=f"Codenames game",
            description="Game ended",
        )
        return e

    async def finalize(self, timed_out: bool):
        if timed_out:
            await self.edit_or_send(
                None, content="Akinator game timed out.", embed=None, components=[]
            )



def get_menu():


    return CodenamesMenu