from pywinauto import application
from pywinauto import controls
from pywinauto import keyboard
from pywinauto import win32functions
from DirectXKeyCodes import KeyCodes
import KeyCodeInput

DOLPHIN_FILE_PATH = "C:/Program Files/Dolphin/Dolphin.exe"

app = application.Application()

app.start(DOLPHIN_FILE_PATH)

appdel = app.window(title='Dolphin 5.0')

GamesList = appdel['ListViewPaper Mario']

GamesList.get_item(5).select().click('left', True)

TTYDHandle = app.top_window()

time.sleep(9)
PressKey(KeyCodes.SPACEBAR)
time.sleep(.01)
ReleaseKey(KeyCodes.SPACEBAR)

print("pressed it!")

#dlg.child_window(title="SPACE", class_name="Button").click()
#PressKey(0x1)
#time.sleep(1)
#ReleaseKey(0x1)
#dlg.draw_outline()