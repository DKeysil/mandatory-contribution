from aiogram import Bot, Dispatcher, types
import os
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from motor_client import SingletonClient
from aiogram.dispatcher.handler import CancelHandler
import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import uvloop


API_TOKEN = os.environ['BOT_API_KEY']

bot = Bot(token=API_TOKEN, parse_mode='html')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.new_event_loop()


def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
    return ServiceAccountCredentials.from_json_keyfile_name(
        "service_account_credentials.json",
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )


agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds, loop=loop)


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
