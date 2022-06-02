import json
from multiprocessing import connection
import os
import urllib

from dynaconf import settings
import requests


def get_credentials_from_vault(key):
    if (settings.ENV_FOR_DYNACONF == "DEVELOPMENT"):
        return "", ""

    VAULT_CT_READ = settings.VAULT_CT_READ
    url = "/v1/secret/"
    try:
        baseurl = settings.VAULT_URL
        if '/' in key:
            return False, ''
        ct = VAULT_CT_READ
        if ct:
            status = True
        else:
            status = False
        if status:
            r = requests.get(baseurl + url + key, headers={'X-Vault-Token': ct}, timeout=2)
            data = json.loads(r.content)
            if data.get('data', {}).get(key, ''):
                return True, data.get('data').get(key)
            else:
                return False, ''
    except Exception as e:
        import traceback
        print('Exception incurred for key :', key)
        print(str(e))
        print(traceback.format_exc())
    return False, ''


def get_mongodb_config():
    if settings.ENV_FOR_DYNACONF in ['DEVELOPMENT', 'DEFAULT']:
        return settings.MONGO_HOST

    mongo_host = settings.MONGO_HOST
    status, mongo_up = get_credentials_from_vault('mongo_u__mongo_p')

    if status:
        mongo_username = mongo_up.split('__')[0]
        mongo_password = mongo_up.split('__')[1]
        connection_uri = mongo_host[: 10] + mongo_username + ':' + urllib.parse.quote_plus(
            mongo_password) + '@' + mongo_host[10:] + '/finance'
        return connection_uri

    else:
        print("Failed to get credential from vault")

def get_psql_config():
    settings.ENV_FOR_DYNACONF = 'testing'
    if settings.ENV_FOR_DYNACONF in ['DEVELOPMENT', 'DEFAULT']:
        psql_host= settings.PSQL_HOST
        psql_username="postgres"
        psql_password="123"
        return psql_host[:13]+psql_username+':'+urllib.parse.quote_plus(psql_password)+"@"+psql_host[13:]+'/postgres';

    psql_host=settings.PSQL_HOST
    if settings.ENV_FOR_DYNACONF in ['testing']:
        status, psql_up = get_credentials_from_vault('postgres_u__p')
        print(status,psql_up)
    else:
        status, psql_up = get_credentials_from_vault('psql_finance_creds')
    psql_username = ''
    psql_password = ''
    if status and psql_up:
        psql_username = psql_up.split('__')[0]
        psql_password = psql_up.split('__')[1]
        connection_uri = psql_host[:13]+psql_username+':'+urllib.parse.quote_plus(psql_password)+"@"+psql_host[13:]+'/finance';
    return connection_uri

def get_redis_config():
    return settings.REDIS_HOST

def connect_with_kafka():
    if (settings.ENV_FOR_DYNACONF == "DEVELOPMENT"):
        return "", ""
    status, KAFKA_CREDENTIALS = get_credentials_from_vault('kafka_user__kafka_pass')
    KAFKA_USER_NAME = ''
    KAFKA_PASSWORD = ''

    if status:
        KAFKA_USER_NAME = KAFKA_CREDENTIALS.split('__')[0]
        KAFKA_PASSWORD = KAFKA_CREDENTIALS.split('__')[1]
    return KAFKA_USER_NAME, KAFKA_PASSWORD


def get_encryption_credentials():
    if (settings.ENV_FOR_DYNACONF == "DEVELOPMENT"):
        return "", ""
    keystatus, ken_iv = get_credentials_from_vault('enckey__enciv')
    if keystatus and ken_iv:
        ENCKEY = ken_iv.split('__')[0]
        ENCIV = ken_iv.split('__')[1]
        return ENCKEY, ENCIV
    else:
        return None, None


def get_aws_s3_access_keys():
    if (settings.ENV_FOR_DYNACONF == "DEVELOPMENT"):
        return "", ""
    status, kid_ak = get_credentials_from_vault('amzn_secret__amzn_acess')
    if status and kid_ak:
        return kid_ak.split('__')[0], kid_ak.split('__')[1]
    else:
        return None, None
