import sqlite3, sys
from itertools import chain
from collections import namedtuple
import random
import datetime

sql_connect = None
cursor = None

QuoteData = namedtuple('Quote', ('id', 'text'))
IntelUser = namedtuple('Intel', ('id', 'points'))
class FollowData:
    """
    The Data about a user following that gets passed to an SQL server

    Attributes
    -------------------
    name : str
        the username of the follower
    id : int
        the follower's user ID
    followDate : :class:`.datetime`
        The datetime that the user first followed

    """

    __slots__ = ('_id', '_name', '_followDate')

    def __init__(self, id: int, name: str, followDate: datetime):
        self._id = id
        self._name = name
        self._followDate = followDate


    def __str__(self):
        return f'{self._id}, {self._name}, {self._followDate}'


    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        """The user's name."""
        return self._name

    @property
    def followDate(self) -> datetime:
        return self._followDate


def Setup():
    global sql_connect
    sql_connect = sqlite3.connect('C:/Users/Nolan/Desktop/ManiacalBot/ManiacalBot/SQLData/ManiacalBotData.db')
    if sql_connect is not None:
        global cursor
        cursor = sql_connect.cursor()


def Teardown():
    sql_connect.close()

#Following
#region Follow
def AddFollowEntry(Data: FollowData):
    global cursor, sql_connect
    query = '''INSERT INTO FollowData(id, name, followdate) VALUES(?,?,?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name;'''
    try:
        cursor.execute(query, (Data.id, Data.name, Data.followDate.isoformat()))
        sql_connect.commit()        
    except:
       print('Something went wrong')


#endregion Follow

#Suggestions
#region Suggestions
def AddSuggestionEntry(suggestion: str):
    global cursor, sql_connect
    query = '''INSERT OR IGNORE INTO Suggestions(Suggestion) VALUES(?);'''
    cursor.execute(query, [suggestion])
    sql_connect.commit()
#endregion Suggestions

#Quotes
#region Quotes
def AddQuoteEntry(quote: str):
    global cursor, sql_connect
    query = '''INSERT OR IGNORE INTO Quotes(quote) VALUES(?);'''
    cursor.execute(query, [quote])
    sql_connect.commit()

async def GetQuote(id = None) -> QuoteData:
    global cursor, sql_connect
    if (id == None):
        countResponse = int((cursor.execute('''SELECT COUNT(*) FROM Quotes;''').fetchone())[0])
        selection = random.randint(1,countResponse)
    else:
       selection = id
    Query = f'''SELECT rowid, quote FROM Quotes WHERE rowid={selection}'''
    quote = cursor.execute(Query).fetchone()
    if (quote is not None):
       return QuoteData(*quote)

#endregion Quotes

#ChatCommands
#region ChatCommands
async def AddChatCommand(commandName: str, botResponse: str):
    global cursor, sql_connect
    
    query = '''INSERT INTO AddedCommands(name, response) VALUES(?,?)
    ON CONFLICT(name)
    DO UPDATE SET response=?'''
    
    cursor.execute(query, [commandName, botResponse, botResponse])
    sql_connect.commit()

async def AddCountCommand(commandClass):
    global cursor, sql_connect

    query = '''INSERT INTO CountingCommands(Name, CommandText, CommandCount) VALUES(?,?,?)
    ON CONFLICT(name)
    DO UPDATE SET CommandText=?, CommandCount=?'''
    
    cursor.execute(query, [commandClass.name, commandClass.text, commandClass.count, commandClass.text, commandClass.count])
    sql_connect.commit()

async def GetChatCommands():
    global cursor, sql_connect

    query = '''SELECT * FROM AddedCommands'''
    commands = cursor.execute(query).fetchall()
    return commands

async def GetCountCommands():
    global cursor, sql_connect

    query = '''SELECT * FROM CountingCommands'''
    commands = cursor.execute(query).fetchall()
    return commands

async def DeleteChatCommand(commandName: str):
    global cursor, sql_connect

    query = '''DELETE FROM AddedCommands WHERE name = ?'''

    cursor.execute(query, [commandName])
    sql_connect.commit()
#endregion ChatCommands

#Intel
#region Intel
async def EnlistUsers(*users: IntelUser):
    global cursor, sql_connect
    query = '''INSERT OR IGNORE INTO IntelUsers(id,points) VALUES'''
    if(len(users) > 0):
        for i in range(len(users)):
            query+='''(?,?)'''
            if(i < len(users)-1): query+= ''','''
        query+=''';'''
        cursor.execute(query, list(chain.from_iterable((user.id, user.points) for user in users)))
        sql_connect.commit()

async def UpdateIntelUsers(userdata: list):
    global cursor, sql_connect
    users = [item for item in userdata]
    query = '''INSERT INTO IntelUsers (id, points) VALUES(?, ?) 
    ON CONFLICT(id) 
    DO UPDATE SET points=excluded.points;'''
    for user in users:
        cursor.execute(query, (user.id, user.points))
    sql_connect.commit()

async def GetIntelUser(userid:int):
    global cursor, sql_connect
    try:
        query = '''SELECT * FROM IntelUsers WHERE id = ?;'''
        user = cursor.execute(query, [userid]).fetchone()
        if(user is not None):
            UserData = IntelUser(user[0],user[1])
            return UserData
        else: return None
    except Exception as e:
        print(e)
#endregion Intel