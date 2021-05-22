from dataclasses import dataclass

@dataclass(frozen = True)
class ButtonData:
    button: int #Keycode you want to send
    duration: float = 0.1


@dataclass(frozen = True)
class MouseData:
    inputType: str = 'BUTTON' #either BUTTON, MOVEMENT, or SWAP
    button: str = 'LEFT' #button to press if type is BUTTON
    xMovement: int = 0 #distance to move on the X-axis if inputType is MOVEMENT
    yMovement: int = 0 #distance to move on the Y-axis if inputType is MOVEMENT
    duration: int = .15 #duration of either the button press or how long the mouse movement takes

@dataclass(init = True, unsafe_hash = True)
class InputChord:
    def __init__(self, ChordList):
        self.InputList = ChordList