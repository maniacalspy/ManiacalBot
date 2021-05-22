import asyncio

class PollManager(object):
    """Object that Manages running polls in the Twitch Chat"""
    _Time = 0
    active = False
    _Options = []
    _Votes = {}

    async def __init__(self, Time: int, Options: list):
        self._Time = Time
        self._Optionss = Options
        self.active = True

    async def HanldeVote(self, ctx):
        voteoption = -1
        if self.active:
            voteoption = int(ctx.message)
            if voteoption > 0 and voteoption < len(options):
                self._Votess[ctx.author] = voteoption

    async def run(self):
        while self._Time > 0:
            await asyncio.sleep(1)
            self._Time -= 1

        self.active = False


    async def GetResults(self):
        while(self.active):
            continue
        VoteResults = list(self._Votes.values())
        winningvote = -1
        for i in range(1,len(options)+1):
            if (VoteResults.count(i) > winningvote): winningvote = i
        return self._Options[winningvote -1]

    @staticmethod
    async def CreatePoll(Time: int, Options: list):
        PollObj = await PollManager(Time, Options)
        eventloop = asyncio.get_event_loop()
        eventloop.create_task(PollObj.run())
        return PollObj