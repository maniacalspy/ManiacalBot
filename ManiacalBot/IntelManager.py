import asyncio
from dataclasses import dataclass
import MBSQLModule as SQL
CallID = 0

@dataclass
class IntelUser:
    id:int
    points:int

    def __init__(self, id:int = 0, points:int = 0, datatuple=None):
        if(datatuple is None):
            self.id = id
            self.points = points
        else:
            self.id = datatuple.id
            self.points = datatuple.points

@dataclass
class IntelPendingCall:
    userid:int
    callCost:int
    callID:int

    def __init__(self, id:int, cost:int, callid:int):
        self.userid = id
        self.callCost = cost
        self.callID = callid
@dataclass
class CommandFinishedResponse:
    User:str
    CallID:int

    def __init__(self, User:str, CallID:int):
        self.User = User
        self.CallID = CallID

def as_CommandFinishedResponse(dct):
    if 'JSONType' in dct:
        if dct['JSONType'] == "CommandFinished":
            return CommandFinishedResponse(dct['User'], dct['CallID'])
    return dct

def IntelCostFunction(cost, DelayCost = False):
    def wrap(f):
        #print("wrapping function with cost " + str(cost))
        def wrapper(*args,**kwargs):
            global CallID
            user = kwargs['username']
            id = kwargs['id']
            for group in IntelManager.Instance.Intel_Users:
                match = None
                matchList = [user for user in group if id == user.id]
                if len(matchList) > 0: match = matchList[0]
                if(match is not None):
                    pending_spent = IntelManager.Instance.Pending_Costs.get(str(match.id),0)
                    if(match.points - pending_spent >= cost):
                        CallID += 1
                        print(user + " does have enough, call the function with ID " + str(CallID))
                        if (not DelayCost): match.points -= cost
                        else:
                            if str(match.id) in IntelManager.Instance.Pending_Costs:
                                IntelManager.Instance.Pending_Costs[str(match.id)] += cost
                            else:
                                IntelManager.Instance.Pending_Costs[str(match.id)] = cost
                            Pending = IntelPendingCall(id = match.id, cost = cost, callid = CallID)
                            IntelManager.Instance.Pending_Calls[str(CallID)] = Pending
                        f(*args, **kwargs, Callid = CallID)
            #print("this is where we would check that " + user + " has " + str(cost) + " points")
                    else:
                        print("Oops, " + user + " needs more points, no funtion call")
        return wrapper
    return wrap

def innerLamTest(username, keyword):
    print(username + " has decided they want " + keyword)


class IntelManager(object):
    """description of class"""
    Instance = None
    def __init__(self):
        self.Intel_Users = [[],[],[],[],[]]
        self.Pending_Costs = {}
        self.Pending_Calls = {}
        self.currentIntelGroupIndex = 0
        self.IntelGroupMax = 5
        self.IntelTimer = 60
        self.Enlisted_Users = []
        IntelManager.Instance = self

    async def ResolvePendingCall(self, callID):
        call = self.Pending_Calls[str(callID)]
        IntelUserData = None
        if (call is not None):
            try:
                for group in self.Intel_Users:
                    match = None
                    matchList = [user for user in group if user.id == call.userid]
                    if len(matchList) > 0: match = matchList[0]
                    if(match is not None): IntelUserData = match
            except:
                pass
            if (IntelUserData is not None):
                IntelUserData.points -= call.callCost

    async def EnlistIntelUser(self, id):
        IntelData = IntelUser(datatuple=await SQL.GetIntelUser(id))
        bSuccessfullyEnlisted = False
        if (IntelData.id == 0):
            bIsNewlyEnlisted = False
            for newlyEnlisted in self.Enlisted_Users:
                match = None
                matchList = [user for user in newlyEnlisted if id == user.id]
                if len(matchList) > 0: match = matchList[0]
                if(match is not None): bIsNewlyEnlisted = True
            if not bIsNewlyEnlisted:
                TargetIndex = self.currentIntelGroupIndex-1 if self.currentIntelGroupIndex-1 >=0 else self.IntelGroupMax-1
                newuser = IntelUser(id, 100)
                self.Enlisted_Users.append(newuser)
                self.Intel_Users[TargetIndex].append(newuser)
                bSuccessfullyEnlisted = True
                #await ctx.send(f'@{ctx.author.name} welcome to the intelligence program! You\'ll now earn intel points as you watch the stream, use !intel to track your points')
        #if not bSuccessfullyEnlisted:
            #await ctx.send(f'@{ctx.author.name} we were unable to enlist you, it\'s likely you have already enlisted in the intelligence program')
        return bSuccessfullyEnlisted


    async def AddEnlistedUsers(self):
        await SQL.EnlistUsers(*self.Enlisted_Users)
        self.Enlisted_Users = []


    async def IntelCommand(self, id):
        IntelUserData = None
        try:
            for group in self.Intel_Users:
                match = None
                matchList = [user for user in group if user.id == id]
                if len(matchList) > 0: match = matchList[0]
                if(match is not None): IntelUserData = match
        except:
            pass
        if (IntelUserData is not None):
            #await ctx.send(f'@{ctx.author.name} you have {IntelUserData.points} intel')
            return IntelUserData.points
        else:
            User = IntelUser(datatuple=await SQL.GetIntelUser(id))
            if(User is not None and User.id != 0):
                await self.ActivateIntelUser(User)
                return User.points
            else:
                return -1

    async def ActivateIntelUser(self, user:IntelUser):
        if (user is not None):
            if(not await self.IntelUserActivated(user.id)):
                TargetIndex = self.currentIntelGroupIndex-1 if self.currentIntelGroupIndex-1 >=0 else self.IntelGroupMax-1
                self.Intel_Users[TargetIndex].append(user)

    async def DeactivateIntelUser(self, id:int):
        if(await self.IntelUserActivated(id=id)):
            for group in self.Intel_Users:
                match = None
                matchList = [user for user in group if user.id == id]
                if len(matchList) > 0: 
                    match = matchList[0]
                    if(match is not None):
                        await SQL.UpdateIntelUsers(userdata=[match])
                        group.remove(match)

    async def IntelUserActivated(self, id:int):
        try:
            for group in self.Intel_Users:
                match = None
                matchList = [user for user in group if id == user.id]
                if len(matchList) > 0: match = matchList[0]
                if(match is not None): return True
        except:
            pass
        else: return False

    async def AwardIntel(self):
        while True:
            for user in self.Intel_Users[self.currentIntelGroupIndex]:
                user.points +=5
            self.currentIntelGroupIndex += 1
            if self.currentIntelGroupIndex > self.IntelGroupMax-1: self.currentIntelGroupIndex = 0
            await asyncio.sleep(self.IntelTimer)
    

    async def IntelSQLUpdate(self):
        flat_intel_list = []
        for group in self.Intel_Users:
            for user in group:
                flat_intel_list.append(user)
        
        await SQL.UpdateIntelUsers(userdata=flat_intel_list)