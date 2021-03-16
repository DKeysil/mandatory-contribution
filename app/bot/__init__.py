import asyncio
import os

import gspread_asyncio
import uvloop
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from oauth2client.service_account import ServiceAccountCredentials

from motor_client import SingletonClient


API_TOKEN = os.environ['BOT_API_KEY']
bot = Bot(token=API_TOKEN, parse_mode='html')
storage = MongoStorage(host=os.environ['MONGODB_HOSTNAME'],
                       port=os.environ['MONGODB_PORT'],
                       username=os.environ['MONGODB_USERNAME'],
                       password=os.environ['MONGODB_PASSWORD'])
dp = Dispatcher(bot, storage=storage)
uvloop.install()


def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html
    # for-bots-using-service-account
    return ServiceAccountCredentials.from_json_keyfile_name(
        "service_account_credentials.json",
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )


agcm = gspread_asyncio.AsyncioGspreadClientManager(
    get_creds, loop=asyncio.get_event_loop()
)


class BanMiddleware(BaseMiddleware):

    def __init__(self):
        super(BanMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        db = SingletonClient.get_data_base()
        user = await db.Users.find_one({
            'telegram_id': message.from_user.id
        })

        if user:
            if user.get('ban'):
                await message.answer('Вы забанены')
                raise CancelHandler()


dp.middleware.setup(BanMiddleware())


from bot import modules
from tasks import *
