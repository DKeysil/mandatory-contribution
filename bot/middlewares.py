from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware


class BanMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, _: dict):
        from core.motor_client import SingletonClient
        db = SingletonClient.get_data_base()
        user = await db.Users.find_one({
            'telegram_id': message.from_user.id
        })

        if user:
            if user.get('ban'):
                await message.answer('Вы забанены')
                raise CancelHandler()
