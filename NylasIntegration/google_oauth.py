# from oauth.services.mongodb import OAuthMongoDB
from helperfiles import async_exception_handler, exception_handler
from oauth.manager import OAuth2Manager
from kafka_logger import logger
from oauth.utils.helperfile import notify_user_sync
from oauth.utils.app_name_map import APP_NAME_MAP
from NylasIntegration.managers.calendar_manager import register, sync_register
from NylasIntegration.scripts.constants import config_file
# import requests
from oauth.entities import User
from config import settings
import os
import json


profile_name = ""
profile_email = ""


def extract_domain():
    env = os.environ.get("YOUR_ENV")  # integrationservice
    url = settings.DOMAIN + env
    if settings.ENV_FOR_DYNACONF == "DEVELOPMENT":
        return f"http://localhost:8000"
    return f"https://{url}.sentieo.com"

    # return f"http://localhost:8000"


class GoogleOAuth(OAuth2Manager):
    def __init__(self, user, source, app, data, acc_ref, env):
        super(GoogleOAuth, self).__init__(user, source, app, data, acc_ref, env)
        pass

    @staticmethod
    @exception_handler
    def parse_profile(profile):
        global profile_email
        global profile_name
        profile_name = profile.get("name")
        profile_email = profile.get("email")

        res = {
            "acc_ref": profile.get("id"),
            "acc_name": profile.get("email"),
            "profile_name": profile.get("name")
        }
        return res

    @async_exception_handler
    async def get_profile(self, token):
        api_endpoint = "https://www.googleapis.com/oauth2/v1/userinfo"
        handler = self.oauth_handler.get_session(token)
        res = handler.get(api_endpoint)
        resp = res.json()
        resp = self.parse_profile(resp)
        return resp

    @async_exception_handler
    async def save_token(self, token):
        logger.info("Saving Token... ")
        # import pdb;pdb.set_trace()
        token = self.parse_token(self.source, token)
        profile = await self.get_profile(token)
        token["acc_name"] = profile.get("acc_name")
        token["profile_name"] = profile.get("profile_name")
        user_app_token = await self.dbService.save_token(token, profile.get("acc_ref"))
        logger.info("Saved Token ... ")
        return profile.get("acc_name"), user_app_token

    @async_exception_handler
    async def get_token_from_authcode(self, code):
        """
         param code: authorization code that OAuth2Source Provide after Authorization
        :return: A token dict containing {'access_token','refresh_token','bearer','expires_at'} keys
        """
        logger.info("Entering function get_token_from_authcode")

        auth_obj = self.oauth_handler
        # fetch token
        token = self.get_token(auth_obj, code)
        # print('tkn ', token)
        # saving token in database
        acc_name, user_token = await self.save_token(token)

        if user_token:
            logger.info(
                "Exiting function get_token_from_authcode. Successfully extracted user_token",
                extra={"user_id": str(self.user.id)},
            )
            
        else:
            logger.error(
                "Exiting function get_token_from_authcode. Unable to get authorization code for token"
            )

        
        NYLAS_CLIENT = ""
        user_id = str(self.user.id)
        GOOGLE_CLIENT = ""
        GOOGLE_CLIENT_SECRET = ""

        with open(os.getcwd()+'/oauth/'+config_file, 'r') as f:
            config_dict = json.load(f)
            GOOGLE_CLIENT = config_dict["GOOGLE"]["CLIENT_ID"]
            GOOGLE_CLIENT_SECRET = config_dict["GOOGLE"]["CLIENT_SECRET"]
            NYLAS_CLIENT = config_dict["NYLAS"]["CLIENT_ID"]
        # user_id = '61a7195428387f0b9fc737b9'
        user_id = str(self.user.id)
        global profile_name
        global profile_email

        curr = {
            "client_id": NYLAS_CLIENT,
            "name": profile_name,
            "email_address": profile_email,
            "provider": "gmail",
            "user": user_id,
            "settings": {
                "google_client_id": GOOGLE_CLIENT,
                "google_client_secret": GOOGLE_CLIENT_SECRET,
                "google_refresh_token": user_token.get("refresh_token"),
            },
            "scopes": "calendar,calendar.read_only",
        }
        
        curr_another = {
            "name": profile_name,
            "email_address": profile_email,
            "user": user_id,
            "token": user_token.get("access_token"),
            "refresh_token": user_token.get("access_token"),}

        sync_register(curr)
        
        return acc_name, user_token


OAuth2Manager.add_service("google", GoogleOAuth)
