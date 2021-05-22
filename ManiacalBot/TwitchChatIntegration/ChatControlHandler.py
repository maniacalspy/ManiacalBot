import asyncio
import InputDataClasses


async def HandleIntegration(self, ctx):
    message = ctx.content.strip(' ').lower()

    #if self.GameTitle == "test":
    #    if message == "look left":
    #        await SendTestMouseInput(-480,0)
    #    elif message == "look right":
    #        await SendTestMouseInput(480,0)
    #    elif len(message) == 1 or message in pyautogui.KEYBOARD_KEYS:
    #        await SendTestKeyInput(message)
    #    elif message == "space":
    #        await SendKeyInputDuration(' ', 1)
    #    elif message == "click":
    #        await SendTestMouseClick()
    #    elif message == "swap":
    #        await SendMouseButtonSwap()
    #    elif message == "info":
    #        await PrintMouseInfo()

    #elif(self.GameTitle == "BeatBars"):
    #    if message == 'up' or message == 'north':
    #        self.chat_data[ctx.author.name] = 'north'
    #    elif message == 'down' or message == 'south':
    #        self.chat_data[ctx.author.name] = 'south'
    #    elif message == 'right' or message == 'east':
    #        self.chat_data[ctx.author.name] = 'east'
    #    elif message == 'left' or message == 'west':
    #        self.chat_data[ctx.author.name] = 'west'

    #else:
    #IF UNCOMMENTING THE ABOVE, INCREASE LINE INDENT FOR THE FOLLOWING
    if message in GameInputData.keywords:
        InputData = GameInputData.keywords[message]
        await SendKeyInputDuration(Key = InputData.button, duration = InputData.duration)
    else:
        try:
            if GameInputData.GameInfo.MouseControlsEnabled:
                if message in GameInputData.MouseControlData.keywords:
                    MouseData = GameInputData.MouseControlData.keywords[message]
                    await self.HandleMouseInput(MouseData)
                else:
                    try:
                        if message in GameInputData.InputChords.keywords:
                            for item in GameInputData.InputChords.keywords[message]:
                                if item.__class__ is InputDataClasses.MouseData:
                                    loop = asyncio.get_event_loop()
                                    loop.create_task(self.HandleMouseInput(item))
                                elif item.__class__ is InputDataClasses.ButtonData:
                                    loop = asyncio.get_event_loop()
                                    loop.create_task(SendKeyInputDuration(Key = item.button, duration = item.duration))
                                else:
                                    print(item.__class__)
                    except Exception as e:
                        print(e)
                        pass
        except Exception as e:
            print(e)
            pass





async def ImportKeyCodeData(title):
    modulename = "KeyCodeInput"
    global Input, GameInputData
    if modulename not in sys.modules:
        spec = importlib.util.find_spec(modulename)
        if spec is not None:
            Input = importlib.import_module(modulename)
    else:
        Input = sys.modules[modulename]
        
    GameData = title + "GameData"
    if GameData not in sys.modules:
        spec = importlib.util.find_spec(GameData)
        if spec is not None:
            GameInputData = importlib.import_module(GameData)
    else:
        GameInputData = sys.modules[GameData]

async def SendKeyInput(Key):
    try:
        Input.PressKey(Key)
        await asyncio.sleep(.01)
        Input.ReleaseKey(Key)
    except e:
        print(e)

async def SendKeyInputDuration(Key, duration):
    try:
        Input.PressKey(Key)
        await asyncio.sleep(duration)
        Input.ReleaseKey(Key)
    except e:
        print(e)


async def SendTestKeyInput(Key):
    pyautogui.press(Key)


async def SendTestKeyInputDuration(Key, duration):
    pyautogui.keyDown(Key)
    await asyncio.sleep(duration)
    pyautogui.keyUp(Key)


@rate_limited(2,mode='kill')
async def SendMouseMoveInput(X,Y,duration):
    #pyautogui.moveTo(X,Y,.5,pyautogui.easeOutQuad)
    #Input.set_pos(X,Y)
    Input.move_mouse_relative(X,Y,duration)

async def SendMouseClick(button, duration):
    #pydirectinput.click()
    #pydirectinput.press('esc')
    #await SendKeyInput(0x100)
    Input.click(button, duration)
