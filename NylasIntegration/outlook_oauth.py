from helperfiles import async_exception_handler, exception_handler
from oauth.manager import OAuth2Manager
from kafka_logger import logger
from oauth.utils.helperfile import notify_user_sync
from oauth.entities import User
from config import settings
from NylasIntegration.scripts.constants import config_file
import os
import json
from NylasIntegration.managers.calendar_manager import register, sync_register

profile_name = ""
profile_email = ""


def extract_domain():
    env = os.environ.get("YOUR_ENV")  # integrationservice
    url = settings.DOMAIN + env
    if settings.ENV_FOR_DYNACONF == "DEVELOPMENT":
        return f"http://localhost:8000"
    return f"https://{url}.sentieo.com"

    # return f"http://localhost:8000"


class OutlookOAuth(OAuth2Manager):
    def __init__(self, user, source, app, data, acc_ref, env):
        super(OutlookOAuth, self).__init__(user, source, app, data, acc_ref, env)
        pass

    @staticmethod
    @exception_handler
    def parse_profile(profile):
        global profile_email
        global profile_name
        profile_name = profile.get("displayName")
        profile_email = (
            profile.get("mail")
            if "mail" in profile.keys()
            else profile.get("userPrincipalName")
        )

        res = {"acc_ref": profile.get("id"), "acc_name": profile_email, "profile_name": profile_name}
        return res

    @async_exception_handler
    async def save_token(self, token):
        logger.info("Saving Token... ")
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

        OUTLOOK_CLIENT = ""
        OUTLOOK_CLIENT_SECRET = ""

        with open(os.getcwd()+'/oauth/' + config_file, 'r') as f:
            config_dict = json.load(f)
            OUTLOOK_CLIENT = config_dict["OUTLOOK"]["CLIENT_ID"]
            OUTLOOK_CLIENT_SECRET = config_dict["OUTLOOK"]["CLIENT_SECRET"]
            NYLAS_CLIENT = config_dict["NYLAS"]["CLIENT_ID"]

        global profile_name
        global profile_email

        env = extract_domain()
        curr = {
            "client_id": NYLAS_CLIENT,
            "name": profile_name,
            "email_address": profile_email,
            "provider": "graph",
            "user": user_id,
            "settings": {
                "microsoft_client_id": OUTLOOK_CLIENT,
                "microsoft_client_secret": OUTLOOK_CLIENT_SECRET,
                "microsoft_refresh_token": user_token.get("refresh_token"),
                "redirect_uri": env + "/api/nylas/ocalendar/oauth/callback",
            },
            "scopes": "calendar",
        }
        
        sync_register(curr)
        return acc_name, user_token

    @async_exception_handler
    async def get_profile(self, token):
        graph_api_endpoint = "https://graph.microsoft.com/v1.0/me/"

        handler = self.oauth_handler.get_session(token)
        res = handler.get(graph_api_endpoint)
        resp = res.json()
        return self.parse_profile(resp)


OAuth2Manager.add_service("outlook", OutlookOAuth)
