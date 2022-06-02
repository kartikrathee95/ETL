from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from sqlalchemy import BOOLEAN, Table, Column, Integer, ForeignKey, MetaData, ARRAY, String, JSON
import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from NylasIntegration.models.conn import SessionLocal, Base, drop_tables
from NylasIntegration.models.modeltypes import (
    WatchlistType,
    EventType,
    NylasDataType,
    UserAccountType,
    CalendarType,
)
from datetime import datetime
import pytz
import requests
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from typing import List
from sqlalchemy import select, update, delete, text

sess = SessionLocal()

CLIENT_ID = "9skwzkne2afs80ux1w8p3vnv4"
CLIENT_SECRET = "97n4taetonhk6jqyn8z9z8j4v"

ACCESS_TOKEN = "Oyq7gxqGqOWR3nTJyuaGTPzJ7yKodc"


class WatchLists(Base):
    __tablename__ = "watchlists"
    __table_args__ = {"extend_existing": True}
    watchlistid = Column(
        "watchlistid", sqlalchemy.VARCHAR, primary_key=True, index=True, unique=True
    )
    
    watchlistarray = Column("watchlistarray",ARRAY(String))
    earningsevents = Column("earningsevents",JSON,nullable=True)
    google_flag = Column("google_flag",sqlalchemy.VARCHAR)
    outlook_flag = Column("outlook_flag",sqlalchemy.VARCHAR)
    


    def __init__(
        self, watchlistid, watchlistarray, earningsevents, google_flag, outlook_flag
    ):
        self.watchlistid = watchlistid
        self.watchlistarray= watchlistarray
        self.earningsevents = earningsevents
        self.google_flag = google_flag
        self.outlook_flag = outlook_flag

    @staticmethod
    def getwatchlistarray():
        query = text("SELECT * FROM watchliststemp_orary")
        res = sess.execute(query).first()
        return res

    @staticmethod
    def addWatchlist(activeWatchlists,watchlistId,earningsevents, google_flag, outlook_flag):

        try:
            sess.execute(delete(WatchLists))
            sess.commit()
        except Exception as e:
            sess.rollback() 
     
        
        watchlist: WatchlistType = {'watchlistid': watchlistId, 'watchlistarray': activeWatchlists,'earningsevents':earningsevents,'google_flag':google_flag, 'outlook_flag':outlook_flag}
        sess.add(WatchLists(**watchlist))
        sess.commit()       
    
    @staticmethod
    def deleteWatchlists(watchlistid: str):
        
        try:
            sess.execute(delete(WatchLists))
            sess.commit()
        except Exception as e:
            sess.rollback() 
        
class UserAccount(Base):
    __tablename__ = "user_accounts"
    __table_args__ = {"extend_existing": True}
    accountId = Column(
        "account_id", sqlalchemy.VARCHAR, primary_key=True, index=True, unique=True
    )
    userId = Column("user_id", sqlalchemy.VARCHAR, index=True)
    profileName = Column("profile_name", sqlalchemy.VARCHAR)
    emailAddress = Column("email_address", sqlalchemy.VARCHAR)
    accessToken = Column("access_token", sqlalchemy.VARCHAR)
    provider = Column("provider", sqlalchemy.VARCHAR)
    nylasCursor = Column("nylas_cursor", sqlalchemy.VARCHAR)
    createdAt = Column("created_at", sqlalchemy.DateTime, server_default=func.now())
    calendars = relationship(
        "Calendar", backref="user_accounts", cascade="all, delete-orphan"
    )

    def __init__(
        self, accountId, userId, profileName, emailAddress, accessToken, provider, nylasCursor,
    ):
        self.accountId = accountId
        self.userId = userId
        self.profileName = profileName
        self.emailAddress = emailAddress
        self.accessToken = accessToken
        self.provider = provider
        self.nylasCursor = nylasCursor

    def __repr__(self):
        return str(jsonable_encoder(self))

    @staticmethod
    def getAll():
        return sess.execute(select(UserAccount)).scalars().all()

    @staticmethod
    def getAccount(accountId: str):
        return sess.execute(select(UserAccount).where(UserAccount.accountId==accountId)).scalar_one_or_none()

    @staticmethod
    def addAccount(account: UserAccountType):
        present = UserAccount.getAccount(account.get('accountId'))
        if not present:
            try:
                sess.add(UserAccount(**account))
                sess.commit()
            except Exception as e:
                sess.rollback()
        else:
            UserAccount.updateAccount(account)

    @staticmethod
    def updateAccount(account: UserAccountType):
        accountDic={**account}
        del accountDic["accountId"]
        try:
            sess.execute(update(UserAccount).where(UserAccount.accountId == account.get('accountId')).values( accountDic ))
            sess.commit()
        except Exception as e:
            sess.rollback()

    @staticmethod
    def filterByUser(userId: str):
        return sess.execute(select(UserAccount).where(UserAccount.userId == userId)).scalars().all()

    @staticmethod
    def getLastCreatedAt(userId: str):
        return sess.execute(select(UserAccount).where(UserAccount.userId==userId).order_by(UserAccount.createdAt.desc())).scalars().first()

    @staticmethod
    def filterByEmailAddress(email: str):
        return sess.execute(select(UserAccount).where(UserAccount.emailAddress==email)).scalar_one_or_none()

    @staticmethod
    def deleteAccount(accountId: str):
        account = UserAccount.getAccount(accountId)
        if account != None:
            try:
                sess.execute(delete(UserAccount).where(UserAccount.accountId==accountId))
                sess.commit()
            except Exception as e:
                sess.rollback()


class Calendar(Base):
    __tablename__ = "calendars"
    __table_args__ = {"extend_existing": True}
    calendarId = Column(
        "calendar_id", sqlalchemy.VARCHAR, primary_key=True, index=True, unique=True
    )
    accountId = Column(
        "account_id",
        sqlalchemy.VARCHAR,
        ForeignKey("user_accounts.account_id", ondelete="cascade"),
        unique=False,
        index=True,
    )
    name = Column("name", sqlalchemy.VARCHAR)
    status = Column("status", sqlalchemy.Boolean)
    events = relationship("Event", backref="calendars", cascade="all, delete-orphan")

    def __init__(self, calendarId, accountId, name, status) -> None:
        self.calendarId = calendarId
        self.accountId = accountId
        self.name = name
        self.status = status

    def __repr__(self):
        return str(jsonable_encoder(self))

    @staticmethod
    def getAll():
        return sess.execute(select(Calendar)).scalars().all()

    @staticmethod
    def filterByAccountWiz(accountId: str):
        return sess.execute(select(Calendar).where(Calendar.accountId == accountId, Calendar.name !="Earnings Calendar")).scalars().all()
 
    @staticmethod
    def filterByAccount(accountId: str):
        return sess.execute(select(Calendar).where(Calendar.accountId == accountId, Calendar.name !="Earnings Calendar", Calendar.status==True)).scalars().all()

    @staticmethod
    def getCalendar(calendarId: str):
        return sess.execute(select(Calendar).where(Calendar.calendarId==calendarId)).scalar_one_or_none()

    @staticmethod
    def addCalendar(calendar: CalendarType):
        present = Calendar.getCalendar(calendar["calendarId"])
        if not present:
            try:
                sess.add(Calendar(**calendar))
                sess.commit()
            except Exception as e:
                sess.rollback()
        else:
            Calendar.updateCalendar(calendar)

    @staticmethod
    def updateCalendar(calendar: CalendarType):
        calendarDic={**calendar}
        del calendarDic["calendarId"]
        try:
            sess.execute(update(Calendar).where(Calendar.calendarId== calendar.get('calendarId')).values( calendarDic ))
            sess.commit()
        except Exception as e:
            sess.rollback()

    @staticmethod
    def deleteCalendar(calendarId: str):
        calendar = Calendar.getCalendar(calendarId)
        if calendar != None:
            try:
                sess.execute(delete(Calendar).where(Calendar.calendarId==calendarId))
                sess.commit()
            except Exception as e:
                sess.rollback()


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"extend_existing": True}
    eventId = Column(
        "event_id", sqlalchemy.VARCHAR, primary_key=True, index=True, unique=True
    )
    calendarId = Column(
        "calendar_id",
        sqlalchemy.VARCHAR,
        ForeignKey("calendars.calendar_id", ondelete="cascade"),
        unique=False,
        index=True,
    )
    title = Column("title", sqlalchemy.String)
    desc = Column("desc", sqlalchemy.String)
    startTS = Column("start_ts", sqlalchemy.DateTime)
    endTS = Column("end_ts", sqlalchemy.DateTime)
    owner = Column("owner", sqlalchemy.VARCHAR)
    notesIds = Column("notes_ids", sqlalchemy.ARRAY(sqlalchemy.VARCHAR))
    parentId = Column("parent_id", sqlalchemy.VARCHAR)
    status = Column("status", sqlalchemy.VARCHAR)
    participants = Column("participants", sqlalchemy.ARRAY(sqlalchemy.JSON))
    icalUid = Column("ical_uid", sqlalchemy.VARCHAR)
    busy = Column("busy", sqlalchemy.BOOLEAN)
    location = Column("location", sqlalchemy.VARCHAR)
    reminders = Column("reminders", sqlalchemy.JSON)
    readOnly = Column("read_only", sqlalchemy.BOOLEAN)
    nylasData = relationship("NylasData", backref="events", cascade="all, delete-orphan")
    
    def __repr__(self):
        return str(jsonable_encoder(self))

    def __init__(
        self,
        eventId,
        calendarId,
        title,
        desc,
        startTS,
        endTS,
        owner,
        notesIds,
        status,
        parentId,
        participants,
        icalUid,
        busy,
        location,
        reminders,
        readOnly
    ):
        self.eventId = eventId
        self.calendarId = calendarId
        self.title = title
        self.desc = desc
        self.startTS = startTS
        self.endTS = endTS
        self.owner = owner
        self.notesIds = notesIds
        self.status = status
        self.parentId = parentId
        self.participants = participants
        self.icalUid = icalUid
        self.busy = busy
        self.location = location
        self.reminders = reminders
        self.readOnly = readOnly

    @staticmethod
    def getAll():
        return sess.execute(select(Event).where(Event.status == "confirmed")).scalars().all()

    @staticmethod
    def getEvent(eventId: str):
        return sess.execute(select(Event).where(Event.eventId==eventId)).scalar_one_or_none()

    @staticmethod
    def getEvents(eventIds:List[str]):
        return sess.execute(select(Event).where(Event.eventId.in_(eventIds))).scalars().all()

    @staticmethod
    def addEvent(event: EventType):
        present = Event.getEvent(event["eventId"])
        if not present:
            try:
                sess.add(Event(**event))
                sess.commit()
            except Exception as e:
                sess.rollback()
        else:
            Event.updateEvent(event)

    @staticmethod
    def otherIcalStartTS(icalUid: str, startTS: datetime):
        try:
            return sess.execute(select(Event).where(Event.icalUid == icalUid, Event.startTS == startTS)).scalars().all()
        except Exception as e:
            sess.rollback()

    @staticmethod
    def addBulkEvents(events: List[EventType]):
        try:
            sess.bulk_insert_mappings(Event, events)
            sess.commit()
        except Exception as e:
            sess.rollback()
    
    @staticmethod
    def updateEvent(event: EventType):
        eventDic={**event}
        del eventDic["eventId"]
        try:
            sess.execute(update(Event).where(Event.eventId == event.get('eventId')).values( eventDic ))
            sess.commit()
        except Exception as e:
            sess.rollback()

    @staticmethod
    def addNote(eventId: str, noteId: str):
        event: EventType = sess.query(Event).get(eventId)
        event.notesIds.append(noteId)
        try:
            if event.parentId != None or event.parentId != "None":
                sess.execute(update(Event).where(Event.parentId == event.parentId).values({Event.notesIds: event.notesIds}))
                sess.commit()
            else:
                sess.execute(update(Event).where(Event.eventId == event.eventId).values({Event.notesIds: event.notesIds}))
                sess.commit()
        except Exception as e:
            sess.rollback()
        return event

    @staticmethod
    def filterByCalendarsTs(calendarIds: List[str], startTS: datetime, endTS: datetime):
        return sess.execute(select(Event).where(Event.calendarId.in_(calendarIds), Event.startTS >= startTS,
                Event.startTS <= endTS,
                Event.status == "confirmed")).scalars().all()

    @staticmethod
    def filterByCalendars(calendarIds: List[str]):
        return sess.execute(select(Event).where(Event.calendarId.in_(calendarIds))).scalars().all()

    @staticmethod
    def deleteByCalendars(calendarIds: List[str]):
        sess.execute(delete(Event).where(Event.calendarId.in_(calendarIds)))
        sess.commit()
        
    @staticmethod
    def getEventsinTS(startTS: datetime, endTS: datetime, calendarId: str):
        return (
            sess.execute(select(Event).where(Event.startTS >= startTS,
                Event.startTS <= endTS,
                Event.status == "confirmed",
                Event.calendarId == calendarId,)).scalars().all()
        )

    @staticmethod
    def deleteBulkEvents(eventIds: List[str]):
        try:
            sess.execute(delete(Event).where(Event.eventId.in_(eventIds)))
            sess.commit()
        except Exception as e:
            sess.rollback()

    @staticmethod
    def deleteEvent(eventId: str):
        event = Event.getEvent(eventId)
        if event != None:
            try:
                sess.execute(delete(Event).where(Event.eventId==eventId))
                sess.commit()
            except Exception as e:
                sess.rollback()


class NylasData(Base):
    __tablename__ = "nylas_data"
    __table_args__ = {"extend_existing": True}
    eventId =  Column(
        "event_id",
        sqlalchemy.VARCHAR,
        ForeignKey("events.event_id", ondelete="cascade"),
        unique=True,
        index=True,
        primary_key=True
    )
    data = Column("data", sqlalchemy.JSON)
    status = Column("status", sqlalchemy.VARCHAR)
    createdAt = Column("created_at", sqlalchemy.DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return str(jsonable_encoder(self))

    def __init__(self, eventId, data, status):
        self.eventId = eventId
        self.data = data
        self.status = status

    @staticmethod
    def getAll():
        return sess.execute(select(NylasData)).scalars().all()

    @staticmethod
    def getNylasData(eventId: str):
        return sess.execute(select(NylasData).where(NylasData.eventId==eventId)).scalar_one_or_none()

    @staticmethod
    def addNylasData(event: NylasDataType):
        present = NylasData.getNylasData(event["eventId"])
        if not present:
            try:
                sess.add(NylasData(**event))
                sess.commit()
            except Exception as e:
                sess.rollback()
        else:
            NylasData.updateNylasData(event)

    @staticmethod
    def addBulkNylasData(events: List[NylasDataType]):
        try:
            sess.bulk_insert_mappings(NylasData, events)
            sess.commit()
        except Exception as e:
            sess.rollback()

    @staticmethod
    def updateNylasData(event: NylasDataType):
        nylasDic={**event}
        del nylasDic["eventId"]
        try:
            sess.execute(update(NylasData).where(NylasData.eventId == event.get('eventId')).values( nylasDic ))
            sess.commit()
        except Exception as e:
            sess.rollback()


# drop_tables()

# nylas = APIClient(
#                 CLIENT_ID,
#                 CLIENT_SECRET,
#                 ACCESS_TOKEN
#             )


# def process_accounts():
#     latest_cursor = requests.post(
#                     "https://api.nylas.com/delta/latest_cursor", headers=({"Authorization": "Bearer "+ACCESS_TOKEN})
#             )
#     cursor=latest_cursor.json()["cursor"]
#     UserAccount.addAccount({'accountId':nylas.account.account_id, 'userId':'61a7195428387f0b9fc737b9', 'accessToken': 'Oyq7gxqGqOWR3nTJyuaGTPzJ7yKodc', 'emailAddress' : nylas.account.email_address, 'provider': nylas.account.provider, 'nylasCursor': cursor})

# def process_calendars():
#     calendarlist=[]
#     curr_calendars=requests.get(
#                     "https://api.nylas.com/calendars",headers=({"Authorization": "Bearer "+ ACCESS_TOKEN })
#                     ).json()[0]
#     for curr_calendar in curr_calendars:
#         if UserAccount.getAccount(curr_calendar['account_id']) != None:
#             calendarlist.append({'calendarId':curr_calendar['id'], 'accountId':curr_calendar['account_id'], 'name':curr_calendar['name']})

#     for calendar in calendarlist:
#         Calendar.addCalendar(calendar)

# def process_events(startTimestamp, endTimestamp):
#     eventlist=[]
#     nylaslist=[]
#     curr_events=requests.get(
#                     "https://api.nylas.com/events/", params={'starts_after': startTimestamp,'ends_before':endTimestamp,'expand_recurring':True},headers=({"Authorization": "Bearer "+ACCESS_TOKEN })
#                     ).json()

#     for curr_event in curr_events:
#         parent_id="None"
#         startTS=-1
#         endTS=-1
#         if 'master_event_id' in curr_event.keys():
#             parent_id=curr_event['master_event_id']

#         if 'start_time' in curr_event['when'].keys():
#             startTS=int(curr_event['when']['start_time'])

#         if 'end_time' in curr_event['when'].keys():
#             endTS=int(curr_event['when']['end_time'])

#         if 'start_date' in curr_event['when'].keys():
#             startTS= int(datetime.timestamp(datetime.strptime(curr_event['when']['start_date'],"%Y-%m-%d").astimezone(pytz.utc)))

#         if 'end_date' in curr_event['when'].keys():
#             endTS= int(datetime.timestamp(datetime.strptime(curr_event['when']['end_date'],"%Y-%m-%d").astimezone(pytz.utc)))

#         if 'date' in curr_event['when'].keys():
#             startTS= int(datetime.timestamp(datetime.strptime(curr_event['when']['date'],"%Y-%m-%d").astimezone(pytz.utc)))

#         status=curr_event['status']
#         eventlist.append({'eventId':curr_event['id'],'calendarId':curr_event['calendar_id'], 'title':curr_event['title'], 'desc': curr_event['description'],
#          'owner':curr_event['owner'], 'participants': curr_event['participants'], 'parentId':parent_id, 'startTS': startTS, 'endTS': endTS, 'notesIds':[] })

#         nylaslist.append({'eventId':curr_event['id'],'data':curr_event, 'status':status})

#     for event in eventlist:
#         Event.addEvent(event)

#     for nylas in nylaslist:
#         NylasData.addNylasData(nylas)


# process_accounts()
# process_calendars()
# process_events(1618022348,1641782348)

# print(Event.addNote('1liv5131jtnxq37qm7bkt8d8e_20210818T150000Z','note123'))

# add_accounts()
# add_calendar()
# add_event()
# add_nylas()


# sess.close()
