from config import settings

if settings.SERVER_TYPE == 'app':
    QUEUE_USER_CALENDARS = 'add_calendar_prod'
    QUEUE_USER_CALENDARS_ERROR = 'add_calendar_error_prod'
    config_file = 'app-config.json'
elif settings.SERVER_TYPE == 'test':
    QUEUE_USER_CALENDARS = 'add_calendar'
    QUEUE_USER_CALENDARS_ERROR = 'add_calendar_error'
    config_file = 'config.json'
else:
    QUEUE_USER_CALENDARS = 'add_calendar_'+ settings.DOMAIN
    QUEUE_USER_CALENDARS_ERROR = 'add_calendar_error_' + settings.DOMAIN
    config_file = 'app-config.json'

EVENTS_API = "https://api.nylas.com/events/"