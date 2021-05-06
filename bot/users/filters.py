from typing import Union

from aiogram import types
from aiogram.dispatcher.filters import Filter

from core import db


__all__ = ('UserRegistered',)


class UserRegistered(Filter):
    async def check(
            self, obj: Union[types.CallbackQuery, types.Message]
    ) -> bool:
        if await db.models.User.get({'tg_id': int(obj.from_user.id)}):
            return True
        return False
