import json

import uvicorn
from fastapi import FastAPI, Request, requests

from helperfiles import fetch_user, create_entry_in_io_log
from oauth.entities import User
from oauth.views import model as oauthrouter
from utils.logging_util import upload_payload_s3
from NylasIntegration.views import nylas_router
from fastapi.middleware.cors import CORSMiddleware
from dynaconf import settings
import NylasIntegration.outlook_oauth
import NylasIntegration.google_oauth
import uuid
from kafka_logger import set_logger_context_vars, reset_logger_context_vars, logger
import contextvars
from starlette.types import Message

origins = settings.ALLOWED_ORIGINS
# Remove origins

app = FastAPI()

#app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True)
request_id_var = contextvars.ContextVar("request_id", default="")


async def set_body(request: Request, body):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


# @app.middleware("http")
# async def log_request(request: Request, call_next):
#     request_id = request.headers["request-id"] if 'request-id' in request.headers else str(uuid.uuid4())
#     request_id_token = request_id_var.set(request_id)

#     user, user_id = None, ''
#     apid = request.cookies.get('apid')

#     payload = await get_body(request)
#     payload = payload.decode('utf-8')

#     if 'state_apid' in payload:
#         data = json.loads(payload)
#         apid = data["state_apid"]

#     # if 'acc_ref' in payload:
#     #     data = json.loads(payload)
#     #     user_id = await BotDBservice(data['acc_ref']).get_user_id()

#     # # validating session and setting user_id
#     if apid:
#         user = await fetch_user(apid)
#         user_id = str(user.id)

#     # to run locally, uncomment
#     # user_id = '61a7195428387f0b9fc737b9'
#     user = User(user_id)

#     username = request.headers["nylas-username"] if "nylas-username" in request.headers else ''
#     request.scope['user'] = user
#     req_obj = request.__dict__

#     # setting context vars
#     logger_request_id_token, logger_user_id_token, logger_username_token = set_logger_context_vars(request_id_var.get(), str(user_id),
#                                                                                                    username)
#     # logging payload for post endpoints
#     if request.method.lower() == 'post':
#         upload_payload_s3(payload, request_id_var.get(), "nylas_payloads/request/")
#     await create_entry_in_io_log({
#         'source': 'NylasIntegration',
#         'username': username,
#         'ri': request_id_var.get(),
#         'file_id': request_id_var.get()
#     })

#     message = '{0} Request: {1}'.format(request['method'], req_obj['scope']['path'])
#     logger.info('Entering : {0}'.format(message))

#     # hitting the views
#     response = await call_next(request)

#     response.headers["X-request-id"] = request_id_var.get()
#     resp = "Failure" if response.status_code != 200 else "Success"
#     logger.info('{0} Response received: {1}'.format(resp, message))
#     logger.info('Exiting {0}'.format(message))

#     # resetting context vars
#     request_id_var.reset(request_id_token)
#     reset_logger_context_vars(logger_request_id_token, logger_user_id_token, logger_username_token)

#     return response


app.include_router(oauthrouter)
app.include_router(nylas_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
