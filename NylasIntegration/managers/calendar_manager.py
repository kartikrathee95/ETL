from fastapi.encoders import jsonable_encoder
from config import settings
import aiohttp
from NylasIntegration.models.models import NylasData, UserAccount, Event, Calendar
from NylasIntegration.models.modeltypes import CalendarType, EventType, UserAccountType
from NylasIntegration.managers.nylas_manager import (
    connect_nylas_token,
    get_nylas_calendars,
    get_nylas_register_events,
)
from datetime import datetime, timedelta
from typing import List
import traceback
from kafka_logger import logger

async def get_notebook_note(note_id, usId) -> dict:
    cookies = {"usid": str(usId)}
    note_id = str(note_id)
    r = None
    try:
        async with aiohttp.ClientSession() as session:
            env = "local"
            if settings.DOMAIN == "testing":
                env = "testing"
            else:
                env = "local"
            async with session.get(
                f"https://user-{env}.sentieo.com/api/get_note_html/?id={note_id}&first_get=1&team_hl=true&query_analysis=false",
                cookies=cookies,
            ) as response:
                r = await response.json()
        if r["result"]["active"] == 1:
            return {
                "deleted": 0,
                "exception": 0,
                "title": str(r["result"]["title"]),
                "owner": str(r["result"]["owner"]),
                "note_id": str(note_id),
            }
        else:
            return {"deleted": 1, "exception": 0}
    except:
        logger.error("Exception occured in get_notebook_note {0}".format(str(traceback.format_exc())))
        return {"deleted": 0, "exception": 1}


async def fetch_bulk_notes(event_ids, cookies):
    event_dict = {}
    try:
        for event_id in event_ids:
            curr_event = Event.getEvent(event_id)
            if curr_event != None:
                present_notes = curr_event.notesIds
                bulk_notes = []
                for note_id in present_notes:
                    curr_sentieo_note = await get_notebook_note(note_id, cookies["usid"])
                    if (
                        curr_sentieo_note["deleted"] == 0
                        and curr_sentieo_note["exception"] == 0
                    ):
                        bulk_notes.append(jsonable_encoder(curr_sentieo_note))

                event_dict[event_id] = bulk_notes
    except Exception as e:
        logger.error("Exception occured in fetch_bulk_notes {0}".format(str(traceback.format_exc())))

    return event_dict


def fetch_bulk_events(calendar_ids: List[str], start_ts: int, end_ts: int):
    event_dic = {}
    accout_email_dic={}
    try:
        curr_events = Event.filterByCalendarsTs(calendar_ids,datetime.fromtimestamp(start_ts), datetime.fromtimestamp(end_ts))
        for event in curr_events:
            event=vars(event)
            account_email=''
            if event['calendarId'] in accout_email_dic.keys():
                account_email = accout_email_dic[event['calendarId']]
            else:
                acc_id = Calendar.getCalendar(event['calendarId']).accountId
                account_email = UserAccount.getAccount(acc_id).emailAddress
                accout_email_dic[event['calendarId']] = account_email

            event['startTS'] = int(datetime.timestamp(event['startTS']))
            if(event['endTS'] == datetime(1990,1,1)):
                event['endTS'] = -1
            else:
                event['endTS'] = int(datetime.timestamp(event['endTS']))
            if(len(event['participants']) == 0):
                event['eventStatus'] = "yes"
            else:
                for participant in event['participants']:
                    if participant['email'] == account_email:
                        event['eventStatus'] = participant['status']
            
            if event['calendarId'] in event_dic.keys():
                event_dic[event['calendarId']].append(event)
            else:
                event_dic[event['calendarId']] = [event]

    except Exception as e:
        logger.error("Exception occured in fetch_bulk_events {0}".format(str(traceback.format_exc())))
    return event_dic

def get_wizard_payload(userId: str):
    try:
        if(userId == None or userId == ''):
            return {}
        account: UserAccount = UserAccount.getLastCreatedAt(userId)
        calendarlist = []
        payload = {}
        if account != None:
            calendars = Calendar.filterByAccountWiz(account.accountId)
            for calendar in calendars:
                calendar.provider = account.provider
                calendar.emailAddress = account.emailAddress
                calendarlist.append(calendar)
            payload = {'profileName': account.profileName , 'accountId': account.accountId, 'emailAddress': account.emailAddress, 'calendarList': calendarlist}
    except Exception as e:
        exp_msg = "Exception occured in get_wizard_payload. Traceback: %s \n" % traceback.format_exc()
        logger.error(exp_msg)
        return {}

    return payload

def get_calendars(user_id: str):
    accounts: List[UserAccount] = UserAccount.filterByUser(user_id)
    calendarlist = []
    try:
        for account in accounts:
            calendars = Calendar.filterByAccount(account.accountId)
            for calendar in calendars:
                calendar.provider = account.provider
                calendar.emailAddress = account.emailAddress
                calendarlist.append(calendar)
    except Exception as e:
        logger.error("Exception occured in get_calendars {0}".format(str(traceback.format_exc())))

    return calendarlist

def add_earnings_note(event_id:str, note_id:str, user_id:str, title:str, start_ts: int):
    try:
        user_acc = UserAccount.getAccount(user_id)
        if user_acc == None:
            acc: UserAccountType={'accountId': user_id, 'userId': user_id, 'profileName': '', 'emailAddress':'', 'accessToken':'', 'provider': 'sentieo', 'nylasCursor':''}
            UserAccount.addAccount(acc)
            user_acc = UserAccount.getAccount(user_id)

        er_calendar = Calendar.getCalendar(user_id)
        if er_calendar == None:
            cal: CalendarType = {'calendarId': user_id, 'accountId': user_acc.accountId, 'name': 'Earnings Calendar', 'status': False}
            Calendar.addCalendar(cal)
            er_calendar = Calendar.getCalendar(user_id)
        
        er_event = Event.getEvent(event_id)
        start = datetime.fromtimestamp(start_ts)
        end = start+timedelta(hours=1)
        if er_event == None:
            event: EventType = {'eventId': event_id, 'calendarId': er_calendar.calendarId, 'title': title, 'desc':'', 'startTS': start, 'endTS': end, 'owner': 'sentieo',\
                'notesIds': [note_id], 'parentId': None, 'status': 'confirmed', 'participants': [], 'icalUid': '', 'busy': False, 'location': None, 'reminders': None, 'readOnly': False}
            Event.addEvent(event)
        else:
            Event.addNote(event_id, note_id)
    
    except Exception as e:
        logger.error("Exception occured in add_earnings_note {0}".format(str(traceback.format_exc())))
    

def add_note(event_id: str, note_id: str):
    Event.addNote(event_id, note_id)

def sync_register(payload):
    try:
        auth_response = connect_nylas_token(payload)
        curr_user: UserAccountType = {**auth_response,"profileName": payload["name"], "userId": payload["user"]}
        UserAccount.addAccount(curr_user)
        calendars = get_nylas_calendars(curr_user["accessToken"])
        for calendar in calendars:
            calendar["status"] = False
            Calendar.addCalendar(calendar)
    except:
        logger.error("Exception occured in sync register {0}".format(str(traceback.format_exc())))
        return "error occured"

def register(payload):
    try:
        auth_response = connect_nylas_token(payload)
        curr_user: UserAccountType = {**auth_response, "userId": payload["user"], "profileName": payload["name"]}
        UserAccount.addAccount(curr_user)
        calendars = get_nylas_calendars(curr_user["accessToken"])

        startPrevMonth = int(
            datetime.timestamp(
                (datetime.today().replace(day=1) - timedelta(days=1)).replace(day=1)
            )
        )
        endNextMonth = int(
            datetime.timestamp(
                (
                    datetime.today().replace(day=28)
                    + timedelta(days=28)
                    + timedelta(days=10)
                ).replace(day=1)
                - timedelta(days=1)
            )
        )

        for calendar in calendars:
            calendar["status"] = True
            Calendar.addCalendar(calendar)
            (eventlist, nylaslist) = get_nylas_register_events(
                startPrevMonth,
                endNextMonth,
                calendar["calendarId"],
                curr_user["accessToken"],
            )
            for event in eventlist:
                Event.addEvent(event)

            for nylasd in nylaslist:
                NylasData.addNylasData(nylasd)

        return "Done"
    except:
        logger.error("Exception occured in register {0}".format(str(traceback.format_exc())))
        return "error occured"
