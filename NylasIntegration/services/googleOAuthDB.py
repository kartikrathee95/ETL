from oauth.services.mongodb import OAuthMongoDB
import traceback

from kafka_logger import logger
from oauth.models import *
from datetime import datetime
from config import get_mongodb_config
from helperfiles import connect_with_mongo, async_exception_handler

connection_uri = get_mongodb_config()


class GoogleOAuthDB(OAuthMongoDB):
    def __init__(self, user, source, acc_ref, app_name):
        super(GoogleOAuthDB, self).__init__(user, source, acc_ref, app_name)
        pass

    @staticmethod
    async def get_user_quick(source, acc_ref):
        db = await connect_with_mongo()
        collection = db["user_app_token"]

        __filter = {"source": source, "acc_ref": acc_ref}
        obj = await collection.find_one(__filter)
        return obj["user"]

    async def save_token(self, token, acc_ref):
        # import pdb; pdb.set_trace()
        db = await connect_with_mongo()
        collection = db["user_app_token"]
        __filter = {"user": self.user, "source": self.source, "acc_ref": acc_ref}
        try:
            UserAppToken(**__filter, **token)
            if token.get("refresh_token") != None:
                await collection.update_one(__filter, {"$set": token}, upsert=True)
            return await collection.find_one(__filter)
        except KeyError:
            raise Exception("Invalid Token")
        except Exception as e:
            raise Exception("Something Went Wrong while saving in Mongo", e)
