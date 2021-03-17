from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger


async def cancel_cmd(_: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info('state cancelled')
    await state.finish()
