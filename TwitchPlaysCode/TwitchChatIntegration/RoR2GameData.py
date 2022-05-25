import GameInputBase
from InputDataClasses import *
#from dataclasses import dataclass
from DirectXKeyCodes import KeyCodes
import KeyCodeInput
import asyncio
import json
import socket
import select
import IntelManager

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server
PACKET_SIZE = 128



class RoR2GameData(GameInputBase.GameInputBase):
    """description of class"""
    def __init__(self):
        self.reading = True
        self.IntelCosts = {
            "movingon" : 25,
            "nailbiter" : 50,
            "nolife" : 25,
            "organize" : 50,
            "ambush": 10
            }
        self.socketKeywords = {
            "whiteitem" : self.JSONlamfactory("spawnwhite"),
            "greenitem" : self.JSONlamfactory("spawngreen"),
            "reditem" : self.JSONlamfactory("spawnred"),
            "blueitem" : self.JSONlamfactory("spawnlunar"),
            "pinkitem" : self.JSONlamfactory("spawnvoid"),
            "anyitem" : self.JSONlamfactory("spawnany"),
            "equipment" : self.JSONlamfactory("spawnequip"),
            "yoink" : self.JSONlamfactory("removeitem"),
            "slow" : self.JSONlamfactory("applyslow"),
            "weak" : self.JSONlamfactory("applyweak"),
            "overheat" : self.JSONlamfactory("applyoverheat"),
            "hobble" : self.JSONlamfactory("applyhobble"),
            "takemoney" : self.JSONlamfactory("takemoney"),
            "givemoney" : self.JSONlamfactory("givemoney"),
            "heal" : self.JSONlamfactory("heal"),
            "movingon" : IntelManager.IntelCostFunction(self.IntelCosts["movingon"], DelayCost = True)(self.JSONlamfactory("nextstage")),
            "nailbiter" : IntelManager.IntelCostFunction(self.IntelCosts["nailbiter"], DelayCost = True)(self.JSONlamfactory("OneHP")),
            "organize" : IntelManager.IntelCostFunction(self.IntelCosts["organize"], DelayCost = True)(self.JSONlamfactory("OrderInventory")),
            "nolife" : IntelManager.IntelCostFunction(self.IntelCosts["nolife"], DelayCost=True)(self.JSONlamfactory("HideHP")),
            "ambush" : IntelManager.IntelCostFunction(self.IntelCosts["ambush"], DelayCost=True)(self.JSONlamfactory("Ambush"))
            #,"test" : self.JSONlamfactory("testcommand")
            }
        self.testKeywords = {
            "test" : self.JSONlamfactory("testcommand"),#(lambda username, id, Callid = -1: self.WriteAndSendJSON(username = username, id = id, Callid = Callid, function = "testcommand")),
            "inteltest" : IntelManager.IntelCostFunction(0, DelayCost = True)(self.JSONlamfactory("testcommand"))#(lambda username, id, Callid = -1: self.WriteAndSendJSON(username = username, id = id, Callid = Callid, function = "testcommand")))
            }
        self.mysock = socket.create_connection((HOST,PORT)) #(socket.AF_INET, socket.SOCK_STREAM, proto = 0)
        #self.mysock.connect((HOST, PORT))
        #self.mysock.
        loop = asyncio.get_event_loop()
        loop.create_task(self.SocketResponseTask())
    
    async def GetKeywords(self):
        output = []
        for keyword in self.socketKeywords.keys():
            if keyword in self.IntelCosts:
                output.append("{key} ({cost} Intel)".format(key=keyword, cost = self.IntelCosts[keyword]))
            else:
                output.append(keyword)
        return (output)


    async def HandleKeyword(self, ctx):
        try:
            keyword = ctx.content.strip(' ').lower()
        except:
            keyword = ctx
        #if keyword in self.keywords:
        #    InputData = self.keywords[keyword]
        #    if InputData.__class__ is InputChord:
        #        for item in InputData.InputList:
        #            loop = asyncio.get_event_loop()
        #            loop.create_task(self.SendInput(item))
        #    else:
        #        await self.SendInput(InputData)
        if keyword in self.socketKeywords:
            self.socketKeywords[keyword](username = ctx.author.name, id = ctx.author.id)
        #    funcname = self.socketKeywords[keyword]
        #    JSONToSend = json.dumps({"User" : ctx.author.name.lower(), "CallID" : -1, "Function": funcname})
        #    loop = asyncio.get_event_loop()
        #    loop.create_task(self.SendJSON(JSONToSend))
        #elif keyword in self.testKeywords:
        #    print(ctx.author.id)
        #    self.testKeywords[keyword](username = ctx.author.name, id = ctx.author.id)

    def JSONlamfactory(self,functiontocall):
        return (lambda username, id, Callid = -1: self.WriteAndSendJSON(username = username, id = id, Callid = Callid, function = functiontocall))


    def WriteAndSendJSON(self, username, id, Callid,function):
        JSONToSend = json.dumps({"User" : username.lower(), "CallID": Callid, "Function": function})
        loop = asyncio.get_event_loop()
        loop.create_task(self.SendJSON(JSONToSend))
    
    async def SendJSON(self, jsonobj):
        print(jsonobj)
        encodedmsg = jsonobj.encode()
        msgSize = len(encodedmsg)
        print('\tPacket Size: ' + str(msgSize))
        self.mysock.sendall(msgSize.to_bytes(1, 'big'))
        self.mysock.sendall(encodedmsg)
        print(encodedmsg)
        size = self.mysock.recv(2)
        data = self.mysock.recv(int(size))
        print('Received', str(data, 'utf-8'))
        if data:
            if data != -1:
                test = json.loads(data, object_hook=IntelManager.as_CommandFinishedResponse)
                if type(test) is IntelManager.CommandFinishedResponse:
                    if test.CallID != -1:
                        await IntelManager.IntelManager.Instance.ResolvePendingCall(test.CallID)

    async def TearDown(self):
        self.mysock.close()

    async def SocketResponseTask(self):
        while self.reading:
            ready_to_read, ready_to_write, in_error = \
                   select.select(
                    [self.mysock],
                      [],
                      [],
                      .1)
            for sock in ready_to_read:
                if sock == self.mysock:
                    size = sock.recv(2)
                    if not size:
                        break;
                    data = sock.recv(int(size))
                    if not data:
                        break;
                    else:
                        if data != -1:
                            test = json.loads(data, object_hook=IntelManager.as_CommandFinishedResponse)
                            if type(test) is IntelManager.CommandFinishedResponse:
                                if test.CallID != -1:
                                    await IntelManager.IntelManager.Instance.ResolvePendingCall(test.CallID)
                        else:
                            self.reading = False
            await asyncio.sleep(.25)
