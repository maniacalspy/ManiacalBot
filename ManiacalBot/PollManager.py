import asyncio
import random
class PollManager(object):
    """Object that Manages running polls in the Twitch Chat"""
    def __init__(self, Time: int, Options: list):
        self._Time = Time
        self._Options = Options
        self._Votes = {}
        self.active = True
        self.__run_task = None


    async def HandleVote(self, ctx):
        voteoption = -1
        if self.active:
            voteoption = int(ctx.content)
            if voteoption > 0 and voteoption <= len(self._Options):
                self._Votes[ctx.author.name] = voteoption
                print(f"{ctx.author.name} voted for {self._Options[voteoption -1]} with code {voteoption}")
                print(f"{self._Votes[ctx.author.name]}")

    async def run(self):
        while self._Time > 0:
            await asyncio.sleep(1)
            self._Time -= 1        
        self.active = False
        print('test')


    async def GetResults(self):
        await self.__run_task
        VoteResults = list(self._Votes.values())
        print(VoteResults)
        winning_vote_id = -1
        winning_votes = []
        winning_vote_total = -1
        final_winner = "No votes were cast. Way to participate in democracy"
        for i in range(1,len(self._Options)+1):
            print(f"{i}: {VoteResults.count(i)}")
            votetotal = VoteResults.count(i)
            if votetotal > 0:
                if ( votetotal > VoteResults.count(winning_vote_id)): 
                    winning_vote_id = i
                    winning_vote_total = VoteResults.count(winning_vote_id)
                    winning_votes = [self._Options[i-1]]
                elif (votetotal  == VoteResults.count(winning_vote_id)): winning_votes.append(self._Options[i-1])
        if winning_vote_id > 0: 
            if (len(winning_votes) > 1):
                final_winner = random.choice(winning_votes)
            else: final_winner = winning_votes[0]

        return final_winner

    @staticmethod
    async def CreatePoll(Time: int, Options: list):
        PollObj = PollManager(Time, Options)
        eventloop = asyncio.get_event_loop()
        PollObj.__run_task = eventloop.create_task(PollObj.run())
        return PollObj