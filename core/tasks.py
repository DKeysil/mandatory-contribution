import aiocron
from bson import ObjectId
from loguru import logger

from bot import bot
from core.motor_client import SingletonClient


async def new_payments():
    logger.info('Началась рассылка о непроверенных взносах')
    db = SingletonClient.get_data_base()
    regions = db.Regions.find({})
    regions = await regions.to_list(
        length=await db.Regions.count_documents({})
    )
    string = 'У вас есть непроверенные взносы'
    for region in regions:
        payment = await db.Payments.find_one(
            {'status': 'waiting', 'region': ObjectId(region['_id'])}
        )
        if payment:
            user_cursor = db.Users.find({
                'region': ObjectId(region['_id']),
                'treasurer': True
            })
            async for user in user_cursor:
                logger.info('send mandatory notification to %s %s %s',
                            user['telegram_id'],
                            user['second_name'],
                            user['first_name'])
                await bot.send_message(user['telegram_id'], text=string)


def setup_tasks() -> None:
    aiocron.crontab('0 17 * * *', func=new_payments)
