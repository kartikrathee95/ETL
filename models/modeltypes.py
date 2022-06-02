from sqlalchemy.orm import Session
from pydantic import BaseModel, Json
from typing import List, Optional
from datetime import date, datetime
import asyncio


class WatchlistType(BaseModel):
    watchlistid: str
    watchlistarray: List
    earningsEvents: Json
    google_flag: str
    outlook_flag: str
    class Config:
        orm_mode = True
        
class UserAccountType(BaseModel):
    accountId: str
    emailAddress: str
    profileName: str 
    accessToken: str
    provider: str
    nylasCursor: str
    class Config:
        orm_mode = True


class CalendarType(BaseModel):
    calendarId: str
    accountId: str
    name: str
    status: bool
    class Config:
        orm_mode = True


class EventType(BaseModel):
    eventId: str
    calendarId: str
    title: Optional[str]
    desc: Optional[str]
    startTS: datetime
    endTS: datetime
    owner: Optional[str]
    notesIds: List[str]
    parentId: Optional[str]
    status: str
    participants: List[dict]
    icalUid: str
    busy: bool
    location: Optional[str]
    reminders: Optional[dict]
    readOnly: bool

    class Config:
        orm_mode = True


class NylasDataType(BaseModel):
    eventId: str
    data: Json
    status: str

    class Config:
        orm_mode = True


