from aiogram import Dispatcher, types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from app.motor_client import SingletonClient


class BanMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, _: dict):
        db = SingletonClient.get_data_base()
        user = await db.Users.find_one({
            'telegram_id': message.from_user.id
        })

        if user:
            if user.get('ban'):
                await message.answer('Вы забанены.')
                raise CancelHandler()


def setup_middlewares(dp: Dispatcher) -> None:
    dp.middleware.setup(BanMiddleware)
