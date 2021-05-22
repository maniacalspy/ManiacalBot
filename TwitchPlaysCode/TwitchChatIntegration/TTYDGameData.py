from InputDataClasses import ButtonData
from GamecubeGameData import KeyWordBindData
from DolphinControlData import GCKeyBindData

#class TTYDKEYS:
keywords = KeyWordBindData.generickeywords

keywords['jump'] = keywords['a']
keywords['hammer'] = keywords['b']

keywords['hold jump'] = ButtonData(button=GCKeyBindData.KeyBinds['A'], duration = 5)
keywords['hold hammer'] = ButtonData(button=GCKeyBindData.KeyBinds['B'], duration = 5)

keywords['partner'] = keywords['x']
keywords['hold partner'] = ButtonData(button=GCKeyBindData.KeyBinds['X'], duration = 5)
