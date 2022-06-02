import os

from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import date
from config import get_psql_config, get_redis_config
import redis
from motor import motor_asyncio

DATABASE_URL = get_psql_config()
REDIS_URL = get_redis_config()
# MONGO_URL = get_mongodb_config()

redis_engine = redis.StrictRedis(
    host=REDIS_URL, port=6379, socket_timeout=2, charset="utf-8", decode_responses=True
)
# mongo_client = motor_asyncio.AsyncIOMotorClient(MONGO_URL)
# mongo_engine = mongo_client['finance']


db_engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=db_engine)
Base = declarative_base()


def create_tables():
    from NylasIntegration.models.models import UserAccount, Calendar, Event, NylasData

    Base.metadata.create_all(bind=db_engine)


def drop_tables():
    from NylasIntegration.models.models import UserAccount, Calendar, Event, NylasData

    Base.metadata.drop_all(db_engine, checkfirst=True)
