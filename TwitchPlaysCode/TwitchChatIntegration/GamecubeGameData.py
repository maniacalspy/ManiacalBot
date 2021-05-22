from InputDataClasses import ButtonData
from DolphinControlData import GCKeyBindData as KeyBindData

class KeyWordBindData:
    generickeywords = {
        'a' : ButtonData(button=KeyBindData.KeyBinds['A']),
        'b' : ButtonData(button=KeyBindData.KeyBinds['B']),
        'x' : ButtonData(button=KeyBindData.KeyBinds['X']),
        'y' : ButtonData(button=KeyBindData.KeyBinds['Y']),
        'l' : ButtonData(button=KeyBindData.KeyBinds['LTRIGGER']),
        'r' : ButtonData(button=KeyBindData.KeyBinds['RTRIGGER']),
        'z' : ButtonData(button=KeyBindData.KeyBinds['Z']),
        'start' : ButtonData(button=KeyBindData.KeyBinds['START']),
        'up' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_UP'], duration = 1),
        'long up' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_UP'], duration = 10),
        'light up' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_UP'], duration = .25),
        'right' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_RIGHT'], duration = 1),
        'long right' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_RIGHT'], duration = 10),
        'light right' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_RIGHT'], duration = .25),
        'left' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_LEFT'], duration = 1),
        'long left' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_LEFT'], duration = 10),
        'light left' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_LEFT'], duration = .25),
        'down' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_DOWN'], duration = 1),
        'long down' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_DOWN'], duration = 10),
        'light down' : ButtonData(button=KeyBindData.KeyBinds['LSTICK_DOWN'], duration = .25)
        }
