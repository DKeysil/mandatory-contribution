from aiogram import Dispatcher
from aiogram_dialog import DialogManager

from bot.users.registration import Registration


async def start_cmd(_, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(Registration.name, reset_stack=True)


def setup_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(start_cmd, commands=None)
