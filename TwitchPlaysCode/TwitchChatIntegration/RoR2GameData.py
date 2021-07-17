import GameInputBase
from InputDataClasses import *
#from dataclasses import dataclass
from DirectXKeyCodes import KeyCodes
import KeyCodeInput
import asyncio
import json
import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server




class RoR2GameData(GameInputBase.GameInputBase):
    """description of class"""
    def __init__(self):
        self.socketKeywords = {
            "whiteitem" : "spawntest",
            "greenitem" : "spawntwo",
            "reditem" : "spawnthree",
            "blueitem" : "spawnlunar",
            "anyitem" : "spawnany",
            "equipment" : "spawnequip",
            "yoink" : "removeitem"
            }
        self.mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mysock.connect((HOST, PORT))
    
    async def GetKeywords(self):
        return (list(self.socketKeywords.keys()))


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
            funcname = self.socketKeywords[keyword]
            JSONToSend = json.dumps({"User" : ctx.author.name.lower(), "Function": funcname})
            loop = asyncio.get_event_loop()
            loop.create_task(self.SendJSON(JSONToSend))
    
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

