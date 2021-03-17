from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage

from bot import middlewares as mws
from core import settings as cfg


def create_bot_and_dispatcher() -> Dispatcher:
    bot = Bot(cfg.BOT_API_TOKEN, parse_mode='html')
    storage = MongoStorage(**cfg.MONGO_DB)
    dp = Dispatcher(bot, storage=storage)
    return dp


dp = create_bot_and_dispatcher()


from bot import modules  # for setup bot handlers


dp.setup_middleware(mws.BanMiddleware())
