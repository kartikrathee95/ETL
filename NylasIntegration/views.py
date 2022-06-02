import json
import time
import traceback
import aiohttp
from config import *
from NylasIntegration.scripts.calendar_scripts import CalendarUpdate
from fastapi import APIRouter, Request
from typing import Dict, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from kafka_logger import logger
from starlette.responses import JSONResponse
from fastapi.responses import PlainTextResponse, FileResponse
from oauth.user.utility import fetch_user_id
from NylasIntegration.models.models import Calendar, UserAccount, Event, sess
from NylasIntegration.managers.generate_excel import export_calendar
from NylasIntegration.models.modeltypes import EventType, UserAccountType
from NylasIntegration.managers.nylas_manager import event_deleted_webhook
from NylasIntegration.managers.calendar_manager import (
    fetch_bulk_events,
    fetch_bulk_notes,
    get_calendars,
    add_note,
    add_earnings_note,
    get_wizard_payload
)

from NylasIntegration.managers.nylas_manager import (
    event_created_webhook,
    event_updated_webhook,
    calendar_created_webhook,
    calendar_updated_webhook,
    calendar_deleted_webhook,
)
from NylasIntegration.helpers import extract_env, fetchCookies, divide_chunks

nylas_router = APIRouter()


def success_response(counter, response):
    return {
        "counter": counter,
        "response": {"status": True, "msg": ""},
        "result": response,
    }


class WebhookTrigger(BaseModel):
    deltas: List[object]

    class Config:
        arbitrary_types_allowed = True


@nylas_router.get("/api/nylas/checksession")
async def checkSession(request: Request):
    (_, user_id) = await fetch_user_id(request.cookies.get("apid"))

    if user_id == None:
        return {"status": "false"}
    else:
        return {"status": "true"}

@nylas_router.get("/api/nylas/getUserAccounts")
async def getUserAccounts(request: Request):
    (_, user_id) = await fetch_user_id(request.cookies.get("apid"))
    accounts = UserAccount.filterByUser(user_id)
    accounts_payload=[]
    for account in accounts:
        accounts_payload.append({"accountId":account.accountId, "profileName":account.profileName, "emailAddress": account.emailAddress, "provider": account.provider, "lastSynced": int(datetime.timestamp(account.createdAt))})
    return accounts_payload
    
@nylas_router.get("/api/nylas/getWizardPayload")
async def getCalendarWizardPayload(request: Request):
    try:
        (_, user_id) = await fetch_user_id(request.cookies.get("apid"))
        payload = get_wizard_payload(user_id)
        return payload
        
    except Exception as e:
        logger.error("Exception occured in getWizardPayload {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})
    

class SyncRegisterType(BaseModel):
    accountId: str
    calendarList:List
    pastTimestamp:int

@nylas_router.post("/api/nylas/syncRegisterQueue")
async def syncRegisterQueue(request: Request, payload: SyncRegisterType):
    try:
        load_events = CalendarUpdate(debug=True)
        for calendarId in payload.calendarList:
            script_payload = {'startTS': payload.pastTimestamp,
                                'calendarId':calendarId,
                                'accountId':payload.accountId}
            load_events.add_message_to_queue(json.dumps(script_payload))
        synced_calendars=[]
        for cid in payload.calendarList:
            status=False
            while not status:
                calendar = Calendar.getCalendar(cid)
                sess.refresh(calendar)     
                if calendar != None:
                   status = calendar.status
                else:
                    return
                time.sleep(1)

            if status == True:
                synced_calendars.append(cid)
        return JSONResponse(status_code=200, content={
                "info": {"message": "Calendar has been added!"}})

    except Exception as e:
        logger.error("Exception occured in syncRegisterQueue {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})


@nylas_router.get("/api/nylas/nylasidsecret")
async def getnylasidsecret():
    return {
        "clientId": "3yw1qraym5wzmiuzye7s7bg72",
        "clientSecret": "9mmcky90lt1phxcv2s4jott9z",
    }


class BulkEventParams(BaseModel):
    calendarIds: List
    startTS: int
    endTS: int


@nylas_router.post("/api/nylas/fetchBulkEvents")
async def fetchBulkEvents(request: Request, data: BulkEventParams):
    # (status, user_id) = await fetch_user_id(request.cookies.get('apid'))
    # user_id= '61a7195428387f0b9fc737b9'
    try:
        events_dic = fetch_bulk_events(data.calendarIds, data.startTS, data.endTS)
        return events_dic
    except Exception as e:
        logger.error("Exception occured in fetchBulkEvents {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})


class BulkNotesParams(BaseModel):
    eventIds: List

@nylas_router.post("/api/nylas/fetchBulkNotes")
async def fetchBulkNotes(request: Request, data: BulkNotesParams):
    # (status, user_id) = await fetch_user_id(request.cookies.get('apid'))
    # user_id= '61a7195428387f0b9fc737b9'
    try:
        cookies = fetchCookies(request)
        notes_dic = await fetch_bulk_notes(data.eventIds, cookies)
        return notes_dic
    except Exception as e:
        logger.error("Exception occured in fetchBulkNotes {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})


@nylas_router.get("/api/nylas/getCalendars")
async def getCalendars(request: Request):
    try:
        (_, user_id) = await fetch_user_id(request.cookies.get("apid"))
        calendars = get_calendars(user_id)
        return calendars
    except Exception as e:
        logger.error("Exception occured in getCalendars {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})


class CalendarListParams(BaseModel):
    calendars: List
    account_id: str

class EarningsEventParams(BaseModel):
    watch: List
    startTS: int
    endTS: int
    excel: bool


@nylas_router.post("/api/nylas/fetchEarningsEvents")
async def fetchEarningsEvents(request: Request, earningParams: EarningsEventParams):
    cookies = fetchCookies(request)
    start_date = datetime.fromtimestamp(earningParams.startTS).strftime("%Y-%m-%d")
    end_date = datetime.fromtimestamp(earningParams.endTS).strftime("%Y-%m-%d")
    env = extract_env()
    result = []
    ct = 0
    ticker_set = set()
    obj_ids=[]
    try:
        # for watch in earningParams.watch:
        watch_split = list(divide_chunks(earningParams.watch, 5))
        for watch in watch_split:
            req = {
            "watch": '<>'.join(watch),
            "startDate": start_date,
            "endDate": end_date,
            "counter": "1",
            "multi":"1",
            "_": "1643085569423211fad-d73c0e-caf81a",
            "loc": "app",
            "csrfmiddlewaretoken": cookies["csrftoken"],
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://user-{env}.sentieo.com/api/fetch_calendar/",
                    data=req,
                    cookies=cookies,
                ) as response:
                    r = await response.json()
            for row in r["result"]:
                extra_data = row.get('extra', {})
                call_times = list(set(extra_data.get("call_time", "").replace("None,", "").replace("None", "").split(',')))
                if len(call_times) == 1:
                    call_time = call_times[0]
                else:
                    call_times_with_time = [x for x in call_times if x[-8:] != '00:00:00']
                    if len(call_times_with_time) == 1:
                        call_time = call_times_with_time[0]
                    else:
                        call_time = call_times[0]
                live_link = extra_data.get("call_live_link", "").replace("None,", "").replace("None", "")
                read_listen = extra_data.get("read_listen", "").replace("None,", "").replace("None", "")
                replay_link = extra_data.get("call_replay_link", "").replace("None,", "").replace("None", "")
                ticker_set.add(row["ticker"])
                market_time = row["market_time"]
                if len(market_time) == 0:
                    market_time = "undetermined"
                obj_ids.append(row["obj_id"])
                result.append(
                    {
                        "confirmed": row["confirmed"],
                        "ticker": row["ticker"],
                        "company": row["company"],
                        "marketTime": market_time,
                        "date": row["date"],
                        "logo": "",
                        "earnings_id": row["obj_id"],
                        "call_time": call_time,
                        "call_live_link": live_link,
                        "call_replay_link": replay_link,
                        "doc_id": extra_data.get("docid",""),
                        "period": row["quarter_year"],
                        "info": (read_listen+" " if len(read_listen)>0 else "")+live_link
                    }
                )
        if earningParams.excel:
            file_name, file_path = export_calendar(result)
            return FileResponse(path = file_path, media_type='text/mp4', filename=file_name)

        tickerstr = ""
        tickerdic = {}
        for ticker in ticker_set:
            if (ct + 1) % 500 == 0:
                ct = 0
                tickerstr += ticker + ","
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://{env}.sentieo.com/api/get_company_logos/",
                        params={"tickers": tickerstr},
                        cookies=cookies,
                    ) as response:
                        r = await response.json()
                        for ticker_name in r["result"]:
                            tickerdic[ticker_name] = r["result"][ticker_name]
                tickerstr = ""
            else:
                ct += 1
                tickerstr += ticker + ","

        if len(tickerstr) > 0:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://{env}.sentieo.com/api/get_company_logos/",
                    params={"tickers": tickerstr},
                    cookies=cookies,
                ) as response:
                    r = await response.json()
                    for ticker_name in r["result"]:
                        tickerdic[ticker_name] = r["result"][ticker_name]
            tickerstr = ""

        # print(result)
        # print(tickerdic)
        earn_events_dic={}
        bk_earn_events=Event.getEvents(obj_ids)
        for ev in bk_earn_events:
            earn_events_dic[ev.eventId] = ev.notesIds
        for row in result:
            if row["ticker"] in tickerdic.keys():
                row["logo"] = tickerdic[row["ticker"]]
            if row["earnings_id"] in earn_events_dic.keys():
                row["notesIds"] = earn_events_dic[row["earnings_id"]]
            else:
                row["notesIds"] = []
        
        return result
    except Exception as e:
        logger.error("Exception occured in fetchEarningsEvents {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})


@nylas_router.get("/api/nylas/getWatchlists")
async def getWatchlists(request: Request):
    cookies = fetchCookies(request)
    params = (
            ('count', '4'),
            ('active_id', 'my_alert'),
            ('counter', '1'),
            ('_', '1647416644193_14a3ce-f1a61d-a14327'),
            ('loc', 'testing'),
            ('csrfmiddlewaretoken', cookies['csrftoken']),
            ('__call_from__', 'Calendar Manager'),
    )

    try:
        env = extract_env()
        watchlistDict={}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://user-{env}.sentieo.com/api/get_user_watchlist_data/",
                params=params,
                cookies=cookies,
            ) as response:
                r = await response.json()
                watchlistDict = {
                    "My Watchlists": r["result"]["individual_watchlist"],
                    # "Sentieo Watchlists": r["result"]["sentieo_watchlist"],
                    "Shared Watchlists": r["result"].get("indi_shared_watchlist",[])
                }
        return watchlistDict

    except Exception as e:
        logger.error("Exception occured in getWatchlists {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})


@nylas_router.get("/api/nylas/webhook", response_class=PlainTextResponse)
async def getChallenge(challenge):
    return challenge


@nylas_router.post("/api/nylas/webhook")
async def getTrigger(trigger: WebhookTrigger):
    currObj = trigger.deltas[0]
    # (status, user_id) = await fetch_user_id(request.cookies.get('apid'))
    # user_id= '61a7195428387f0b9fc737b9'
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
    print(currObj)
    if( currObj["object"] == "event" and int(currObj['date']) < startPrevMonth or int(currObj['date']) > endNextMonth):
        return "done", 200
        
    if currObj["type"] == "event.created":
        await event_created_webhook(
            currObj["object_data"]["account_id"], currObj["object_data"]["id"]
        )
    elif currObj["type"] == "event.updated":
        await event_updated_webhook(
            currObj["object_data"]["account_id"], currObj["object_data"]["id"]
        )
    elif currObj["type"] == "event.deleted":
        await event_deleted_webhook(
            currObj["object_data"]["account_id"], currObj["object_data"]["id"]
        )
    elif currObj["type"] == "calendar.created":
        await calendar_created_webhook(
            currObj["object_data"]["account_id"], currObj["object_data"]["id"]
        )
    elif currObj["type"] == "calendar.updated":
        await calendar_updated_webhook(
            currObj["object_data"]["account_id"], currObj["object_data"]["id"]
        )
    elif currObj["type"] == "calendar.deleted":
        await calendar_deleted_webhook(currObj["object_data"]["account_id"], currObj["object_data"]["id"])
    
    accId=currObj["object_data"]["account_id"]
    user=None
    if accId != None:
        user = UserAccount.getAccount(accId)

    if user != None:
            new_user = UserAccountType.parse_obj({**user.__dict__}).__dict__
            new_user['createdAt'] = datetime.now()
            UserAccount.updateAccount(new_user)

    return "done", 200


class CreateNote(BaseModel):
    eventName:str
    eventId:str
    tickers:str
    earnings:bool
    startTS:int

@nylas_router.post("/api/nylas/createNote")
async def createNote(request: Request, payload: CreateNote):
    try:
        cookies = fetchCookies(request)
        (status, user_id) = await fetch_user_id(cookies.get('apid'))
        env = extract_env()
        url = f"https://user-{env}.sentieo.com/api/notes/"
        data = {
            "type":"typed",
            "title": payload.eventName,
            "content":"",
            "tags":"",
            "tickers": json.dumps(payload.tickers.split(',')),
            "category":"",
            "created_at":datetime.strftime(datetime.now(),'%Y-%m-%dT%H:%M:%S'),
            'csrfmiddlewaretoken': cookies['csrftoken'],
            'uid': cookies['usid'],
            'create_source':'calendar'
            }

        headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        async with aiohttp.ClientSession() as session:
                async with session.post(url, cookies=cookies, data=data, headers=headers) as response:
                    r = await response.json()
        note_id = r['id']
        if(payload.earnings):
            add_earnings_note(payload.eventId, note_id,user_id,payload.eventName, payload.startTS)
        else:
            add_note(payload.eventId, note_id)
        
        return note_id

    except Exception as e:
        logger.error("Exception occured in createNote {0}".format(str(traceback.format_exc())))
        return JSONResponse(status_code=200, content={
                "error": {"message": "Some unknown error occurred", "code": "INTERNAL SERVER ERROR"}})
