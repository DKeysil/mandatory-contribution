from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage

from bot import middlewares as mws
from bot.setup_handlers import setup_handlers
from core import settings as cfg


def create_bot_and_dispatcher() -> Dispatcher:
    bot = Bot(cfg.BOT_API_TOKEN, parse_mode='html')
    storage = MongoStorage(**cfg.MONGO_DB)
    dp = Dispatcher(bot, storage=storage)
    setup_handlers(dp)
    dp.setup_middleware(mws.BanMiddleware())
    return dp


dp = create_bot_and_dispatcher()
