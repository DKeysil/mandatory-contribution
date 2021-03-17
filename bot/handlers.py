"""Модуль для простых хендлеров."""
from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from loguru import logger as log


async def send_help(msg: types.Message) -> None:
    """
    Функция для отправки вспомогательного сообщения.
    Также используется, как хендлер для команды /help.
    :param msg:
    :return:
    """
    await msg.answer('Для отправки взноса воспользуйтесь командой /send.\n'
                     'Для сброса введённых данных отправьте /cancel.')


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
    msg = obj
    if isinstance(obj, types.CallbackQuery):
        msg = obj.message
    log.debug('Cancel state for user %s (%d)', user.mention, user.id)
    await state.finish()
    await msg.answer('Ввод данных сброшен.')


def setup_handlers(dp: Dispatcher) -> None:
    """
    Регистрация хендлеров бота.

    Хендлеры с состояниями должны быть выше других.
    :param dp:
    :return:
    """
    dp.register_message_handler(cancel, commands='cancel', state='*')

    dp.register_message_handler(help, commands='help')
