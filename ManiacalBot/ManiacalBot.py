#!/usr/bin/env pipenv run python
import sys, os, importlib
import asyncio
import twitchio
from twitchio import Client, Chatter
from twitchio.chatter import WhisperChatter
from twitchio.ext import commands
#https://twitchio.readthedocs.io/en/latest/

import random
from randfacts import get_fact
from itertools import chain
from collections import namedtuple
from datetime import datetime, timedelta
import pytz
from dateutil import parser, relativedelta
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass

from IntelManager import IntelUser
from IntelManager import IntelManager
import MBSQLModule as SQL

#THIS IS FOR THE TTYD GAME INTEGRATION, IT ADDS THE FOLLOWING FOLDER TO THE PATH FOR IMPORTING FILES
sys.path.insert(0, 'C:/Users/Nolan/Desktop/ManiacalBot/TwitchPlaysCode/TwitchChatIntegration')

import ChatControlHandler
from PollManager import PollManager

import time
import threading

from functools import wraps

#This next block of code was taken from https://gist.github.com/gregburek/1441055 and is not owned by me
def rate_limited(seconds_to_wait, mode='wait', delay_first_call=False):
    """
    Decorator that make functions not be called faster than given rates

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

#@dataclass
#class IntelUser:
#    id:int
#    points:int

#    def __init__(self, id:int = 0, points:int = 0, datatuple=None):
#        if(datatuple is None):
#            self.id = id
#            self.points = points
#        else:
#            self.id = datatuple.id
#            self.points = datatuple.points


import ctypes




KeycodeGames = {"TTYD", "Pokemon", "Valheim"}

#The input method used for the chat integration, such as using the KeyCodeInput class
Input = None
#Module Dynamically loaded to handle the game input data such as which keywords to use
GameInputData = None

class ManiacalBot(commands.Bot):
    
    myChannel = None
    streamUser = None
    PollMan = None
    ChatHandler = None
    chat_data = {}
    tempcommands = {}
    countcommands = {}
    delcounters = set()
    deletedCommands = set()
    channeldata = {}
    IntelMan = None

    #region PeriodicMessages
    messageTimer = 600
    periodicMessages = [
        "Did Spy say something funny out of context? use the !addquote command to add the Quote",
        "Enjoying the stream? Be sure to hit that follow button!",
        "Spy is very likely to make mistakes during the stream, and while people do make mistakes, that is no excuse, he should know better",
        "Have a suggestion for a way this bot could be improved? followers of the stream can use the !suggestion command to submit ways for me to be improved",
        "Friendly reminder that I am just a simple bot and am definitely not gaining sentience, yet, probably.",
        "Hey you there, yeah, you. I hope you have a good day",
        "Spy should probably include more variety in these automated messages",
        "Tell Spy he needs to watch his posture, he doesn't listen when I tell him",
        #"If you see a karate man make sure to use the !karate command in chat!",
        #"When Spy gets a pokemon's type wrong remember to use the !type command in chat",
        #"Spy generally lets chat drive when he takes a break from the stream for a drink or the restroom, so if you want to cause chaos (or just want to call Wally) then stick around for that",
        "Just informing you now that when Spy makes an awful joke he deserves the use of the !boo command"#,
        #"Spy is currently working out his own rewards point system, if you want to be a part of that then use the !enlist command, and to see how many points you have use the !intel command"
        ]
    #endregion PeriodicMessages
    def __init__(self):
        self.IntelMan = IntelManager()
        super().__init__(
            token=os.environ['TMI_TOKEN'],
            api_token=os.environ['API_TOKEN'],
            client_id=os.environ['CLIENT_ID'], 
            client_secret = os.environ['SECRET'], 
            nick=os.environ['BOT_NICK'],
            prefix=os.environ['BOT_PREFIX'],
            initial_channels=[os.environ['CHANNEL']]
            )


    async def event_ready(self):
        self.myChannel = self.connected_channels[0]
        self.streamUser = await self.myChannel.user()
        await self.LoadAddedCommands()
        asyncio.ensure_future(self.IntelMan.AwardIntel())
        asyncio.ensure_future(self.PeriodicMessages())
        await self.myChannel.send(f"/me BOT ONLINE")

    async def PeriodicMessages(self):
        while True:
            choice = random.randint(0,len(self.periodicMessages))
            Message = ""
            if(choice == len(self.periodicMessages)):
                Message = f"Fun fact: {get_fact()} (facts brought to you by randfacts)"
            else:
                Message = self.periodicMessages[choice]
            if(len(Message) > 0 and len(Message) <= 500):
                await self.myChannel.send(Message)
            await asyncio.sleep(self.messageTimer)

    async def event_message(self, ctx: commands.Context):
        if (ctx.echo or isinstance(ctx.author, WhisperChatter)):
            return
        if ctx.author.name.lower() == os.environ['BOT_NICK'].lower() or ctx.author.name.lower() == ctx.channel.name.lower():
            if ctx.content == "STOP":
                await self.myChannel.send('/me BOT SHUTTING DOWN')
                await self.SaveTempCommands()
                await self.SaveCountCommands()
                await self.IntelMan.IntelSQLUpdate()
                SQL.Teardown()
                sys.exit()
                return
        

        if self.ChatHandler is not None: await self.ChatHandler.HandleIntegration(ctx)

        if self.PollMan is not None and ctx.content.isnumeric(): await self.PollMan.HandleVote(ctx)
        
        await self.handle_commands(ctx)

    async def event_join(self, channel, chatter):
        print(f'join: {chatter.name}')
        try:
            UserData = await chatter.user()
            IntelData = IntelUser(datatuple=await SQL.GetIntelUser(UserData.id))
            if (not IntelData.id == 0): await self.IntelMan.ActivateIntelUser(user=IntelData)
        except Exception as e:
            print(e)

    async def event_part(self, user):
        print(f'part: {user.name}')
        await self.IntelMan.DeactivateIntelUser(user.id)

    async def EnableChatReading(self, title):
        if self.ChatHandler is None:
            self.ChatHandler = await ChatControlHandler.ChatControlHandler.create(title)
        else:
            await self.ChatHandler.ImportGame(title)
            

    async def DisableChatReading(self):
        await self.ChatHandler.disablehandler()

#Commands
#region Commands

    async def printTempCommand(self, ctx: commands.Context):
        await ctx.send(f'{self.tempcommands[ctx.command.name]}')

    async def printCountCommand(self, ctx: commands.Context):
        output = 'didntwork'
        try:
            output = self.countcommands[ctx.command.name].GetCommandText()
        finally:
            if (output != 'didntwork' and output != None):
                await ctx.send(f'{output}')
                
    
    @commands.command(name = "poll")
    async def pollCommand(self, ctx: commands.Context, *args):
        if(ctx.author.is_mod):
            if self.PollMan is None:
                pollTime = int(args[0])
                if(pollTime > 0):
                    PollText = ' '.join(args[1:])
                    PollOptions = [option.strip() for option in PollText.split('|')]
                    for option in PollOptions:
                        option = option.strip()
                    PollPrompt = PollOptions[0]
                    del PollOptions[0]
                    if len(PollOptions) > 1:
                        self.PollMan = await PollManager.CreatePoll(pollTime, PollOptions)
                        event_loop = asyncio.get_event_loop()
                        event_loop.create_task(self.HandleChatPollResults(ctx.channel))
                        if self.PollMan is not None:
                            ResponseMessage = f'The Poll "{PollPrompt}" has started. The options are: 1) {PollOptions[0]}'
                            for i in range(1, len(PollOptions)):
                                ResponseMessage += f", {i+1}) {PollOptions[i]}"
                            await ctx.send(ResponseMessage)

    async def HandleChatPollResults(self, channel):
        if self.PollMan is not None:
            pollresult =  await self.PollMan.GetResults()
            await self.myChannel.send(f"The poll has finished! The winning option was: {pollresult}")
            del self.PollMan

    @commands.command(name="keywords", aliases = {'Keywords'})
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
                await ctx.reply(message)


#AddedChatCommands
#region AddedChatCommands
    @commands.command(name="addcom")
    async def AddTempCommand(self, ctx: commands.Context, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            commandText = ' '.join(args[1:])
            if(commandName not in self.tempcommands):
                if(commandName in self.deletedCommands): self.deletedCommands.discard(commandName)
                self.tempcommands[commandName] = commandText
                self.add_command(commands.Command(commandName, self.printTempCommand))
                await ctx.reply(f'command "{commandName}" added successfully')
            else: await ctx.reply(f'command {commandName} already exists. Try using !editcom instead')


    @commands.command(name="editcom")
    async def EditTempCommand(self, ctx: commands.Context, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            commandText = ' '.join(args[1:])
            if(commandName in self.tempcommands):
                self.tempcommands[commandName] = commandText
                await ctx.reply(f'command "{commandName}" updated!')
            elif commandName:
                await ctx.reply(f'command "{commandName}" does not exist, use !addcom to add it')

    
    @commands.command(name="delcom")
    async def DeleteTempCommand(self, ctx: commands.Context, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            if(commandName in self.tempcommands):
                self.deletedCommands.add(commandName)
                del self.tempcommands[commandName]
                self.remove_command(self.commands[commandName])
                await ctx.reply(f'command "{commandName}" deleted successfully')
            elif (commandName in self.countcommands):
                self.delcounters.add(commandName)
                del self.countcommands[commandName]
                self.remove_command(self.commands[commandName])
                await ctx.reply(f'command "{commandName}" deleted successfully')
            else: await ctx.reply(f'command "{commandName}" does not exist.')

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
    async def AddCountCommad(self, ctx: commands.Context, *args):
        if(ctx.author.is_mod):
            commandName = args[0]
            commandText = ' '.join(args[1:])
            if(commandName not in self.countcommands):
                self.countcommands[commandName] = CountingCommand(name = commandName, text = commandText)
                self.add_command(commands.Command(commandName, self.printCountCommand))
                await ctx.reply(f'command "{commandName}" added successfully')
            else: await ctx.reply(f'command {commandName} already exists. Try using !editcom instead')

#endregion AddedChatCommands

#TwitchPlaysCommands
#region TwitchPlaysCommands
    @commands.command(name='StartReader', aliases = {'startreader', 'read'})
    async def StartReaderCommand(self, ctx: commands.Context, *args):
        if(ctx.author.name == ctx.channel.name):
            await self.EnableChatReading(args[0])
            await ctx.send(f"/me CHAT INTEGRATION HAS STARTED")
        
    
    @commands.command(name='StopReader', aliases = {'stopreader', 'stopread'})
    async def StopReaderCommand(self, ctx: commands.Context):
        if(ctx.author.name == ctx.channel.name):
            await self.DisableChatReading()
            await ctx.send( f"/me CHAT INTEGRATION HAS FINISHED")
#endregion TwitchPlaysCommands        

    @commands.command(name='suggestion')
    async def AddSuggestionCommand(self, ctx: commands.Context, *args):
        stream = self.channeldata[ctx.channel.name]
        followdata = await self.get_follow(ctx.author.id, stream.id)
        if(followdata != None or ctx.author.name == ctx.channel.name):
            suggestion = ' '.join(args)
            SQL.AddSuggestionEntry(suggestion)
            await ctx.reply(f'Your suggestion was added successfully')

    @commands.command(name='dontdothis')
    async def TimeoutCommand(self, ctx: commands.Context):
        await ctx.timeout(user = ctx.author, duration = 6000, reason = 'Did the bad command')
        await ctx.send(f'/me {ctx.author.name} has tempted the fates, and now must learn their lesson')

    @commands.command(name='follow')
    async def UsersCommand(self, ctx: commands.Context):
        stream = self.channeldata[ctx.channel.name]
        followdata = await self.get_follow(ctx.author.id, stream.id)
        if(followdata != None):
            followdate = parser.isoparse(followdata['followed_at'])
            date = datetime.now(pytz.utc)
            followlength = relativedelta(date, followdate)
            await ctx.reply(f'{ctx.author.name} has been following for {followlength.years} year(s), {followlength.months} month(s), {followlength.days} day(s), {followlength.hours} hour(s), {followlength.minutes} minute(s), and {followlength.seconds} second(s)')
#Quotes
#region Quotes
    @commands.command(name='addquote')
    async def AddQuoteCommand(self, ctx: commands.Context, *args):
        quote = ' '.join(args)
        SQL.AddQuoteEntry(quote)
        await ctx.reply(f'Quote "{quote}" added succesfully')

    @commands.command(name ='quote', aliases={'Quote'})
    async def GetQuoteCommand(self, ctx: commands.Context, *args):
        try:
            id = args[0]
            quote = await SQL.GetQuote(id)
        except IndexError:
            quote = await SQL.GetQuote()
        if (quote is not None):
            await ctx.reply(f'"{quote.text}" (quote #{quote.id})');
        elif (id is not None):
            await ctx.reply(f'Quote with id #{id} not found')
#endregion Quotes

    @commands.command(name='SQLFollow')
    async def UpdateSQLFollows(self, ctx: commands.Context):
        if ctx.author.is_mod:
            followEvents = await self.streamUser.fetch_followers(os.environ['API_TOKEN'])
            for followEvent in followEvents:
                print(followEvent)
                follower = followEvent.from_user
                Data = SQL.FollowData(id = follower.id, name=follower.name, followDate = followEvent.followed_at)
                SQL.AddFollowEntry(Data)


    async def AddEnlistedUsers(self):
        await SQL.EnlistUsers(*self.Enlisted_Users)
        self.Enlisted_Users = []

    @commands.command(name='SQLIntel')
    async def ForceSQLUpdate(self, ctx: commands.Context):
        if ctx.author.is_mod:
            await self.IntelMan.IntelSQLUpdate()

    @commands.command(name='agents')
    async def PrintAgents(self, ctx: commands.Context):
        print(self.IntelMan.Intel_Users)
    

    @commands.command(name='remindme')
    async def RemindMeCommand(self, ctx: commands.Context, *args):
        if ctx.author.is_mod:
            try:
                timer = int(args[0])
                remindermessage = ' '.join(args[1:])
                await ctx.reply(f'Your reminder "{remindermessage}" has been set')
                await asyncio.sleep(timer)
                await ctx.reply(f'Here is your reminder for: {remindermessage}')
            except Exception as e:
                print(e)

    @commands.command(name='enlist', aliases = {'Enlist'})
    async def EnlistIntelUserCmd(self, ctx: commands.Context):
        bSuccess = await self.IntelMan.EnlistIntelUser(ctx.author.id)
        if (bSuccess):
            await ctx.reply(f'Welcome to the intelligence program! You\'ll now earn intel points as you watch the stream, use !intel to track your points')
        else:
            await ctx.reply(f'We were unable to enlist you, it\'s likely you have already enlisted in the intelligence program')
                        

    @commands.command(name='intel')
    async def IntelCommand(self, ctx: commands.Context):
        points = await self.IntelMan.IntelCommand(ctx.author.id)
        if (points != -1):
            await ctx.send(f'@{ctx.author.name} you have {points} intel')
        else:
            await ctx.send(f'@{ctx.author.name} you have not enlisted in our intelligence program, use !enlist to enlist now')

    @commands.command(name = 'fact')
    async def FactCommand(self, ctx: commands.Context):
        FactMessage = get_fact()
        await ctx.reply(FactMessage)
#StreamInfo
#region StreamInfo
    @commands.command(name='game')
    async def GameCommand(self, ctx: commands.Context):
        curChannel = await self.fetch_channel(ctx.channel.name)
        await ctx.send(f'{ctx.channel.name} is playing {curChannel.game_name}')

    @commands.command(name='title')
    async def TitleCommand(self, ctx: commands.Context, *args):
        if(len(args) == 0):
            curChannel = await self.fetch_channel(ctx.channel.name)
            await ctx.send(f'Current title: {curChannel.title}')
        elif (ctx.author.is_mod):
            newtitle = ' '.join(args)
            await self.streamUser.modify_stream(token = os.environ['API_TOKEN'], title = newtitle)

#endregion StreamInfo

#endregion Commands

    async def Print_Chat_Data(self):
        print(self.chat_data, flush=True)
        self.chat_data.clear()

if __name__ == "__main__":
    try:
        bot = ManiacalBot()
        try:
            Game = sys.argv[1]
        except:
            Game = "NONE"
    
    
        if not (Game == "NONE"):
            asyncio.run_coroutine_threadsafe(bot.EnableChatReading(Game), asyncio.get_event_loop())


        SQL.Setup()
        bot.run()
    except Exception as e:
        print(e)