from loguru import logger

from app.bot import start_polling
from app.tasks import create_cron_tasks


if __name__ == '__main__':
    logger.info('Bot is starting.')
    create_cron_tasks()
    start_polling()
