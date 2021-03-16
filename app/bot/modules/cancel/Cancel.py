from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger

from app.bot import dp


@dp.message_handler(lambda message: message.chat.type == 'private',
                    state='*',
                    commands=['cancel'])
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info('state cancelled')
    await state.finish()
