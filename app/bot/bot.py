from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.mongo import MongoStorage

from app.bot import settings
from app.bot.filters import setup_filters
from app.bot.handlers import setup_handlers
from app.bot.middlewares import setup_middlewares


def setup_bot_and_dp() -> Dispatcher:
    bot = Bot(settings.API_TOKEN, parse_mode='html')
    storage = MongoStorage(**settings.MONGODB)
    dp = Dispatcher(bot, storage=storage)
    setup_filters(dp)
    setup_handlers(dp)
    setup_middlewares(dp)
    return dp


dp = setup_bot_and_dp()


def start_polling() -> None:
    executor.start_polling(dp, skip_updates=True)


def start_webhook() -> None:
    executor.start_webhook(dp, '/')
