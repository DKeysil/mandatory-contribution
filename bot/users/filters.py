from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Filter


class UserRegistered(Filter):
    async def check(
            self, obj: Union[types.CallbackQuery, types.Message]
    ) -> bool:
        from core.users import check_is_user_registered_by_tg_id
        return await check_is_user_registered_by_tg_id(obj.from_user.id)


def setup_filters(dp: Dispatcher) -> None:
    dp.bind_filter(UserRegistered)
