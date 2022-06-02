import json
import os
import time
import webbrowser
import aiohttp
import uvicorn
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from icalendar import Calendar, Event, vCalAddress, vText
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
from loguru import logger
from fastapi.responses import PlainTextResponse, FileResponse
from constants import start_ts,end_ts,iteration,google_url,outlook_url
from NylasIntegration.models.models import WatchLists
from NylasIntegration.models.conn import create_tables
from NylasIntegration.models.modeltypes import WatchlistType

app = APIRouter()


def fetchCookies(request):
    cookies = {
        "apid": request.cookies.get("apid"),
        "usid": request.cookies.get("usid"),
        "csrftoken": request.cookies.get("csrftoken")


    }
    return cookies

def ics_download(result):
    cal = Calendar()
    open(os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sentieo_cal.ics'),'w').close()
    for row in result:
        
        ts = datetime.fromisoformat(row['date'])
        event = Event()
        event.add('summary', row['ticker'].upper() + '(' + row['company']   + ') Earnings')
        event.add('dtstart', ts)
        # event.add('dtend', datetime(2022, 10, 24, 10, 0, 0, tzinfo=pytz.utc))

        event.add('dtstamp', ts.date())

        # organizer = vCalAddress('MAILTO:hello@example.com')
        # organizer.params['cn'] = vText()
        # organizer.params['role'] = vText()
        # event['organizer'] = organizer
        event['location'] = vText(row['marketTime'])

        # Adding events to calendar
        cal.add_component(event)
 
        f = open(os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sentieo_cal.ics'), 'wb')
        f.write(cal.to_ical())
        f.close()

def addWebCalGoogle(apid,google_flag):
   
    if(google_flag=="none"):
        webbrowser.open(google_url.format(apid))
    


def addWebCalOutlook(apid,outlook_flag):
 
    if(outlook_flag=="none"):
        webbrowser.open(outlook_url.format(apid))




from loguru import logger

class WatchlistParams(BaseModel):
    watch: List
    google_flag:str
    outlook_flag:str

@app.post("/api/onenote/exportWatchlistsGoogle")
async def getWatchlists(request:Request,watchlistsParams:WatchlistParams):
    
    create_tables()
    cookies = fetchCookies(request)
    logger.info(cookies)
    create_tables()
    earningsevents = []
    payload = {"watch":watchlistsParams.watch,"startTS":start_ts,"endTS":end_ts,"excel":False}
    logger.info(payload)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://testingintegrationservice.sentieo.com/api/nylas/fetchEarningsEvents/",
                data = json.dumps(payload),
                cookies = cookies
            ) as response:
                earningsevents = await response.json() 
                
    except:
        logger.info("Error occured")
    logger.info(earningsevents)
    WatchLists.addWatchlist(watchlistsParams.watch,cookies["apid"],earningsevents,watchlistsParams.google_flag,"none")
    addWebCalGoogle(cookies["apid"],watchlistsParams.google_flag)
    payload = {"token":cookies["apid"]}

    ics_response = subscribeWatchlists()
    
    
    return ics_response

@app.post("/api/onenote/exportWatchlistsOutlook")
async def getWatchlists(request:Request,watchlistsParams:WatchlistParams):
    
    create_tables()
    cookies = fetchCookies(request)
    create_tables()
    earningsevents = []
    payload = {"watch":watchlistsParams.watch,"startTS":start_ts,"endTS":end_ts,"excel":False}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://testingintegrationservice.sentieo.com/api/nylas/fetchEarningsEvents/",
                data = json.dumps(payload),
                cookies = cookies
            ) as response:
                earningsevents = await response.json() 
                
    except:
        logger.info("Error occured")
    logger.info(earningsevents)
    WatchLists.addWatchlist(watchlistsParams.watch,cookies["apid"],earningsevents,"none",watchlistsParams.outlook_flag)
    addWebCalOutlook(cookies["apid"],watchlistsParams.outlook_flag)
    ics_response = subscribeWatchlists()
    
    
    return ics_response

def subscribeWatchlists():
    data  = WatchLists.getwatchlistarray()
    ics_data = data["earningsevents"]
 
    logger.info(type(ics_data))
    
    ics_download(ics_data)
         
    response = FileResponse(os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sentieo_cal.ics'))

    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)