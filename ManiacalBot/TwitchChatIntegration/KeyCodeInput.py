import ctypes
import time
import collections


Point = collections.namedtuple("Point", "x y")

winuser = ctypes.windll.user32


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]

SendInput = ctypes.windll.user32.SendInput

PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))



mouse_button_down_mapping = {
    'LEFT': 0x0002,
    'MIDDLE': 0x0020,
    'RIGHT': 0x0008
}

mouse_button_up_mapping = {
    'LEFT': 0x0004,
    'MIDDLE': 0x0040,
    'RIGHT': 0x0010
}


def click_down(button='LEFT', **kwargs):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, mouse_button_down_mapping[button], 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))



def click_up(button='LEFT', **kwargs):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, mouse_button_up_mapping[button], 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def click(button='LEFT', duration=0.05, **kwargs):
    click_down(button=button, **kwargs)
    time.sleep(duration)
    click_up(button=button, **kwargs)


def set_pos(xpos, ypos):
    convertedXPos = 1 + int(xpos * 65536./1920.)
    ConvertedYPos = 1 + int(ypos * 65536./1080.)
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(convertedXPos, ConvertedYPos, 0, (0x0001 | 0x8000), 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def _move_mouse_to_relative(dX, dY):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(dX, dY, 0, (0x0001), 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def move_mouse_relative(dX, dY, duration = .1):
    MINIMUM_SLEEP = .05

    #cursorpoint = position()
    #print('X1 = {a:d}, Y1 = {b:d}'.format(a=cursorpoint.x, b=cursorpoint.y))

    dX = int(dX) if dX is not None else 0
    dY = int(dY) if dY is not None else 0

    num_steps = max(abs(dX), abs(dY))
    sleep_amount = duration / num_steps
    if sleep_amount < MINIMUM_SLEEP:
        num_steps = int(duration / MINIMUM_SLEEP)
        sleep_amount = duration / num_steps

    step = Point(dX // num_steps, dY//num_steps)
    # Making sure the last position is the actual destination.
    for n in range(num_steps):
        _move_mouse_to_relative(step.x, step.y)
        time.sleep(sleep_amount)

    #cursorpoint = position()
    #print('X2 = {a:d}, Y2 = {b:d}'.format(a=cursorpoint.x, b=cursorpoint.y))


def GetInfo():
    thresholds = (ctypes.c_int * 3)()
    speed = (ctypes.c_int*1)()

    ctypes.windll.user32.SystemParametersInfoA(0x003, 0, thresholds, 0)
    ctypes.windll.user32.SystemParametersInfoA(0x0070, 0, speed, 0)

    print('{a:d} - {b:d} - {c:d}'.format(a=thresholds[0], b=thresholds[1], c=thresholds[2]))
    
    print("%d" %speed[0])



def _position():
    cursor = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor))
    return (cursor.x, cursor.y)


def position():
    posx, posy = _position()
    posx = int(posx)
    posy = int(posy)
    return Point(posx, posy)


def SwapMouseButton():
    winuser.SwapMouseButton(ctypes.c_bool(True))
    

def RevertMouseButton():
    winuser.SwapMouseButton(ctypes.c_bool(False))