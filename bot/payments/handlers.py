from aiogram import Dispatcher
from aiogram_dialog import DialogManager

from bot.payments.send import Send


async def send_cmd(_, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(Send.choose_payer, reset_stack=True)


def setup_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(send_cmd, commands=None)
