from aiogram import Dispatcher

from bot import middlewares as mws
from bot import users
from bot.setup_handlers import setup_handlers
from core import settings as cfg


def setup_middlewares(dp: Dispatcher) -> None:
    dp.setup_middleware(mws.BanMiddleware())


def setup_filters(dp: Dispatcher) -> None:
    users.setup_filters(dp)


def setup_dialogs(dp: Dispatcher) -> None:
    from aiogram_dialog import DialogRegistry

    registry = DialogRegistry(dp)

    registry.register(users.reg_dialog)


def create_bot_and_dispatcher() -> Dispatcher:
    from aiogram import Bot
    from aiogram.contrib.fsm_storage.mongo import MongoStorage

    bot = Bot(cfg.BOT_API_TOKEN, parse_mode='html')
    storage = MongoStorage(**cfg.MONGO_DB)
    dp = Dispatcher(bot, storage=storage)

    setup_middlewares(dp)
    setup_filters(dp)
    setup_dialogs(dp)
    setup_handlers(dp)

    return dp


dp = create_bot_and_dispatcher()
