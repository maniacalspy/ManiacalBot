import GameInputBase
import asyncio
import json
import socket
import select
import IntelManager

HOST = '127.0.0.1'  # The server's hostname or IP address, currently set to localhost address
PORT = 65432        # The port used by the server
PACKET_SIZE = 128   # this can allow you to specify the packet size to send later, but I don't currently use it



class RoR2GameData(GameInputBase.GameInputBase):
    """description of class"""
    def __init__(self):
        self.reading = True
        self.IntelCosts = {
            "movingon" : 25,
            "nailbiter" : 50,
            "nolife" : 25,
            "organize" : 50,
            "ambush": 10
            }
        #this dictionary has the keyword to enter in chat as the key, then stores the lambda function to call as the value.
        self.socketKeywords = {
            "whiteitem" : self.JSONlamfactory("spawnwhite"),
            "greenitem" : self.JSONlamfactory("spawngreen"),
            "reditem" : self.JSONlamfactory("spawnred"),
            "blueitem" : self.JSONlamfactory("spawnlunar"),
            "pinkitem" : self.JSONlamfactory("spawnvoid"),
            "anyitem" : self.JSONlamfactory("spawnany"),
            "equipment" : self.JSONlamfactory("spawnequip"),
            "yoink" : self.JSONlamfactory("removeitem"),
            "slow" : self.JSONlamfactory("applyslow"),
            "weak" : self.JSONlamfactory("applyweak"),
            "overheat" : self.JSONlamfactory("applyoverheat"),
            "hobble" : self.JSONlamfactory("applyhobble"),
            "takemoney" : self.JSONlamfactory("takemoney"),
            "givemoney" : self.JSONlamfactory("givemoney"),
            "heal" : self.JSONlamfactory("heal"),
            "movingon" : IntelManager.IntelCostFunction(self.IntelCosts["movingon"], DelayCost = True)(self.JSONlamfactory("nextstage")), #the first part of these entries go through a manager class for my rewards points system
            "nailbiter" : IntelManager.IntelCostFunction(self.IntelCosts["nailbiter"], DelayCost = True)(self.JSONlamfactory("OneHP")),   #it essentially just generates a call ID so I can track when an individual redemption has gone through to properly subtract points
            "organize" : IntelManager.IntelCostFunction(self.IntelCosts["organize"], DelayCost = True)(self.JSONlamfactory("OrderInventory")), #but those calls are just a wrapper around the same lambda generator function the other keywords use
            "nolife" : IntelManager.IntelCostFunction(self.IntelCosts["nolife"], DelayCost=True)(self.JSONlamfactory("HideHP")),
            "ambush" : IntelManager.IntelCostFunction(self.IntelCosts["ambush"], DelayCost=True)(self.JSONlamfactory("Ambush"))
            }
        #put secret testing keywords in here for me for debugging
        self.testKeywords = {
            "test" : self.JSONlamfactory("testcommand"),
            "inteltest" : IntelManager.IntelCostFunction(0, DelayCost = True)(self.JSONlamfactory("testcommand"))
            }
        #connect to the socket opened by the game mod
        self.mysock = socket.create_connection((HOST,PORT))
        loop = asyncio.get_event_loop()
        loop.create_task(self.SocketResponseTask())

    #this creates the lambda functions that are the value in the socketKeywords dictionary, this lamba essentially just creates the JSON object to be sent over the socket
    def JSONlamfactory(self,functiontocall):
        return (lambda username, id, Callid = -1: self.WriteAndSendJSON(username = username, id = id, Callid = Callid, function = functiontocall))

    #create the JSON object to send over the websocket, essentially just stores the username and a call ID so I know when my rewards points functions have finished calling so I can subtract the points
    #the function argument is the internal name used to call the function in the game mod, which can be a different than the chat keyword
    #the "id" keyword argument is there for the wrapper function for my rewards points, hence why it isn't used in this function itself
    def WriteAndSendJSON(self, username, id, Callid,function):
        JSONToSend = json.dumps({"User" : username.lower(), "CallID": Callid, "Function": function})
        loop = asyncio.get_event_loop()
        loop.create_task(self.SendJSON(JSONToSend))
    
    #this is called by the chat bot itself so that I can have the !keywords command in chat that adapts when I change what game I'm having the bot read
    async def GetKeywords(self):
        output = []
        for keyword in self.socketKeywords.keys():
            if keyword in self.IntelCosts:
                output.append("{key} ({cost} Intel)".format(key=keyword, cost = self.IntelCosts[keyword]))
            else:
                output.append(keyword)
        return (output)


    #This is the driver function of this class, the bot passes the chat message here and it handles the actual logic
    async def HandleKeyword(self, ctx):
        #this try-except is here because the library I use for Twitch's API keeps changing their formatting on me
        try:
            keyword = ctx.content.strip(' ').lower()
        except:
            keyword = ctx

        #if the chat message is in the keywords dictionary, call the lambda function with the username and internal twitch user ID (so that name changes don't break my rewards points)
        if keyword in self.socketKeywords:
            self.socketKeywords[keyword](username = ctx.author.name, id = ctx.author.id)

   
    #this function sends the JSON object over the socket so the game mod can interpret it
    async def SendJSON(self, jsonobj):
        #print(jsonobj)
        #encode the JSON and get the packet size
        encodedmsg = jsonobj.encode()
        msgSize = len(encodedmsg)
        #print('\tPacket Size: ' + str(msgSize))
        #send 2 messages over the socket, the first being the size of the next message (that integer is always 1 byte, so no JSON objects longer than 255 characters) so the mod doesn't accidentally start reading the next command
        #then send the actual JSON object representing the command
        self.mysock.sendall(msgSize.to_bytes(1, 'big'))
        self.mysock.sendall(encodedmsg)
        #print(encodedmsg)

        #game mod sends a response object in a similar style, first the message size, then the message
        #however, the 2 here is not 2 bytes, since the other library sends the number as a string and not a byte, the 2 here reads the first 2 characters on the socket (so reply messages are always between 10 and 99 characters)
        #then receive the message itself, this message is essentially a confirmation that we got the JSON object
        size = self.mysock.recv(2)
        data = self.mysock.recv(int(size))
        print('Received', str(data, 'utf-8'))

        #this is a safety valve in case we have multiple commands being processed, if the socket was trying to send that a command finished
        #rather than getting the confirmation message we'd get a commandFinished message, and we need to process that here
        if data:
            if data != -1:
                test = json.loads(data, object_hook=IntelManager.as_CommandFinishedResponse)
                if type(test) is IntelManager.CommandFinishedResponse:
                    if test.CallID != -1:
                        await IntelManager.IntelManager.Instance.ResolvePendingCall(test.CallID)

    async def TearDown(self):
        self.mysock.close()

    #run this in a loop to check the socket for any function calls that have finished
    async def SocketResponseTask(self):
        #while the socket is running
        while self.reading:
            #from select library, if the socket is ready to read, it will go in the ready_to_read array
            ready_to_read, ready_to_write, in_error = \
                   select.select(
                    [self.mysock],
                      [],
                      [],
                      .1)
            #this currently only reads the one socket, but it should be set up to read from more if need be
            for sock in ready_to_read:
                if sock == self.mysock:
                    #check message size, if we get nothing, break out of the loop and check again in .25 seconds
                    size = sock.recv(2)
                    if not size:
                        break;
                    #check for data
                    data = sock.recv(int(size))
                    if not data:
                        break;
                    else:
                        #if the message from the socket is -1, it means we want to close the socket, otherwise we have a message
                        if data != -1:
                            #check the response object, the JSON reply object is essentially a struct with the username and the call ID as the only 2 fields
                            #all non-rewards redemptions have a CallID of -1, and as such don't need any other processing other than removing them from the socket
                            test = json.loads(data, object_hook=IntelManager.as_CommandFinishedResponse)
                            if type(test) is IntelManager.CommandFinishedResponse:
                                if test.CallID != -1:
                                    await IntelManager.IntelManager.Instance.ResolvePendingCall(test.CallID)
                        else:
                            self.reading = False
            await asyncio.sleep(.25)
