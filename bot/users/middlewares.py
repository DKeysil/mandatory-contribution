from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from core import db


__all__ = ('BanMiddleware',)


class BanMiddleware(BaseMiddleware):
    async def on_process_message(self, msg: types.Message, _: dict):
        user = await db.models.User.get({'tg_id': int(msg.from_user.id)})
        if user:
            if user.get('banned'):
                await msg.answer('Вы забанены. Для разбана обратитесь к '
                                 'казначею вашего отделения.')
                raise CancelHandler()
