from .InputDataClasses import *
#from dataclasses import dataclass
from .DirectXKeyCodes import KeyCodes


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


@dataclass
class GameInfo:
    MouseControlsEnabled: bool = True
    MouseMovementType: str = 'RELATIVE'

keywords = {
    'jump' : ButtonData(KeyCodes.SPACEBAR),
    'crouch' : ButtonData(KeyCodes.LEFTCONTROL),
    'sit' : ButtonData(KeyCodes.X),
    'use' : ButtonData(KeyCodes.E),
    'walk' : ButtonData(KeyCodes.C)
    }

class MouseControlData:
    keywords = {
        'look left': MouseData(inputType='MOVEMENT', xMovement= -1080),
        'look right': MouseData(inputType='MOVEMENT', xMovement= 1080),
        'attack': MouseData(inputType='BUTTON', button='LEFT'),
        'block': MouseData(inputType = 'BUTTON', button='RIGHT', duration = 3),
        'swap': MouseData(inputType = 'SWAP', duration = 5)
        }


class InputChords:
    keywords = {
        'roll': {MouseData(inputType='BUTTON',button='RIGHT',duration=2), ButtonData(KeyCodes.SPACEBAR)}
        }