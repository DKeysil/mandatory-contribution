"""Модуль для простых хендлеров."""
from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from loguru import logger as log


async def cancel(
        obj: Union[types.CallbackQuery, types.Message], state: FSMContext
) -> None:
    """
    Хендлер для отмены состояния по команде /cancel.

    Возможно будет использоваться для отмены состояния по callback'у.
    :param obj:
    :param state:
    :return:
    """
    current_state = await state.get_state()
    if not current_state:
        return
    user = obj.from_user
    log.debug('Cancel state for user %s (%d)', user.mention, user.id)
    await state.finish()


def setup_handlers(dp: Dispatcher) -> None:
    """
    Регистрация хендлеров бота.

    Хендлеры с состояниями должны быть выше других.
    :param dp:
    :return:
    """
    dp.register_message_handler(cancel, commands='cancel', state='*')
