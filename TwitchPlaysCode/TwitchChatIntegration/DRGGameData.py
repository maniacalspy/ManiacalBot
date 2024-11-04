import GameInputBase
import asyncio
import json
import select
import IntelManager
outFilePath = r"C:\Program Files (x86)\Steam\steamapps\common\Deep Rock Galactic\FSD\Mods\BotOutput.txt"
inFilePath = r"C:\Program Files (x86)\Steam\steamapps\common\Deep Rock Galactic\FSD\Mods\BotInput.txt"

class DRGGameData(GameInputBase.GameInputBase):


    def __init__(self):
        self.reading = True
        self.IntelCosts = {
            "features" : 10,
            "butterfingers" : 10,
            "tipsy": 5
            }
        self.fileKeywords = {
            "doubletime" : self.JSONlamfactory("fastTime"),
            "slowmo" : self.JSONlamfactory("slowTime"),
            "bouncehouse" : self.JSONlamfactory("lowGrav"),
            "chonky" : self.JSONlamfactory("heavyGrav"),
            "tipsy" : IntelManager.IntelCostFunction(self.IntelCosts["tipsy"], DelayCost = True)(self.JSONlamfactory("giveDrink")),
            "features" : IntelManager.IntelCostFunction(self.IntelCosts["features"], DelayCost = True)(self.JSONlamfactory("spawnBugs")),
            "butterfingers": IntelManager.IntelCostFunction(self.IntelCosts["butterfingers"], DelayCost = True)(self.JSONlamfactory("dropNitra")),
            "bigbullets" : self.JSONlamfactory("damageUp"),
            "armorup" : self.JSONlamfactory("healArmor")
            }
        loop = asyncio.get_event_loop()
        loop.create_task(self.fileResponseTask())



    def JSONlamfactory(self,functiontocall):
        return (lambda username, id, Callid = -1: self.WriteAndSendJSON(username = username, id = id, Callid = Callid, function = functiontocall))

    def WriteAndSendJSON(self, username, id, Callid,function):
        JSONToSend = json.dumps({"User":username.lower(), "CallID":Callid, "Function":function})
        loop = asyncio.get_event_loop()
        loop.create_task(self.SendJSON(JSONToSend))
    
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
        if keyword in self.fileKeywords:
            self.fileKeywords[keyword](username = ctx.author.name, id = ctx.author.id)
        #    funcname = self.socketKeywords[keyword]
        #    JSONToSend = json.dumps({"User" : ctx.author.name.lower(), "CallID" : -1, "Function": funcname})
        #    loop = asyncio.get_event_loop()
        #    loop.create_task(self.SendJSON(JSONToSend))
        #elif keyword in self.testKeywords:
        #    print(ctx.author.id)
        #    self.testKeywords[keyword](username = ctx.author.name, id = ctx.author.id)


    async def GetKeywords(self):
        output = []
        for keyword in self.fileKeywords.keys():
            if keyword in self.IntelCosts:
                output.append("{key} ({cost} Intel)".format(key=keyword, cost = self.IntelCosts[keyword]))
            else:
                output.append(keyword)
        return (output)

    async def SendJSON(self, jsonobj):
        global outFilePath
        #encodedmsg = jsonobj.encode()
        file1 = open(outFilePath,"a")
        file1.writelines(jsonobj)
        file1.close()

    async def fileResponseTask(self):
        global inFilePath
        while self.reading:
            myFile = open(inFilePath, "r")
            inText = myFile.read()
            if (inText != ""):
                print(inText)
                processedCommands = [x+"}" for x in inText.split('}') if x!=""]
                for command in processedCommands:
                    test = json.loads(command, object_hook=IntelManager.as_CommandFinishedResponse)
                    if type(test) is IntelManager.CommandFinishedResponse:
                        if test.CallID != -1:
                            await IntelManager.IntelManager.Instance.ResolvePendingCall(test.CallID)
            myFile.close()
            myFile = open(inFilePath, "w")
            myFile.write("")
            myFile.close()
            await asyncio.sleep(.25)