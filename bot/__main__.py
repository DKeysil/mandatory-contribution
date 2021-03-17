from aiogram import executor
from loguru import logger

from bot import dp
from core.tasks import setup_tasks


if __name__ == "__main__":

    logger.info('Bot is starting.')

    setup_tasks()

    executor.start_polling(
        dp, skip_updates=True
    )
