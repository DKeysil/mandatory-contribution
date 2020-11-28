from aiogram import Bot, Dispatcher, types
import os
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = os.environ['BOT_API_KEY']

bot = Bot(token=API_TOKEN, parse_mode='html')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class AnalyticsMiddleware(BaseMiddleware):

    def __init__(self):
        super(AnalyticsMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        # TODO: Сделать сбор аналитики
        pass


dp.middleware.setup(AnalyticsMiddleware())

from bot import modules
