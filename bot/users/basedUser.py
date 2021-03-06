# Typing imports
from __future__ import annotations

from ..baseClasses import serializable


class BasedUser(serializable.Serializable):
    """A user of the bot. There is currently no guarantee that user still shares any guilds with the bot,
    though this is planned to change in the future.

    :var id: The user's unique ID. The same as their unique discord ID.
    :vartype id: int
    """

    def __init__(self, id: int, roundWins : int = 0, gameWins : int = 0, pollOwned : bool = False):
        """
        :param int id: The user's unique ID. The same as their unique discord ID.
        """
        self.id = id
        # Not parameterised as help menus are not currently saveable
        self.helpMenuOwned = False
        self.roundWins = roundWins
        self.gameWins = gameWins
        self.pollOwned = pollOwned


    def resetUser(self):
        """Reset the user's attributes back to their default values.
        """
        pass


    def getStatByName(self, stat: str):
        if stat == "round wins":
            return self.roundWins
        elif stat == "game wins":
            return self.gameWins
        else:
            raise ValueError("unknown stat: " + str(stat))


    def toDict(self, **kwargs) -> dict:
        """Serialize this BasedUser to a dictionary representation for saving to file.

        :return: A dictionary containing all information needed to recreate this user
        :rtype: dict
        """
        return {"roundWins": self.roundWins, "gameWins": self.gameWins, "pollOwned": self.pollOwned}


    def __str__(self) -> str:
        """Get a short string summary of this BasedUser. Currently only contains the user ID and home guild ID.

        :return: A string summar of the user, containing the user ID and home guild ID.
        :rtype: str
        """
        return "<BasedUser #" + str(self.id) + ">"


    @classmethod
    def fromDict(cls, userDict: dict, **kwargs) -> BasedUser:
        """Construct a new BasedUser object from the given ID and the information in the
        given dictionary - The opposite of BasedUser.toDict

        :param int id: The discord ID of the user
        :param dict userDict: A dictionary containing all information necessary to construct
                                the BasedUser object, other than their ID.
        :return: A BasedUser object as described in userDict
        :rtype: BasedUser 
        """
        if "id" not in kwargs:
            raise NameError("Required kwarg not given: id")
        userID = kwargs["id"]

        return BasedUser(userID, roundWins=userDict["roundWins"] if "roundWins" in userDict else 0,
                            gameWins=userDict["gameWins"] if "gameWins" in userDict else 0,
                            pollOwned=userDict["pollOwned"] if "pollOwned" in userDict else False)
