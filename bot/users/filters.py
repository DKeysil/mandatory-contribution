from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Filter

from core.users import get_user_by_tg_id


class UserRegistered(Filter):
    async def check(
            self, obj: Union[types.CallbackQuery, types.Message]
    ) -> bool:
        return bool(await get_user_by_tg_id(obj.from_user.id))


def setup_filters(dp: Dispatcher) -> None:
    dp.bind_filter(UserRegistered)
