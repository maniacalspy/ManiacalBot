import GameInputBase
from InputDataClasses import *
#from dataclasses import dataclass
from DirectXKeyCodes import KeyCodes
import KeyCodeInput
import asyncio
import json
import socket

#@dataclass(frozen = True)
#class ButtonData:
#    button: int #Keycode you want to send
#    duration: float = 0.1


#@dataclass(frozen = True)
#class MouseData:
#    inputType: str = 'BUTTON' #either BUTTON, MOVEMENT, or SWAP
#    button: str = 'LEFT' #button to press if type is BUTTON
#    xMovement: int = 0 #distance to move on the X-axis if inputType is MOVEMENT
#    yMovement: int = 0 #distance to move on the Y-axis if inputType is MOVEMENT
#    duration: int = .15 #duration of either the button press or how long the mouse movement takes

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server


class ValheimGameData(GameInputBase.GameInputBase):

    def __init__(self):
        self.Input = KeyCodeInput
        self.keywords = {
            'jump' : ButtonData(KeyCodes.SPACEBAR),
            'crouch' : ButtonData(KeyCodes.LEFTCONTROL),
            'sit' : ButtonData(KeyCodes.X),
            'use' : ButtonData(KeyCodes.E),
            'walk' : ButtonData(KeyCodes.C),
            'look left': MouseData(inputType='MOVEMENT', xMovement= -1080),
            'look right': MouseData(inputType='MOVEMENT', xMovement= 1080),
            'attack': MouseData(inputType='BUTTON', button='LEFT'),
            'block': MouseData(inputType = 'BUTTON', button='RIGHT', duration = 3),
            'swap': MouseData(inputType = 'SWAP', duration = 5),
            'roll': InputChord({MouseData(inputType='BUTTON',button='RIGHT',duration=2), ButtonData(KeyCodes.SPACEBAR)})
            }
        self.socketKeywords = {
            "wet" : "makewet",
            "rest" : "makerested",
            "burn" : "makeburning",
            "rain" : "makerain",
            "stoprain" : "stoprain",
            "ohdeer" : "spawndeer",
            "crowno" : "spawncrows",
            "skelespawn" : "spawnskeletons"
            }
        self.mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mysock.connect((HOST, PORT))

    async def GetKeywords(self):
        return (list(self.keywords.keys()) + list(self.socketKeywords.keys()))


    async def HandleKeyword(self, ctx):
        try:
            keyword = ctx.content.strip(' ').lower()
        except:
            keyword = ctx
        if keyword in self.keywords:
            InputData = self.keywords[keyword]
            if InputData.__class__ is InputChord:
                for item in InputData.InputList:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.SendInput(item))
            else:
                await self.SendInput(InputData)
        elif keyword in self.socketKeywords:
            funcname = self.socketKeywords[keyword]
            JSONToSend = json.dumps({"User" : ctx.author.name.lower(), "Function": funcname})
            loop = asyncio.get_event_loop()
            loop.create_task(self.SendJSON(JSONToSend))
            
            #await self.SendJSON(JSONToSend)

    async def SendInput(self, InputType):
        if InputType.__class__ is ButtonData:
            loop = asyncio.get_event_loop()
            loop.create_task(self.Input.SendKeyInputDuration(key = InputType.button, duration = InputType.duration))
        elif InputType.__class__ is MouseData:
            loop = asyncio.get_event_loop()
            loop.create_task(self.Input.HandleMouseInput(InputType))
   




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
#@dataclass
#class GameInfo:
#    MouseControlsEnabled: bool = True
#    MouseMovementType: str = 'RELATIVE'

#keywords = {
#    'jump' : ButtonData(KeyCodes.SPACEBAR),
#    'crouch' : ButtonData(KeyCodes.LEFTCONTROL),
#    'sit' : ButtonData(KeyCodes.X),
#    'use' : ButtonData(KeyCodes.E),
#    'walk' : ButtonData(KeyCodes.C)
#    }

#class MouseControlData:
#    keywords = {
#        'look left': MouseData(inputType='MOVEMENT', xMovement= -1080),
#        'look right': MouseData(inputType='MOVEMENT', xMovement= 1080),
#        'attack': MouseData(inputType='BUTTON', button='LEFT'),
#        'block': MouseData(inputType = 'BUTTON', button='RIGHT', duration = 3),
#        'swap': MouseData(inputType = 'SWAP', duration = 5)
#        }


#class InputChords:
#    keywords = {
#        'roll': {MouseData(inputType='BUTTON',button='RIGHT',duration=2), ButtonData(KeyCodes.SPACEBAR)}
#        }