from config import settings
settings.ENV_FOR_DYNACONF ="DEVELOPMENT"

#from NylasIntegration.managers.calendar_manager import get_calendars, fetch_bulk_events, fetch_bulk_notes
from NylasIntegration.views import fetchEarningsEvents, EarningsEventParams
import asyncio


#print(settings.ENV_FOR_DYNACONF)
#cProfile.run('get_calendars("61a7195428387f0b9fc737b9")')
#get_calendars("61a7195428387f0b9fc737b9")
# startTS=1646721783
# endTS=1648622583
# calendarIds=['e7rknty6viyxl5ood1h1j4mh4', '5cprfqvr8odovzauapvqgdpm9']
# be=fetch_bulk_events(calendarIds, startTS, endTS)
# cookies = {
#         "apid": "d00c62fc0c3885bfecbea4863d127a9a948092121657fb1cd3889b7b3a479fb9",
#         "usid": "72559da6736d936473227f0a1bd14b71bfe3c6b5a46145c417411d1b65b63823",
#         "csrftoken": "ztX1CVmK8sPDML3h6vnGobuMzbYdRLyo",
#     }
# eventIds = ['372fm9j7fu71wme8anea0v9l5_20220314T093000Z',
#  'efc0emwww7yrl8apg7z2wysgy',
#  'c4t8ki3bn80cbs9s1ylimqpyq_20220315T023000Z',
#  '2cqtxymmv0vx0i89patjfreh_20220315T023000Z',
#  '9ac0572nf5eypcprc4ulk6e8_20220316T023000Z',
#  '372fm9j7fu71wme8anea0v9l5_20220321T093000Z',
#  'c4t8ki3bn80cbs9s1ylimqpyq_20220322T023000Z',
#  '9rgd7ruii8peggteq6fuxrvaa_20220322T023000Z',
#  '2cqtxymmv0vx0i89patjfreh_20220322T023000Z',
#  '9ac0572nf5eypcprc4ulk6e8_20220323T023000Z',
#  '372fm9j7fu71wme8anea0v9l5_20220328T093000Z',
#  'c4t8ki3bn80cbs9s1ylimqpyq_20220329T023000Z',
#  '9rgd7ruii8peggteq6fuxrvaa_20220329T023000Z',
#  '2cqtxymmv0vx0i89patjfreh_20220329T023000Z',
#  '9ac0572nf5eypcprc4ulk6e8_20220330T023000Z',
#  '62g2lg4aljkxuwa97c2x4op9l_20220317']

# print(asyncio.run(fetch_bulk_notes(cookies, eventIds )))

# print(asyncio.run(fetchEarningsEvents(cookies, EarningsEventParams.parse_obj({
# 	"watch":"All Watchlist Tickers",
#     "startTS":1640031354,
#     "endTS":1656215354,
#     "excel":False
# }) )))