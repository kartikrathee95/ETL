from threading import local
import json
import requests
import traceback
from config import settings
from NylasIntegration.helpers import extract_env

_locals = local()

def default_response():
    return {
        'result':[],
        'counter':0,
        'response':{
                'status':False,
                'msg':[]
        }
    }


def post_request_data(url, params = {}, cookies = {}, timeout=2, default=default_response(),headers={}, data={}, files = None, verify = False, logger = None):
    try:
        params = data if data else params
        if verify:
            if files:
                response = requests.post(url, data=params, cookies=cookies, timeout=timeout, headers=headers, files = files, verify = True)
            else:
                response = requests.post(url, data=params, cookies=cookies, timeout=timeout, headers=headers, verify = True)
        else:
            if files:
                response = requests.post(url, data=params, cookies=cookies, timeout=timeout, headers=headers, files = files)
            else:
                response = requests.post(url, data=params, cookies=cookies, timeout=timeout, headers=headers)
    except Exception as error:
        if logger:
            logger.error('POST API exception for url {0} \n {1} \n {2}'.format(url, error, traceback.format_exc()))

        response = requests.models.Response()
        response.status_code = 504
        if type(default) in (dict, list, tuple):
            response._content = json.dumps(default)
    return response

class Pusher():
    def __init__(self):
        pass
    
    def push_to_socket(obj, cookies={}, logger = None):
        if not obj:
            print('no data to push')
            return

        if 'action_type' not in obj: #set default action type
            obj['action_type'] = 'send_to_members'
        if '' in obj:
            obj['members'] = obj['to']

        obj['requestid'] = getattr(_locals, 'requestid', '')

        env = extract_env()

        # obj['action_info'] = jwt.encode({
        #         'exp': datetime.utcnow() + timedelta(seconds=20),
        #         'members' : obj['members'],
        #         'action_type' : obj['action_type'],
        #         'group' : obj.get('group', '')
        #         }, 
        #         'secret',
        #         algorithm = 'HS256'
        # )

        url = 'https://websocket-'+env+'.sentieo.com?access_token={"username": "keshav"}.jYsgNMHhM9hbclk3S4JkGlCVPOo'
        try:
            r=post_request_data(url = url, data=json.dumps(obj), cookies=cookies, headers={'Content-Type':'application/json'}, timeout = 1)
            if logger:
                logger.info("Push To Socket server - %s - %s", env, r.text)
                #logger.info("data - locked by - %s locked - %s memeber - %s", obj.get('locked_by'), obj.get('locked'), obj.get('members'))
                #logger.info("response - %s", r.text if r else '')
            return obj
        except Exception as e:
            if logger:
                logger.info('exception in push to socket - %s', str(e))
            #send_to_slack(SLACK_NOTEBOOK_API_ERROR, SERVER_HOST.upper() + 'Exception in Push To Socket: ' + str(e))