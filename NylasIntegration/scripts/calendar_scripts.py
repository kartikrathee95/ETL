import os

os.environ['ENV_FOR_DYNACONF'] = 'testing'
os.environ['YOUR_ENV']='integrationservice'
os.environ["PYTHONPATH"] = "."

import sys
import requests
import traceback
import json
import traceback

default_root = 'projects/'.join(os.getcwd().split('projects/')[:-1]) + 'projects/sentieointegrations'
sys.path.append(default_root)

from bson import json_util
from kafka_logger import logger
from typing import List
from datetime import datetime, timedelta
from NylasIntegration.scripts.constants import QUEUE_USER_CALENDARS, EVENTS_API
from NylasIntegration.scripts.script_handler import ScriptHandler
from NylasIntegration.models.models import Event, NylasData, UserAccount, Calendar
from NylasIntegration.scripts.log_func import log_function
from NylasIntegration.models.modeltypes import (
    UserAccountType,
    EventType,
    CalendarType,
    NylasDataType,
)
# from optparse import OptionParser


def nylas_api_offset_data(startTimestamp, endTimestamp, calendar_id, access_token):
    offset=0
    curr_events = []
    while True:
        off_ev = requests.get(
            EVENTS_API,
            params={
                "starts_after": startTimestamp,
                "ends_before": endTimestamp,
                "calendar_id": calendar_id,
                "limit": 1000,
                "offset": offset,
                "expand_recurring": True,
            },
            headers=({"Authorization": "Bearer " + access_token}),
        ).json()
        for ev in off_ev:
            curr_events.append(ev)
        offset += 1000
        if len(off_ev) == 0:
            break
    return curr_events 


def generate_event(curr_event, parent_id, startTS, endTS):
    curr_keys = list(curr_event.keys()) + list(curr_event.get('when',{}).keys())
    if "master_event_id" in curr_keys:
        parent_id = curr_event["master_event_id"]

    if "start_time" in curr_keys:
        startTS = datetime.fromtimestamp(curr_event["when"]["start_time"])

    if "end_time" in curr_keys:
        endTS = datetime.fromtimestamp(curr_event["when"]["end_time"])
    
    if "time" in curr_keys:
        startTS = datetime.fromtimestamp(curr_event["when"]["time"])

    if "start_date" in curr_keys:
        startTS = datetime.strptime(
                    curr_event["when"]["start_date"], "%Y-%m-%d"
                )

    if "end_date" in curr_keys:
        endTS = datetime.strptime(
                    curr_event["when"]["end_date"], "%Y-%m-%d"
                )

    if "date" in curr_keys:
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
    return event
            

class CalendarUpdate(ScriptHandler):

    def __init__(self, debug):
        super(CalendarUpdate, self).__init__(QUEUE_USER_CALENDARS, debug = debug)

    # @log_function
    def  get_nylas_register_events(self, msg):
        try:
            endTimestamp = datetime.timestamp((datetime.utcnow() + timedelta(days=90)))
            calendar_id = msg.get('calendarId')
            accountId = msg.get('accountId')
            startTimestamp = datetime.fromtimestamp(msg.get('startTS'))
            #delete existing events
            Event.deleteByCalendars([calendar_id])
            user = UserAccount.getAccount(accountId)
            if not user:
                logger.info("Queue skipped, user does not exist " + str(msg))
                self.remove_from_queue()
                return
            access_token = user.accessToken
            curr_events = nylas_api_offset_data(startTimestamp, endTimestamp, calendar_id, access_token)
            

            
            nylas_list: List[NylasDataType]=[]
            event_list: List[EventType]=[]
            startTS = datetime(1990,1,1)
            endTS = datetime(1990,1,1)
            parent_id = "None"
            for curr_event in curr_events:
                event = generate_event(curr_event, parent_id, startTS, endTS)

                event_list.append(event)

                nylas_list.append(
                        {"eventId": event['eventId'], "data": json.dumps(event, default=json_util.default), "status": event['status']}
                    )
            
            logger.info("Number of events updated for " + str(msg) + " : " + str(len(event_list)))

            Event.addBulkEvents(event_list)
            NylasData.addBulkNylasData(nylas_list)

            print(datetime.now(), 'Calendar processed ', str(msg))
            logger.info('Calendar processed '+ str(msg))
                
            self.remove_from_queue()
            calendar = Calendar.getCalendar(calendar_id)
            new_calendar = CalendarType.parse_obj({**calendar.__dict__}).__dict__
            new_calendar['status'] = True
            Calendar.updateCalendar(new_calendar)
            user = UserAccount.getAccount(accountId)
            new_user = UserAccountType.parse_obj({**user.__dict__}).__dict__
            new_user['createdAt'] = datetime.now()
            UserAccount.updateAccount(new_user)
        except:
            traceback.print_exc()
            logger.error('Exception occured in function {0} {1}'.format(msg, traceback.format_exc()))

    def callback(self,message):
        self.get_nylas_register_events(message)
        self.remove_from_queue()

    
    def sync(self, ts):
        try:
            users = UserAccount.getAll()
            startTimestamp = datetime.timestamp((datetime.utcnow() - timedelta(days=-7)))
            if ts == '30':
                endTimestamp = datetime.timestamp((datetime.utcnow() + timedelta(days=30)))
            else:
                endTimestamp = datetime.timestamp((datetime.utcnow() + timedelta(days=90)))
            for user in users:
                accountId = user.accountId
                access_token = user.accessToken
                calendars = Calendar.filterByAccount(user.accountId)
                name = user.profileName

                for calendar in calendars:
                    calendar_id = calendar.calendarId
                    calendar_name = calendar.name
                    print ('Starting for 30 min sync for ' , calendar_name, name)
                    logger.info('Starting for 30 min sync for ', calendar_name, name)
                    curr_events = nylas_api_offset_data(startTimestamp, endTimestamp, calendar_id, access_token)
                    new_nylas_list: List[NylasDataType]=[]
                    new_event_list: List[EventType]=[]
                    update_nylas_list: List[NylasDataType]=[]
                    update_event_list: List[EventType]=[]
                    startTS = datetime(1990,1,1)
                    endTS = datetime(1990,1,1)
                    parent_id = "None"
                    old_events = [x.icalUid for x in Event.getEvents(x['id'] for x in curr_events)]
                    # old_events = [x.eventId for x in Event.getEvents(x['id'] for x in curr_events)]
                    if len(old_events) != len(curr_events):
                        new_events = [x for x in curr_events if x['ical_uid'] not in old_events]
                        update_events = [x for x in curr_events if x['ical_uid'] in old_events]
                    else:
                        new_events = []
                        update_events = curr_events
                    for curr_event in new_events:
                        event = generate_event(curr_event, parent_id, startTS, endTS)

                        new_event_list.append(event)

                        new_nylas_list.append(
                                {"eventId": event['eventId'], "data": json.dumps(event, default=json_util.default), "status": event['status']}
                            )
                    
                    print("Number of events added for " + str(calendar_name) + " : " + str(len(new_event_list)), name)
                    logger.info("Number of events added for " + str(calendar_id) + " : " + str(len(new_event_list)))

                    for curr_event in update_events:
                        event = generate_event(curr_event, parent_id, startTS, endTS)
                        
                        update_event_list.append(event)

                        update_nylas_list.append(
                                {"eventId": event['eventId'], "data": json.dumps(event, default=json_util.default), "status": event['status']}
                            )

                    print("Number of events updated for " + str(calendar_name) + " : " + str(len(new_event_list)), name)
                    logger.info("Number of events updated for " + str(calendar_id) + " : " + str(len(update_event_list)))


                    Event.addBulkEvents(new_event_list)
                    NylasData.addBulkNylasData(new_nylas_list)

                    for e in update_event_list:
                        Event.updateEvent(e)
                    
                    for e in update_nylas_list:
                        NylasData.updateNylasData(e)

                    # print(datetime.now(), 'Calendar processed ', str(calendar_id))
                    logger.info('Calendar processed '+ str(calendar_id))
                        
                    # self.remove_from_queue()
                    # calendar = Calendar.getCalendar(calendar_id)
                    # new_calendar = CalendarType.parse_obj({**calendar.__dict__}).__dict__
                    # new_calendar['status'] = True
                    # Calendar.updateCalendar(new_calendar)
                    user = UserAccount.getAccount(accountId)
                    new_user = UserAccountType.parse_obj({**user.__dict__}).__dict__
                    new_user['createdAt'] = datetime.now()
                    UserAccount.updateAccount(new_user)

        except:
            traceback.print_exc()
            logger.error('Exception occured in function {0} {1}'.format('sync error', traceback.format_exc()))

    
    # def delta():
    #     try:

    #         latest_cursor = requests.get(
    #             "https://api.nylas.com/delta/", params={'cursor': user.nylasCursor},headers=({"Authorization": "Bearer "+user.accessToken})
    #         )
    #         deltas=latest_cursor.json()['deltas']
    #         #print(deltas)
    #         for event in deltas:
    #             #print(event['attributes']['status'])
    #             if(event['attributes']['status']=='confirmed'):
    #                 try:
    #                     curr=nylas.events.get(event['id'])
    #                     print(curr)
                         
    #                 except:
    #                     pass
    #             else:
    #                 #print(event['id'])
    #                  __self.deleteEvent(event['id'])
    #         curr_token_id:Token_Id = __self.add_token_id_helper(token['access_token'],token['provider'],token['email_address'],token['account_id'],latest_cursor.json()['cursor_end'])
    #         curr_token_id = jsonable_encoder(curr_token_id)
    #         acc=token['account_id']
    #         #print(acc)
    #         updated_token =  Tokens_Address.update_one(
    #                 {"account_id": acc}, {"$set": curr_token_id}
    #             )
    #         return
    #     except:
    #     #     return 'error occured'
    #         return



def main():
    # parser = OptionParser()
    # parser.add_option('-d','--debug', action="store_true", dest="debug", help="user this flag to execute all print statements", default=False)
    # (options,args) = parser.parse_args()
    # debug = options.debug
    obj = CalendarUpdate(True)
    msg = obj.read_from_queue()
    if msg:
        logger.info("Started for " + str(msg))
        print(datetime.now(), "Started for ", str(msg))
        obj.get_nylas_register_events(msg)
    return

if __name__ == '__main__':
    main()
