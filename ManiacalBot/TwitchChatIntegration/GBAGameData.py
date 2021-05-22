from InputDataClasses import ButtonData
from dataclasses import dataclass
from RetroarchControlData import GBAKeyBindData as KeyBindData


class KeyWordBindData:
    generickeywords = {
        'a' : ButtonData(button=KeyBindData.KeyBinds['A']),
        'b' : ButtonData(button=KeyBindData.KeyBinds['B']),
        'l' : ButtonData(button=KeyBindData.KeyBinds['L']),
        'r' : ButtonData(button=KeyBindData.KeyBinds['R']),
        'start' : ButtonData(button=KeyBindData.KeyBinds['START']),
        'select' : ButtonData(button=KeyBindData.KeyBinds['SELECT']),
        'up' : ButtonData(button=KeyBindData.KeyBinds['DPAD_UP'], duration = .25),
        'right' : ButtonData(button=KeyBindData.KeyBinds['DPAD_RIGHT'], duration = .25),
        'left' : ButtonData(button=KeyBindData.KeyBinds['DPAD_LEFT'], duration = .25),
        'down' : ButtonData(button=KeyBindData.KeyBinds['DPAD_DOWN'], duration = .25)
        }

