from GameInputBase import *
import asyncio
import json
import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

class TestGameData(GameInputBase):
    """description of class"""


    def __init__(self):
        self.keywords = {
            "testone" : "Func1",
            "testtwo" : "Func2",
            "lick" : "makewet",
            "rest" : "makerested",
            "burn" : "makeburning"
            }
        self.mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mysock.connect((HOST, PORT))



    async def HandleKeyword(self, ctx):
        try:
            keyword = ctx.content.strip(' ').lower()
        except:
            keyword = ctx
        if keyword in self.keywords:
            funcname = self.keywords[keyword]
            JSONToSend = json.dumps({"User" : ctx.author.name.lower(), "Function": funcname})
            await self.SendJSON(JSONToSend)

    async def SendJSON(self, jsonobj):
        encodedmsg = jsonobj.encode()
        msgSize = len(encodedmsg)
        print('\tPacket Size: ' + str(msgSize))
        self.mysock.sendall(msgSize.to_bytes(1, 'big'))
        self.mysock.sendall(encodedmsg)
        data = self.mysock.recv(1024)
        print('Received', str(data, 'utf-8'))

    async def TearDown(self):
        self.mysock.close()
