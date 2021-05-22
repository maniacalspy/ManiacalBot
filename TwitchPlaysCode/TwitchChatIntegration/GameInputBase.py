from abc import ABC, abstractmethod

class GameInputBase(ABC):
    """This is the base handler for game inputs, this class holds a reference to an input handler object.
    This is what handles the game keywords and then sends the input to the input handler"""
    @abstractmethod
    def HandleKeyword(keyword):
        pass

    @abstractmethod
    async def GetKeywords():
        pass



