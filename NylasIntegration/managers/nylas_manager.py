import requests
from fastapi.encoders import jsonable_encoder
from datetime import datetime
import pytz
from typing import List
import json
from bson import json_util
import traceback
from kafka_logger import logger
from NylasIntegration.models.modeltypes import (
    UserAccountType,
    EventType,
    CalendarType,
    NylasDataType,
)
from NylasIntegration.models.models import UserAccount, Event, Calendar, NylasData
from NylasIntegration.scripts.constants import config_file
from NylasIntegration.services.pusher import Pusher

import os
import json

CLIENT_ID = ""
CLIENT_SECRET = ""

with open(os.getcwd()+'/oauth/'+config_file, 'r') as f:
    config_dict = json.load(f)
    CLIENT_ID = config_dict["NYLAS"]["CLIENT_ID"]
    CLIENT_SECRET = config_dict["NYLAS"]["CLIENT_SECRET"]


def connect_nylas_token(authorize_payload):
    try:
        nylas_authorization = requests.post(
            "https://api.nylas.com/connect/authorize",
            json=jsonable_encoder(authorize_payload),
        )
        nylas_code = nylas_authorization.json()["code"]
        token_payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": nylas_code,
        }

        nylas_authorization = requests.post(
            "https://api.nylas.com/connect/token", json=jsonable_encoder(token_payload)
        )
        json_response = nylas_authorization.json()
        account_id = json_response["account_id"]
        access_token = json_response["access_token"]
        email_Address = json_response["email_address"]
        provider = authorize_payload["provider"]

        latest_cursor = requests.post(
            "https://api.nylas.com/delta/latest_cursor",
            headers=({"Authorization": "Bearer " + access_token}),
        )
        cursor = latest_cursor.json()["cursor"]
        return {
            "accountId": account_id,
            "accessToken": access_token,
            "emailAddress": email_Address,
            "provider": provider,
            "nylasCursor": cursor,
        }

        # return nylas_code;
    except Exception as e:
        logger.error("Exception occured in connect_nylas_token {0}".format(str(traceback.format_exc())))
        return {}


def get_nylas_register_events(startTimestamp, endTimestamp, calendar_id, access_token):
    nylaslist = []
    eventlist = []
    try:     
        curr_events = requests.get(
            "https://api.nylas.com/events/",
            params={
                "starts_after": startTimestamp,
                "ends_before": endTimestamp,
                "calendar_id": calendar_id,
                "limit": 500,
                "expand_recurring": True,
            },
            headers=({"Authorization": "Bearer " + access_token}),
        ).json()
        for curr_event in curr_events:
            parent_id = "None"
            startTS = datetime(1990,1,1)
            endTS = datetime(1990,1,1)
            if "master_event_id" in curr_event.keys():
                parent_id = curr_event["master_event_id"]

            if "start_time" in curr_event["when"].keys():
                startTS = datetime.fromtimestamp(curr_event["when"]["start_time"])

            if "end_time" in curr_event["when"].keys():
                endTS = datetime.fromtimestamp(curr_event["when"]["end_time"])
            
            if "time" in curr_event["when"].keys():
                startTS = datetime.fromtimestamp(curr_event["when"]["time"])

            if "start_date" in curr_event["when"].keys():
                startTS = datetime.strptime(
                            curr_event["when"]["start_date"], "%Y-%m-%d"
                        )

            if "end_date" in curr_event["when"].keys():
                endTS = datetime.strptime(
                            curr_event["when"]["end_date"], "%Y-%m-%d"
                        )

            if "date" in curr_event["when"].keys():
                startTS = datetime.strptime(
                            curr_event["when"]["date"], "%Y-%m-%d"
                        )

            status = curr_event["status"]
            eventlist.append(
                {
                    "eventId": curr_event["id"],
                    "calendarId": curr_event["calendar_id"],
                    "title": curr_event["title"],
                    "desc": curr_event["description"],
                    "owner": curr_event["owner"],
                    "participants": curr_event["participants"],
                    "parentId": parent_id,
                    "status": status,
                    "startTS": startTS,
                    "endTS": endTS,
                    "notesIds": [],
                    "icalUid": curr_event["ical_uid"],
                    "busy": curr_event["busy"],
                    "location": curr_event["location"],
                    "reminders": curr_event["reminders"],
                    "readOnly": curr_event["read_only"]
                }
            )

            nylaslist.append(
                {"eventId": curr_event["id"], "data": json.dumps(curr_event, default=json_util.default), "status": status}
            )

        
    except Exception as e:
        logger.error("Exception occured in get_nylas_register_events {0}".format(str(traceback.format_exc())))

    return (eventlist, nylaslist)

def get_nylas_calendars(access_token):
    calendarlist = []
    try:       
        curr_calendars = requests.get(
            "https://api.nylas.com/calendars",
            headers=({"Authorization": "Bearer " + access_token}),
        ).json()
        for curr_calendar in curr_calendars:
            calendarlist.append(
                {
                    "calendarId": curr_calendar["id"],
                    "accountId": curr_calendar["account_id"],
                    "name": curr_calendar["name"],
                }
            )

    except Exception as e:
        logger.error("Exception occured in get_nylas_calendars {0}".format(str(traceback.format_exc())))

    return calendarlist
    


async def event_created_webhook(account_id: str, event_id: str):
    try:
        # print(token['access_token'])
        account = UserAccount.getAccount(account_id)
        curr_events = requests.get(
            "https://api.nylas.com/events",
            params={"event_id": event_id, "expand_recurring": True},
            headers=({"Authorization": "Bearer " + account.accessToken}),
        ).json()
        if(len(curr_events)==0):
            curr_events = requests.get(
                            "https://api.nylas.com/events",
                            params={"event_id": event_id},
                            headers=({"Authorization": "Bearer " + account.accessToken}),
                        ).json()

        if len(curr_events) == 0:
            Event.deleteEvent(event_id)
            return

        event_list=[]
        for curr_event in curr_events:
            parent_id = "None"
            startTS = datetime(1990,1,1)
            endTS = datetime(1990,1,1)
            if "master_event_id" in curr_event.keys():
                parent_id = curr_event["master_event_id"]

            if "start_time" in curr_event["when"].keys():
                startTS = datetime.fromtimestamp(curr_event["when"]["start_time"])

            if "end_time" in curr_event["when"].keys():
                endTS = datetime.fromtimestamp(curr_event["when"]["end_time"])
            
            if "time" in curr_event["when"].keys():
                startTS = datetime.fromtimestamp(curr_event["when"]["time"])

            if "start_date" in curr_event["when"].keys():
                startTS = datetime.strptime(
                            curr_event["when"]["start_date"], "%Y-%m-%d"
                        )

            if "end_date" in curr_event["when"].keys():
                endTS = datetime.strptime(
                            curr_event["when"]["end_date"], "%Y-%m-%d"
                        )

            if "date" in curr_event["when"].keys():
                startTS = datetime.strptime(
                            curr_event["when"]["date"], "%Y-%m-%d"
                        )

            status = curr_event["status"]
            event: EventType = {
                "eventId": curr_event["id"],
                "calendarId": curr_event["calendar_id"],
                "title": curr_event["title"],
                "desc": curr_event["description"],
                "owner": curr_event["owner"],
                "participants": curr_event["participants"],
                "parentId": parent_id,
                "status": status,
                "startTS": startTS,
                "endTS": endTS,
                "notesIds": [],
                "icalUid": curr_event["ical_uid"],
                "busy": curr_event["busy"],
                "location": curr_event["location"],
                "reminders": curr_event["reminders"],
                "readOnly": curr_event["read_only"]
            }
            event_list.append(event)
        
        nylas_list: List[NylasDataType]=[]
        for event in event_list:
            nylas_list.append(
                    {"eventId": event['eventId'], "data": json.dumps(event, default=json_util.default), "status": event['status']}
                )
        Event.addBulkEvents(event_list)
        NylasData.addBulkNylasData(nylas_list)

        pusher_obj = dict()
        pusher_obj['calendar_action'] = 'event_created_webhook'
        pusher_obj['action_status'] = 'Done'
        pusher_obj['members'] = [account.userId]
        Pusher.push_to_socket(pusher_obj)
        
    except Exception as e:
        logger.error("Exception occured in event_created_webhook {0}".format(str(traceback.format_exc())))


async def event_deleted_webhook(account_id:str, event_id: str):
    try:
        account = UserAccount.getAccount(account_id)
        Event.deleteEvent(event_id)

        pusher_obj = dict()
        pusher_obj['calendar_action'] = 'event_deleted_webhook'
        pusher_obj['action_status'] = 'Done'
        pusher_obj['members'] = [account.userId]
        Pusher.push_to_socket(pusher_obj)

    except Exception as e:
        logger.error("Exception occured in event_deleted_webhook {0}".format(str(traceback.format_exc())))


async def event_updated_webhook(account_id: str, event_id: str):
    try:
        # print(token['access_token'])
        account = UserAccount.getAccount(account_id)
        curr_events = requests.get(
            "https://api.nylas.com/events",
            params={"event_id": event_id, "expand_recurring": True},
            headers=({"Authorization": "Bearer " + account.accessToken}),
        ).json()
        if(len(curr_events)==0):
            curr_events = requests.get(
                            "https://api.nylas.com/events",
                            params={"event_id": event_id},
                            headers=({"Authorization": "Bearer " + account.accessToken}),
                        ).json()
        if len(curr_events) == 0:
            Event.deleteEvent(event_id)

            pusher_obj = dict()
            pusher_obj['calendar_action'] = 'event_deleted_webhook'
            pusher_obj['action_status'] = 'Done'
            pusher_obj['members'] = [account.userId]
            Pusher.push_to_socket(pusher_obj)
            return

        for curr_event in curr_events:
            parent_id = "None"
            startTS = datetime(1990,1,1)
            endTS = datetime(1990,1,1)
            if "master_event_id" in curr_event.keys():
                parent_id = curr_event["master_event_id"]

            if "start_time" in curr_event["when"].keys():
                startTS = datetime.fromtimestamp(curr_event["when"]["start_time"])

            if "end_time" in curr_event["when"].keys():
                endTS = datetime.fromtimestamp(curr_event["when"]["end_time"])
            
            if "time" in curr_event["when"].keys():
                startTS = datetime.fromtimestamp(curr_event["when"]["time"])

            if "start_date" in curr_event["when"].keys():
                startTS = datetime.strptime(
                            curr_event["when"]["start_date"], "%Y-%m-%d"
                        )

            if "end_date" in curr_event["when"].keys():
                endTS = datetime.strptime(
                            curr_event["when"]["end_date"], "%Y-%m-%d"
                        )

            if "date" in curr_event["when"].keys():
                startTS = datetime.strptime(
                            curr_event["when"]["date"], "%Y-%m-%d"
                        )

            status = curr_event["status"]
            if "master_event_id" in curr_event.keys():
                timestr=datetime.strftime(
                        startTS.astimezone(pytz.utc),
                        "%Y%m%dT%H%M%SZ",
                    )
                old_recurr_id = (
                    curr_event["master_event_id"]
                    + "_"
                    + timestr
                )
                old_event = Event.getEvent(old_recurr_id)
                if old_event != None:
                    Event.deleteEvent(old_recurr_id)
                other_events = Event.otherIcalStartTS(curr_event["ical_uid"],startTS)
                eventIds=[]
                for event in other_events:
                    eventIds.append(event.eventId)
                Event.deleteBulkEvents(eventIds)

            update_event = Event.getEvent(event_id)
            new_event: EventType = {
                "eventId": curr_event["id"],
                "calendarId": curr_event["calendar_id"],
                "title": curr_event["title"],
                "desc": curr_event["description"],
                "owner": curr_event["owner"],
                "participants": curr_event["participants"],
                "parentId": parent_id,
                "status": status,
                "startTS": startTS,
                "endTS": endTS,
                "notesIds":[] if update_event == None else update_event.notesIds,
                "icalUid": curr_event["ical_uid"],
                "busy": curr_event["busy"],
                "location": curr_event["location"],
                "reminders": curr_event["reminders"],
                "readOnly": curr_event["read_only"]
            }
            Event.addEvent(new_event)   
        pusher_obj = dict()
        pusher_obj['calendar_action'] = 'event_updated_webhook'
        pusher_obj['action_status'] = 'Done'
        pusher_obj['members'] = [account.userId]
        Pusher.push_to_socket(pusher_obj)
        
    except Exception as e:
        logger.error("Exception occured in event_updated_webhook {0}".format(str(traceback.format_exc())))


async def calendar_created_webhook(account_id, calendar_id):
    try:
        account = UserAccount.getAccount(account_id)
        calendar = requests.get(
            "https://api.nylas.com/calendars/" + calendar_id,
            headers=({"Authorization": "Bearer " + account.accessToken}),
        ).json()

        calendar: CalendarType = {
            "calendarId": calendar["id"],
            "accountId": calendar["account_id"],
            "name": calendar["name"],
            "status": False
        }
        Calendar.addCalendar(calendar)
        pusher_obj = dict()
        pusher_obj['calendar_action'] = 'calendar_created_webhook'
        pusher_obj['action_status'] = 'Done'
        pusher_obj['members'] = [account.userId]
        Pusher.push_to_socket(pusher_obj)
    except Exception as e:
        logger.error("Exception occured in calendar_created_webhook {0}".format(str(traceback.format_exc())))



async def calendar_updated_webhook(account_id, calendar_id):
    try:
        account = UserAccount.getAccount(account_id)
        calendar = requests.get(
            "https://api.nylas.com/calendars/" + calendar_id,
            headers=({"Authorization": "Bearer " + account.accessToken}),
        ).json()

        old_calendar = Calendar.getCalendar(calendar_id)
        calendar: CalendarType = {
            "calendarId": calendar["id"],
            "accountId": calendar["account_id"],
            "name": calendar["name"],
            "status": old_calendar.status
        }

        Calendar.updateCalendar(calendar)
        pusher_obj = dict()
        pusher_obj['calendar_action'] = 'calendar_updated_webhook'
        pusher_obj['action_status'] = 'Done'
        pusher_obj['members'] = [account.userId]
        Pusher.push_to_socket(pusher_obj)
    except Exception as e:
        logger.error("Exception occured in calendar_updated_webhook {0}".format(str(traceback.format_exc())))


async def calendar_deleted_webhook(account_id, calendar_id):
    try:
        account = UserAccount.getAccount(account_id)
        Calendar.deleteCalendar(calendar_id)
        pusher_obj = dict()
        pusher_obj['calendar_action'] = 'calendar_deleted_webhook'
        pusher_obj['action_status'] = 'Done'
        pusher_obj['members'] = [account.userId]
        Pusher.push_to_socket(pusher_obj)
    except Exception as e:
        logger.error("Exception occured in calendar_deleted_webhook {0}".format(str(traceback.format_exc())))

