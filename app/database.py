from motor import motor_asyncio
from app.config.settings import get_settings
from pymongo import MongoClient
from enum import Enum, StrEnum

settings = get_settings()

sync_client = MongoClient(settings.db_url)

client = motor_asyncio.AsyncIOMotorClient(settings.db_url)


sync_db = sync_client[settings.db_name]

db = client[settings.db_name]


class cols():
    users = db["Users"]
    sessions = db["Sessions"]
    accesscodes = db["AccessCodes"]
    passwordresetstores = db["PasswordResetStores"]
