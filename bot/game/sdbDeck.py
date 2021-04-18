import json
# from urllib import request
import random
from abc import ABC, abstractmethod
from typing import List, Dict
from discord import Message
from datetime import datetime
import os
import traceback

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from .. import lib
from .. import botState
from ..cfg import cfg
from ..cardRenderer import make_cards


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name(cfg.paths.googleAPICred, scope)
gspread_client = gspread.authorize(creds)

def collect_cards(sheetLink):
    global gspread_client

    worksheet = gspread_client.open_by_url(sheetLink)
    expansions = {}

    for expansion in worksheet.worksheets():
        expansions[expansion.title] = {"white": list(set(card for card in expansion.col_values(1) if card)),
                                        "black": list(set(card for card in expansion.col_values(2) if card))}

    return {"expansions": expansions, "title": worksheet.title}


class SDBCard(ABC):
    def __init__(self, text, url, expansion: "SDBExpansion"):
        self.url = url
        self.text = text
        self.expansion = expansion

    def __str__(self):
        return self.url


class BlackCard(SDBCard):
    def __init__(self, text, url, requiredWhiteCards, expansion):
        super().__init__(text, url, expansion)
        self.requiredWhiteCards = requiredWhiteCards


class WhiteCard(SDBCard):
    def __init__(self, text, url, expansion):
        super().__init__(text, url, expansion)
        self.owner = None

    def isOwned(self):
        return self.owner is not None

    def claim(self, player):
        if self.isOwned():
            botState.logger.log("WhiteCard", "claim",
                                "Player " + self.player.dcUser.name + "#" + str(self.player.dcUser.id) + " Attempted to claim a card that is already owned: " + self.text,
                                eventType="ALREADY_OWNED", trace=traceback.format_exc())
        else:
            self.owner = player
            self.expansion.ownedWhiteCards += 1

    def revoke(self):
        if not self.isOwned():
            botState.logger.log("WhiteCard", "revoke",
                                "Player " + self.player.dcUser.name + "#" + str(self.player.dcUser.id) + " Attempted to revoke a card that is not owned: " + self.text,
                                eventType="NOT_OWNED", trace=traceback.format_exc())
        else:
            self.owner = None
            self.expansion.ownedWhiteCards -= 1


class SDBExpansion:
    def __init__(self):
        self.white = []
        self.black = []
        self.ownedWhiteCards = 0

    def allOwned(self):
        return self.ownedWhiteCards == len(self.white)

    def emptyBoth(self):
        self.white = []
        self.black = []
        self.ownedWhiteCards = 0

    def emptyWhite(self):
        self.white = []

    def emptyBlack(self):
        self.black = []

    def whiteIsEmpty(self):
        return self.white == []

    def blackIsEmpty(self):
        return self.black == []


class SDBDeck:
    def __init__(self, metaPath: str):
        # deckMeta = json.load(request.urlopen(metaUrl))
        deckMeta = lib.jsonHandler.readJSON(metaPath)

        if "expansions" not in deckMeta or deckMeta["expansions"] == {}:
            raise RuntimeError("Attempted to create an empty SDBDeck")

        self.expansionNames: List[str] = list(deckMeta["expansions"].keys())
        self.unseenCards: Dict[str, SDBExpansion] = {expansion : SDBExpansion() for expansion in self.expansionNames}
        self.seenCards: Dict[str, SDBExpansion] = {expansion : SDBExpansion() for expansion in self.expansionNames}
        self.name: str = deckMeta["deck_name"]
        hasWhiteCards: bool = False
        hasBlackCards: bool = False

        for expansion in self.expansionNames:
            if "white" in deckMeta["expansions"][expansion]:
                for cardData in deckMeta["expansions"][expansion]["white"]:
                    self.unseenCards[expansion].white.append(WhiteCard(cardData["text"], cardData["url"], self.unseenCards[expansion]))
            if "black" in deckMeta["expansions"][expansion]:
                for cardData in deckMeta["expansions"][expansion]["black"]:
                    self.unseenCards[expansion].black.append(BlackCard(cardData["text"], cardData["url"], cardData["requiredWhiteCards"], self.unseenCards[expansion]))

            if not hasWhiteCards:
                hasWhiteCards = len(self.unseenCards[expansion].white) != 0
            if not hasBlackCards:
                hasBlackCards = len(self.unseenCards[expansion].black) != 0

        if not hasWhiteCards:
            raise RuntimeError("Attempted to create a deck with no white cards")
        elif not hasBlackCards:
            raise RuntimeError("Attempted to create a deck with no black cards")

        self.emptyBlack: BlackCard = BlackCard("EMPTY", deckMeta["black_back"] if "black_back" in deckMeta else cfg.emptyBlackCard, 0, list(self.unseenCards.values())[0])
        self.emptyWhite: WhiteCard = WhiteCard("EMPTY", deckMeta["white_back"] if "white_back" in deckMeta else cfg.emptyWhiteCard, list(self.unseenCards.values())[0])


    def popRandomWhite(self, expansions=[]):
        if expansions == []:
            expansions = self.expansionNames

        if False not in (self.unseenCards[expansion].whiteIsEmpty() for expansion in expansions):
            if False in (self.seenCards[expansion].whiteIsEmpty() for expansion in expansions):
                for expansion in self.expansionNames:
                    self.unseenCards[expansion].white = self.seenCards[expansion].white
                    self.seenCards[expansion].emptyWhite()
                self.unseenCards[expansion].ownedWhiteCards = self.seenCards[expansion].ownedWhiteCards
                self.seenCards[expansion].ownedWhiteCards = 0
            else:
                raise ValueError("No white cards in any of the given expansions, and no seen cards available for swap: " + ", ".join(expansions))
        
        noFreeCards = True
        for expansion in expansions:
            if not self.unseenCards[expansion].allOwned():
                noFreeCards = False
                break
        if noFreeCards:
            botState.logger.log("SDBDeck", "popRandomWhite",
                                "All white cards are already owned in the given expansions: " + ", ".join(expansions),
                                eventType="ALL_OWNED", trace=traceback.traceback.format_exc())
            return None

        expansion = random.choice(expansions)
        while len(self.unseenCards[expansion].white) == 0 or self.unseenCards[expansion].allOwned():
            expansion = random.choice(expansions)

        card: WhiteCard = random.choice(self.unseenCards[expansion].white)
        while card.isOwned():
            card = random.choice(self.unseenCards[expansion].white)

        card.expansion.ownedWhiteCards -= 1
        card.expansion = self.seenCards[expansion]
        card.expansion.ownedWhiteCards += 1
        self.unseenCards[expansion].white.remove(card)
        self.seenCards[expansion].white.append(card)

        return card
    

    def randomBlack(self, expansions=[]):
        if expansions == []:
            expansions = self.expansionNames
        
        if False not in (self.unseenCards[expansion].blackIsEmpty() for expansion in expansions):
            if False in (self.seenCards[expansion].blackIsEmpty() for expansion in expansions):
                for expansion in self.expansionNames:
                    self.unseenCards[expansion].black = self.seenCards[expansion].black
                    self.seenCards[expansion].emptyBlack()
            else:
                raise ValueError("No black cards in any of the given expansions, and no seen cards available for swap: " + ", ".join(expansions))

        expansion = random.choice(expansions)
        while len(self.unseenCards[expansion].black) == 0:
            expansion = random.choice(expansions)

        card = random.choice(self.unseenCards[expansion].black)
        card.expansion = self.seenCards[expansion]
        self.unseenCards[expansion].black.remove(card)
        self.seenCards[expansion].black.append(card)

        return card


async def updateDeck(callingMsg: Message, bGuild, deckName: str):
    loadingMsg = await callingMsg.reply("Reading spreadsheet... " + cfg.defaultEmojis.loading.sendable)

    try:
        newCardData = collect_cards(bGuild.decks[deckName]["spreadsheet_url"])
        await loadingMsg.edit(content="Reading spreadsheet... " + cfg.defaultEmojis.submit.sendable)
    except gspread.SpreadsheetNotFound:
        await callingMsg.reply(":x: Unrecognised spreadsheet! Please make sure the file exists and is public.")
        bGuild.decks[deckName]["updating"] = False
        return
    else:
        lowerExpansions = [expansion.lower() for expansion in newCardData["expansions"]]
        for expansion in lowerExpansions:
            if lowerExpansions.count(expansion) > 1:
                await callingMsg.reply(":x: Deck update failed - duplicate expansion pack name found: " + expansion)
                bGuild.decks[deckName]["updating"] = False
                return
        
        unnamedFound = False
        emptyExpansions = []
        for expansion in newCardData["expansions"]:
            if expansion == "":
                unnamedFound = True
            if len(newCardData["expansions"][expansion]["white"]) == 0 and len(newCardData["expansions"][expansion]["black"]) == 0:
                emptyExpansions.append(expansion)

        errs = ""
        
        if unnamedFound:
            errs += "\nUnnamed expansion pack detected - skipping this expansion."
            del newCardData["expansions"][""]

        if len(emptyExpansions) != 0:
            errs += "\nEmpty expansion packs detected - skipping these expansions: " + ", ".join(expansion for expansion in emptyExpansions)
            for expansion in emptyExpansions:
                del newCardData["expansions"][expansion]

        whiteCounts = {}
        blackCounts = {}
        for expansion in newCardData["expansions"]:
            whiteCounts[expansion] = len(newCardData["expansions"][expansion]["white"])
            blackCounts[expansion] = len(newCardData["expansions"][expansion]["black"])
            indicesToRemove = []
            for cardNum, cardText in enumerate(newCardData["expansions"][expansion]["black"]):
                if "_" not in cardText:
                    indicesToRemove.append(cardNum)
            if indicesToRemove:
                errs += "\nIgnoring " + str(len(indicesToRemove)) + " black cards from " + expansion + " expansion with no white card slots (`_`)."
                for i in indicesToRemove:
                    newCardData["expansions"][expansion]["black"].pop(i)

        if errs != "":
            await callingMsg.channel.send(errs)

        totalWhite = sum(whiteCounts.values())
        totalBlack = sum(blackCounts.values())
        
        if int(totalWhite / cfg.cardsPerHand) < 2:
            await callingMsg.reply("Deck update failed.\nDecks must have at least " + str(2 * cfg.cardsPerHand) + " white cards.")
            bGuild.decks[deckName]["updating"] = False
            return
        if totalBlack == 0:
            await callingMsg.reply("Deck update failed.\nDecks must have at least 1 black card.")
            bGuild.decks[deckName]["updating"] = False
            return

        oldCardData = lib.jsonHandler.readJSON(bGuild.decks[deckName]["meta_path"])
        deckID = os.path.splitext(os.path.split(bGuild.decks[deckName]["meta_path"])[1])[0]

        cardStorageChannel = None if cfg.cardStorageMethod == "local" else botState.client.get_guild(cfg.cardsDCChannel["guild_id"]).get_channel(cfg.cardsDCChannel["channel_id"])

        loadingMsg = await callingMsg.channel.send("Updating deck... " + cfg.defaultEmojis.loading.sendable)
        results = await make_cards.update_deck(cfg.paths.decksFolder, oldCardData, newCardData, deckID, cfg.paths.cardFont, callingMsg.guild.id, emptyExpansions, cfg.cardStorageMethod, cardStorageChannel, callingMsg, contentFontSize=cfg.cardContentFontSize, titleFontSize=cfg.cardTitleFontSize)
        oldCardData, changeLog = results[0], results[1]

        await loadingMsg.edit(content="Updating deck... " + cfg.defaultEmojis.submit.sendable)
        
        lib.jsonHandler.writeJSON(bGuild.decks[deckName]["meta_path"], oldCardData)
        now = datetime.utcnow()
        bGuild.decks[deckName]["last_update"] = now.timestamp()
        bGuild.decks[deckName]["expansions"] = {expansion: (whiteCounts[expansion], blackCounts[expansion]) for expansion in whiteCounts}
        bGuild.decks[deckName]["white_count"] = totalWhite
        bGuild.decks[deckName]["black_count"] = totalBlack

        bGuild.decks[deckName]["updating"] = False
        if changeLog == "":
            await callingMsg.reply("Update complete, no changes found!")
        else:
            await callingMsg.reply("Update complete!\n" + changeLog)
