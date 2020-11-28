from bot import dp, types
from motor_client import SingletonClient
from loguru import logger
from datetime import datetime


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['start'])
async def start(message: types.Message):
    logger.info('command: /start')
    telegram_id = message.from_user.id
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({
        "telegram_id": telegram_id
    })
    telegram_name = message.from_user.full_name

    if user:
        result = await db.Users.update_one({"telegram_id": telegram_id}, {"$set": {"telegram_name": telegram_name}})
        logger.info(f'user exist. update_one modified count: {result.modified_count}')
    else:
        # TODO: Предлагать пользователю заполнить необязательные данные
        user_data = {"telegram_id": telegram_id,
                     "telegram_name": telegram_name,
                     'first_name': None,
                     'second_name': None,
                     'region': None,
                     'treasurer': False,
                     'registration_date': int(datetime.timestamp(datetime.now()))
                     }

        result = await db.Users.insert_one(user_data)
        logger.info(f'insert user. insert_one result: {result.acknowledged}')

    await message.reply('Добро пожаловать.')
