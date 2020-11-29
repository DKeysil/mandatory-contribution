from aiogram import Bot, Dispatcher, types
import os
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from motor_client import SingletonClient

API_TOKEN = os.environ['BOT_API_KEY']

bot = Bot(token=API_TOKEN, parse_mode='html')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class BanMiddleware(BaseMiddleware):

    def __init__(self):
        super(BanMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        pass
        # todo: сделать нормальный бан пользователей
        # db = SingletonClient.get_data_base()
        # user = await db.Users.find_one({
        #     'telegram_id': message.from_user.id
        # })
        #
        # if user.get('ban'):
        #     await message.answer('Вы забанены')
        #     raise BaseException


dp.middleware.setup(BanMiddleware())

from bot import modules
