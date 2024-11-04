import GameInputBase
import asyncio
import json
import socket
import select
import IntelManager
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

class TestGameData(GameInputBase.GameInputBase):
    """description of class"""


    def __init__(self):
        self.reading = True
        self.socketKeywords = {
            "testone" : self.JSONlamfactory("Func1"),
            "testtwo" : self.JSONlamfactory("Func2")#,
            #"lick" : "makewet",
            #"rest" : "makerested",
            #"burn" : "makeburning"
            }
        self.mysock = socket.create_connection((HOST,PORT)) #(socket.AF_INET, socket.SOCK_STREAM, proto = 0)
        #self.mysock.connect((HOST, PORT))
        #self.mysock.
        loop = asyncio.get_event_loop()
        loop.create_task(self.SocketResponseTask())



    def JSONlamfactory(self,functiontocall):
        return (lambda username, id, Callid = -1: self.WriteAndSendJSON(username = username, id = id, Callid = Callid, function = functiontocall))


    def WriteAndSendJSON(self, username, id, Callid,function):
        JSONToSend = json.dumps({"User" : username.lower(), "CallID": Callid, "Function": function})
        loop = asyncio.get_event_loop()
        loop.create_task(self.SendJSON(JSONToSend))
    
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


    async def GetKeywords(self):
        output = []
        for keyword in self.socketKeywords.keys():
            #if keyword in self.IntelCosts:
            #    output.append("{key} ({cost} Intel)".format(key=keyword, cost = self.IntelCosts[keyword]))
            #else:
            output.append(keyword)
        return (output)

    async def SendJSON(self, jsonobj):
        encodedmsg = jsonobj.encode()
        msgSize = len(encodedmsg)
        print('\tPacket Size: ' + str(msgSize))
        self.mysock.sendall(msgSize.to_bytes(1, 'big'))
        self.mysock.sendall(encodedmsg)


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
                        sizeData = sock.recv(1)
                        if not sizeData:
                            break;
                        print('sizeData:' + str(sizeData,'utf-8'))
                        if (len(sizeData) == 0): break;
                        print('ord(sizeData):' + str(ord(str(sizeData,'utf-8'))))
                        if(ord(sizeData) > 0):
                            data = self.mysock.recv(ord(sizeData))
                            print('Received', str(data, 'utf-8'))
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