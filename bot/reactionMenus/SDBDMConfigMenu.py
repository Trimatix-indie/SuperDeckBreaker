from bot import botState
from . import reactionMenu, pagedReactionMenu
from discord import Message, Member, Role, Embed, User
from typing import Dict, Union
from .. import lib
from ..scheduling import timedTask
from ..users import basedUser
from ..game import sdbGame
import random
from ..cfg import cfg


class SDBDMConfigMenu(pagedReactionMenu.PagedReactionMenu):
    def __init__(self, msg: Message, game: "sdbGame.SDBGame"):
        self.game = game
        self.paused = False
        pageOneEmbed = Embed()
        pages = {pageOneEmbed: {}}
        pageOneEmbed.title = "Deck Master Admin Menu"
        ownerEmoji = lib.emojis.BasedEmoji(unicode="👑")
        pageOneEmbed.add_field(name=ownerEmoji.sendable + " : Relinquish Deck Master", value="Hand game ownership to another user.")
        pages[pageOneEmbed][ownerEmoji] = reactionMenu.NonSaveableReactionMenuOption("Relinquish Deck Master", ownerEmoji, addFunc=self.reliquishOwner)
        super().__init__(msg, pages=pages, targetMember=game.owner)


    async def reactionAdded(self, emoji: lib.emojis.BasedEmoji, member: Union[Member, User]):
        if not self.paused:
            return await super().reactionAdded(emoji, member)


    async def reactionRemoved(self, emoji: lib.emojis.BasedEmoji, member: Union[Member, User]):
        if not self.paused:
            return await super().reactionRemoved(emoji, member)


    async def pauseMenu(self):
        self.paused = True
        self.currentPage.set_footer(text="[menu paused]")
        await self.updateMessage(noRefreshOptions=True)


    async def unpauseMenu(self):
        self.paused = False
        self.currentPage.set_footer(text=Embed.Empty)
        await self.updateMessage(noRefreshOptions=True)


    async def reliquishOwner(self):
        await self.pauseMenu()
        playerPickerMsg = await lib.discordUtil.sendDM("​", self.game.owner, self.msg, reactOnDM=False)
        newOwner = None
        if playerPickerMsg is not None:
            pages = pagedReactionMenu.makeTemplatePagedMenuPages({str(player.dcUser): player.dcUser for player in self.game.players if player.dcUser != self.game.owner})
            for pageEmbed in pages:
                randomPlayerOption = pagedReactionMenu.NonSaveableValuedMenuOption("Pick Random Player", cfg.defaultEmojis.spiral, None)
                pages[pageEmbed][cfg.defaultEmojis.spiral] = randomPlayerOption
                pageEmbed.add_field(name=cfg.defaultEmojis.spiral.sendable + " : Pick Random Player", value="​", inline=False)
                pageEmbed.title = "New Deck Master"
                pageEmbed.description = "Who should be the new deck master?"
                pageEmbed.set_footer(text="This menu will expire in " + str(cfg.timeouts.sdbPlayerSelectorSeconds) + "s")

            allOptions = []
            for page in pages.values():
                allOptions += [option for option in page.values()]

            try:
                playerSelection = await pagedReactionMenu.InlinePagedReactionMenu(playerPickerMsg, cfg.timeouts.sdbPlayerSelectorSeconds, pages=pages, targetMember=self.game.owner, noCancel=True, returnTriggers=allOptions).doMenu()
            except pagedReactionMenu.InvalidClosingReaction as e:
                await self.game.channel.send("An unexpected error occurred when picking the new deck master.\nPicking one at random...")
                botState.logger.log("SDBDMConfigMenu", "relinquishOwner", "Invalid closing reaction: " + e.emoji.sendable, category="reactionMenus", eventType="InvalidClosingReaction")
            else:
                if playerSelection != [] and playerSelection[0] != cfg.defaultEmojis.spiral: 
                    newOwner = playerSelection[0].value
            
            await playerPickerMsg.delete()
        else:
            await self.game.channel.send(self.owner.mention + " Player selection menu failed to send! Are your DMs open?\nPicking a new deck master at random...")
        
        if newOwner is None:
            newOwner = random.choice(self.game.players).dcUser
            while newOwner == self.game.owner:
                print("random picking")
                newOwner = random.choice(self.game.players).dcUser

        await self.game.setOwner(newOwner)
