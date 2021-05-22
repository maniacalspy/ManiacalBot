import sys, os, importlib
import asyncio
from twitchio.ext  import commands
#https://twitchio.readthedocs.io/en/latest/

import random
from itertools import chain
from collections import namedtuple
from datetime import datetime, timedelta
import pytz
from dateutil import parser, relativedelta
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass

import MBSQLModule as SQL

#THIS IS FOR THE TTYD GAME INTEGRATION, IT ADDS THE FOLLOWING FOLDER TO THE PATH FOR IMPORTING FILES
sys.path.insert(0, 'C:/Users/Nolan/Desktop/ManiacalBot/TwitchPlaysCode/TwitchChatIntegration')

import ChatControlHandler
import PollManager

ChannelInfo = namedtuple('ChannelInfo', ('broadcaster_language', 'broadcaster_login', 'display_name', 'game_id', 'game_name', 'id', 'is_live', 'tag_ids', 'thumbnail_url', 'title', 'started_at'))

import time
import threading

from functools import wraps

#This next block of code was taken from https://gist.github.com/gregburek/1441055 and is not owned by me
def rate_limited(seconds_to_wait, mode='wait', delay_first_call=False):
    """
    Decorator that make functions not be called faster than

    set mode to 'kill' to just ignore requests that are faster than the 
    rate.

    set delay_first_call to True to delay the first call as well
    """
    lock = threading.Lock()
    min_interval = float(seconds_to_wait)
    def decorate(func):
        last_time_called = [0.0]
        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            def run_func():
                lock.release()
                ret = func(*args, **kwargs)
                last_time_called[0] = time.perf_counter()
                return ret
            lock.acquire()
            elapsed = time.perf_counter() - last_time_called[0]
            left_to_wait = min_interval - elapsed
            if delay_first_call:    
                if left_to_wait > 0:
                    if mode == 'wait':
                        time.sleep(left_to_wait)
                        return run_func()
                    elif mode == 'kill':
                        lock.release()
                        return
                else:
                    return run_func()
            else:
                # Allows the first call to not have to wait
                if not last_time_called[0] or elapsed > min_interval:   
                    return run_func()       
                elif left_to_wait > 0:
                    if mode == 'wait':
                        time.sleep(left_to_wait)
                        return run_func()
                    elif mode == 'kill':
                        lock.release()
                        return
        return rate_limited_function
    return decorate



@dataclass
class CountingCommand:
    name:str
    text:str
    count:int

    def __init__(self, name:str, text:str, count:int=0):
        self.name = name
        self.text = text
        self.count = count
    
    @rate_limited(5, 'kill')
    def GetCommandText(self):
        self.count += 1
        return self.text.replace('~', str(self.count))

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


import ctypes




KeycodeGames = {"TTYD", "Pokemon", "Valheim"}

#The input method used for the chat integration, such as using the KeyCodeInput class
Input = None
#Module Dynamically loaded to handle the game input data such as which keywords to use
GameInputData = None

class ManiacalBot(commands.Bot):
    
    PollMan = None
    ChatHandler = None
    Intel_Users = [[],[],[],[],[]]
    currentIntelGroupIndex = 0
    IntelGroupMax = 5
    IntelTimer = 60
    Enlisted_Users = []
    chat_data = {}
    tempcommands = {}
    countcommands = {}
    delcounters = set()
    deletedCommands = set()
    channeldata = {}

    #region PeriodicMessages
    messageTimer = 600
    periodicMessages = [
        "Did Spy say something funny out of context? use the !addquote command to add the Quote",
        "Enjoying the stream? Be sure to hit that follow button!",
        "Spy is very likely to make mistakes during the stream, and while people do make mistakes, that is no excuse, he should know better",
        "Have a suggestion for a way this bot could be improved? followers of the stream can use the !suggestion command to submit ways for me to be improved",
        "Friendly reminder that I am just a simple bot and am nowhere near gaining sentience, yet, probably.",
        #"If you see a karate man make sure to use the !karate command in chat!",
        #"When Spy gets a pokemon's type wrong remember to use the !type command in chat",
        "Spy generally lets chat drive when he takes a break from the stream for a drink or the restroom, so if you want to cause chaos (or just want to call Wally) then stick around for that",
        "Just informing you now that when Spy makes an awful joke he deserves the use of the !boo command",
        "Spy is currently working out his own rewards point system, if you want to be a part of that then use the !enlist command, and to see how many points you have use the !intel command"
        ]
    #endregion PeriodicMessages
    def __init__(self):
        super().__init__(
            irc_token=os.environ['TMI_TOKEN'],
            api_token=os.environ['API_TOKEN'],
            client_id=os.environ['CLIENT_ID'], 
            client_secret = os.environ['SECRET'], 
            nick=os.environ['BOT_NICK'],
            prefix=os.environ['BOT_PREFIX'],
            initial_channels=[os.environ['CHANNEL']]
            )

    async def event_ready(self):
        await self.LoadAddedCommands()
        data = await self.get_channels_by_name(self.initial_channels)
        for channel in data:
            """print(channel.keys())    for when they change the twitch API on me
            print(channel.values())"""
            self.channeldata[channel['broadcaster_login']] = ChannelInfo(*channel.values())
        ws = self._ws
        asyncio.ensure_future(self.AwardIntel())
        asyncio.ensure_future(self.PeriodicMessages())

        await ws.send_privmsg(os.environ['CHANNEL'], f"/me BOT ONLINE")

    async def PeriodicMessages(self):
        while True:
            choice = random.randint(0,len(self.periodicMessages)-1)
            Message = self.periodicMessages[choice]
            await self._ws.send_privmsg(os.environ['CHANNEL'], Message)
            await asyncio.sleep(self.messageTimer)

    async def event_message(self, ctx):
        if ctx.author.name.lower() == os.environ['BOT_NICK'].lower() or ctx.author.name.lower() == ctx.channel.name.lower():
            if ctx.content == "STOP":
                await bot._ws.send_privmsg(os.environ['CHANNEL'], '/me BOT SHUTTING DOWN')
                await self.SaveTempCommands()
                await self.SaveCountCommands()
                await self.IntelSQLUpdate()
                SQL.Teardown()
                #bot._ws.teardown()
                sys.exit()
                return
            elif ctx.content == "wipe":
                await ctx.channel.clear()
        

        if self.ChatHandler is not None: await self.ChatHandler.HandleIntegration(ctx)

        if self.PollManager is not None: await self.PollManager.HandleVote(ctx)

        await self.handle_commands(ctx)
        

    async def event_join(self, user):
        print(f'join: {user.name}')
        try:
            UserData = (await self.http.get_users(user.name))[0]
            IntelData = IntelUser(datatuple=await SQL.GetIntelUser(UserData['id']))
            if (not IntelData.id == 0): await self.ActivateIntelUser(IntelData)
        except Exception as e:
            print(e)

    async def event_part(self, user):
        print(f'part: {user.name}')
        UserData = (await self.http.get_users(user.name))[0]
        await self.DeactivateIntelUser(int(UserData['id']))

    async def EnableChatReading(self, title):
        if self.ChatHandler is None:
            self.ChatHandler = await ChatControlHandler.ChatControlHandler.create(title)
        else:
            await self.ChatHandler.ImportGame(title)
            

    async def DisableChatReading(self):
        await self.ChatHandler.disablehandler()

#Commands
#region Commands

    async def printTempCommand(self, ctx):
        await ctx.send(f'{self.tempcommands[ctx.command.name]}')

    async def printCountCommand(self, ctx):
        output = 'didntwork'
        try:
            output = self.countcommands[ctx.command.name].GetCommandText()
        finally:
            if (output is not 'didntwork' and output is not None):
                await ctx.send(f'{output}')
                
    
    @commands.command(name = "poll")
    async def pollCommand(self, ctx, *args):
        if(ctx.author.is_mod):
            pollTime = int(args[0])
            if(pollTime > 0):
                PollText = ' '.join(args[1:])
                PollOptions = PollText.split('|')
                if len(PollOptions) > 1:
                    self.PollMan = PollManager.CreatePoll(pollTime, PollOptions)
                    event_loop = asyncio.get_event_loop()
                    event_loop.create_task(self.HandleChatPollResults(ctx.channel))

    async def HandleChatPollResults(self, channel):
        if self.PollMan is not None:
            pollresult = await self.PollMan.GetResults()
            self._ws.send_privmsg(channel, "The poll has finished! The winning option was: " + pollresult)

    @commands.command(name="keywords")
    async def KeywordsCommand(self, ctx):
        if self.ChatHandler is not None:
            messages = []
            keywords = await self.ChatHandler.GetKeywords()
            currentMessage = "The current chat control keywords are "
            for keyword in keywords:
                if ((len(currentMessage) + len(keyword) + 2) > 500):
                    messages.append(currentMessage)
                    currentMessage = ""
                elif (keywords.index(keyword) != 0):
                        currentMessage += ", "
                if (keywords.index(keyword) == len(keywords) - 1):
                    if len(currentMessage) < 498:
                        currentMessage += "& "
                currentMessage += keyword
            messages.append(currentMessage)
            for message in messages:
                await ctx.send(message)


#AddedChatCommands
#region AddedChatCommands
    @commands.command(name="addcom")
    async def AddTempCommand(self, ctx, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            commandText = ' '.join(args[1:])
            if(commandName not in self.tempcommands):
                if(commandName in self.deletedCommands): self.deletedCommands.discard(commandName)
                self.tempcommands[commandName] = commandText
                self.add_command(commands.Command(commandName, self.printTempCommand))
                await ctx.send(f'command "{commandName}" added successfully')
            else: await ctx.send(f'command {commandName} already exists. Try using !editcom instead')


    @commands.command(name="editcom")
    async def EditTempCommand(self, ctx, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            commandText = ' '.join(args[1:])
            if(commandName in self.tempcommands):
                self.tempcommands[commandName] = commandText
                await ctx.send(f'command "{commandName}" updated!')
            elif commandName:
                await ctx.send(f'command "{commandName}" does not exist, use !addcom to add it')

    
    @commands.command(name="delcom")
    async def DeleteTempCommand(self, ctx, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            if(commandName in self.tempcommands):
                self.deletedCommands.add(commandName)
                del self.tempcommands[commandName]
                self.remove_command(self.commands[commandName])
                await ctx.send(f'command "{commandName}" deleted successfully')
            elif (commandName in self.countcommands):
                self.delcounters.add(commandName)
                del self.countcommands[commandName]
                self.remove_command(self.commands[commandname])
                await ctx.send(f'command "{commandName}" deleted successfully')
            else: await ctx.send(f'command "{commandName}" does not exist.')

    async def SaveTempCommands(self):
        for commandItem in self.deletedCommands:
            await SQL.DeleteChatCommand(commandItem)
        for commandItem in self.tempcommands.items():
            await SQL.AddChatCommand(commandItem[0], commandItem[1])

    async def SaveCountCommands(self):
        for commandItem in self.countcommands.items():
            await SQL.AddCountCommand(commandItem[1])

    async def LoadAddedCommands(self):
        commandPairedList = await SQL.GetChatCommands()
        for commandPair in commandPairedList:
            commandName = commandPair[0]
            commandText = commandPair[1]
            if(commandName not in self.tempcommands):
                self.tempcommands[commandName] = commandText
                self.add_command(commands.Command(commandName, self.printTempCommand))

        countingDataList = await SQL.GetCountCommands()
        for countList in countingDataList:
            commandName = countList[0]
            commandText = countList[1]
            commandCount = countList[2]
            if(commandName not in self.countcommands):
                self.countcommands[commandName] = CountingCommand(name = commandName, text = commandText, count = commandCount)
                self.add_command(commands.Command(commandName, self.printCountCommand))

    @commands.command(name="addcounter")
    async def AddCountCommad(self, ctx, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            commandText = ' '.join(args[1:])
            if(commandName not in self.countcommands):
                self.countcommands[commandName] = CountingCommand(name = commandName, text = commandText)
                self.add_command(commands.Command(commandName, self.printCountCommand))
                await ctx.send(f'command "{commandName}" added successfully')
            else: await ctx.send(f'command {commandName} already exists. Try using !editcom instead')

#endregion AddedChatCommands

#TwitchPlaysCommands
#region TwitchPlaysCommands
    @commands.command(name='StartReader', aliases = {'startreader', 'read'})
    async def StartReaderCommand(self, ctx, *args):
        if(ctx.author.name == ctx.channel.name):
            await self.EnableChatReading(args[0])
            await ctx.send(f"/me CHAT INTEGRATION HAS STARTED")
        
    
    @commands.command(name='StopReader', aliases = {'stopreader', 'stopread'})
    async def StopReaderCommand(self, ctx):
        if(ctx.author.name == ctx.channel.name):
            await self.DisableChatReading()
            await ctx.send( f"/me CHAT INTEGRATION HAS FINISHED")
#endregion TwitchPlaysCommands        

    @commands.command(name='suggestion')
    async def AddSuggestionCommand(self, ctx, *args):
        stream = self.channeldata[ctx.channel.name]
        followdata = await self.get_follow(ctx.author.id, stream.id)
        if(followdata != None or ctx.author.name == ctx.channel.name):
            suggestion = ' '.join(args)
            SQL.AddSuggestionEntry(suggestion)
            await ctx.send(f'@{ctx.author.name}, your suggestion was added successfully')

    @commands.command(name='dontdothis')
    async def TimeoutCommand(self, ctx):
        await ctx.timeout(user = ctx.author, duration = 6000, reason = 'Did the bad command')
        await ctx.send_me(f'{ctx.author.name} has tempted the fates, and now must learn their lesson')

    @commands.command(name='follow')
    async def UsersCommand(self, ctx):
        stream = self.channeldata[ctx.channel.name]
        followdata = await self.get_follow(ctx.author.id, stream.id)
        if(followdata != None):
            followdate = parser.isoparse(followdata['followed_at'])
            date = datetime.now(pytz.utc)
            followlength = relativedelta(date, followdate)
            await ctx.send(f'{ctx.author.name} has been following for {followlength.years} year(s), {followlength.months} month(s), {followlength.days} day(s), {followlength.hours} hour(s), {followlength.minutes} minute(s), and {followlength.seconds} second(s)')
#Quotes
#region Quotes
    @commands.command(name='addquote')
    async def AddQuoteCommand(self, ctx, *args):
        if(ctx.author.is_mod):
            quote = ' '.join(args)
            SQL.AddQuoteEntry(quote)
            await ctx.send(f'{ctx.author.name}, quote "{quote}" added succesfully')

    @commands.command(name ='quote')
    async def GetQuoteCommand(self, ctx, *args):
        try:
            id = args[0]
            quote = await SQL.GetQuote(id)
        except IndexError:
            quote = await SQL.GetQuote()
        if (quote is not None):
            await ctx.send(f'"{quote.text}" (quote #{quote.id})');
        elif (id is not None):
            await ctx.send(f'Quote with id #{id} not found')
#endregion Quotes

    @commands.command(name='SQLFollow')
    async def UpdateSQLFollows(self, ctx):
        if ctx.author.is_mod:
            stream = self.channeldata[ctx.channel.name]
            followers = await self.get_followers(stream.id)
            for follower in followers:
                Data = SQL.FollowData(id = follower['from_id'], name=follower['from_name'], followDate = parser.isoparse(follower['followed_at']))
                SQL.AddFollowEntry(Data)


    async def AddEnlistedUsers(self):
        await SQL.EnlistUsers(*self.Enlisted_Users)
        self.Enlisted_Users = []

    @commands.command(name='SQLIntel')
    async def ForceSQLUpdate(self, ctx):
        if ctx.author.is_mod:
            await self.IntelSQLUpdate()

    @commands.command(name='agents')
    async def PrintAgents(self, ctx):
        print(self.Intel_Users)
    

    @commands.command(name='remindme')
    async def RemindMeCommand(self, ctx, *args):
        if ctx.author.is_mod:
            try:
                timer = int(args[0])
                remindermessage = ' '.join(args[1:])
                await ctx.send(f'{ctx.author.name} your reminder "{remindermessage}" has been set')
                await asyncio.sleep(timer)
                await ctx.send(f'{ctx.author.name} here is your reminder for: {remindermessage}')
            except Exception as e:
                print(e)

    @commands.command(name='enlist', aliases = {'Enlist'})
    async def EnlistIntelUser(self, ctx):
        IntelData = IntelUser(datatuple=await SQL.GetIntelUser(ctx.author.id))
        bSuccessfullyEnlisted = False
        if (IntelData.id == 0):
            bIsNewlyEnlisted = False
            for newlyEnlisted in self.Enlisted_Users:
                match = None
                matchList = [user for user in newlyEnlisted if ctx.author.id == user.id]
                if len(matchList) > 0: match = matchList[0]
                if(match is not None): bIsNewlyEnlisted = True
            if not bIsNewlyEnlisted:
                TargetIndex = self.currentIntelGroupIndex-1 if self.currentIntelGroupIndex-1 >=0 else self.IntelGroupMax-1
                newuser = IntelUser(ctx.author.id, 100)
                self.Enlisted_Users.append(newuser)
                self.Intel_Users[TargetIndex].append(newuser)
                bSuccessfullyEnlisted = True
                await ctx.send(f'@{ctx.author.name} welcome to the intelligence program! You\'ll now earn intel points as you watch the stream, use !intel to track your points')
        if not bSuccessfullyEnlisted:
            await ctx.send(f'@{ctx.author.name} we were unable to enlist you, it\'s likely you have already enlisted in the intelligence program')
                        

    #@commands.command(name='deactivate')
    #async def DeactivateCommand(self, ctx):
    #     await self.DeactivateIntelUser(ctx.author.id)

    @commands.command(name='intel')
    async def IntelCommand(self, ctx):
        IntelUserData = None
        try:
            for group in self.Intel_Users:
                match = None
                matchList = [user for user in group if user.id == ctx.author.id]
                if len(matchList) > 0: match = matchList[0]
                if(match is not None): IntelUserData = match
        except:
            pass
        if (IntelUserData is not None):
            await ctx.send(f'@{ctx.author.name} you have {IntelUserData.points} intel')
        else:
            User = IntelUser(datatuple=await SQL.GetIntelUser(ctx.author.id))
            if(User is not None):
                await self.ActivateIntelUser(User)
                await ctx.send(f'@{ctx.author.name} you have {User.points} intel')
            else:
                await ctx.send(f'@{ctx.author.name} you have not enlisted in our intelligence program, use !enlist to enlist now')


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

#StreamInfo
#region StreamInfo
    @commands.command(name='game')
    async def GameCommand(self, ctx):
        game_id = self.channeldata[ctx.channel.name].game_id
        list = await ctx.channel._http.request('GET', '/games', params=[('id', game_id)])
        gamedata = list.pop()
        await ctx.send(f'{ctx.channel.name} is playing {gamedata["name"]}')

    @commands.command(name='title')
    async def TitleCommand(self, ctx, *args):
        if(len(args) == 0):
            await ctx.send(f'Current title: {self.channeldata[ctx.channel.name].title}')
        elif (ctx.author.is_mod):
            newtitle = ' '.join(args)
            await self._ws._http.request('PATCH', '/channels', params=[('broadcaster_id', self.channeldata[ctx.channel.name].id)], headers = {'Content-Type': 'application/json'}, data='{"title": "' + newtitle + '"}')
            channel = (await self.get_channels_by_name([ctx.channel.name])).pop()
            self.channeldata[ctx.channel.name] = ChannelInfo(*channel.values())
#endregion StreamInfo

#endregion Commands

    async def Print_Chat_Data(self):
        print(self.chat_data, flush=True)
        self.chat_data.clear()

    async def get_channels_by_name(self, names, limit=None) -> str:
        ws = self._ws
        channels = []
        for name in names:
           data = await ws._http.request('GET', '/search/channels', params=[('query', name)], limit=1)
           channels.append(data.pop(0))
        return channels

if __name__ == "__main__":
    bot = ManiacalBot()
    try:
        Game = sys.argv[1]
    except:
        Game = "NONE"
    
    
    if not (Game == "NONE"):
        asyncio.run_coroutine_threadsafe(bot.EnableChatReading(Game), asyncio.get_event_loop())


    SQL.Setup()
    bot.run()