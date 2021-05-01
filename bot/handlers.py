from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from bot import users


HELP_MSG = 'Для отправки взноса воспользуйтесь командой /send.'


async def start_help_cmd(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer(HELP_MSG)


def register_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(start_help_cmd, users.filters.UserRegistered(),
                                commands=('start', 'help'))
    dp.register_message_handler(users.registration.start_cmd, commands='start')
