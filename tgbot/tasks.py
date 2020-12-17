import aiocron
from bot import bot, loop
from motor_client import SingletonClient
from loguru import logger
from bson import ObjectId


@aiocron.crontab("0 17 * * *")
async def new_payments():
    logger.info('Началась рассылка о непроверенных взносах')
    db = SingletonClient.get_data_base()
    regions = db.Regions.find({})
    regions = await regions.to_list(length=await db.Regions.count_documents({}))
    string = "У вас есть непроверенные взносы"
    for region in regions:
        payment = await db.Payments.find_one({"status": 'waiting', "region": ObjectId(region['_id'])})
        if payment:
            user_cursor = db.Users.find({
                "region": ObjectId(region["_id"]),
                "treasurer": True
            })
            async for user in user_cursor:
                logger.info(f'send mandatory notification to '
                            f'{user["telegram_id"]} {user["second_name"]} {user["first_name"]}')
                await bot.send_message(user["telegram_id"], text=string)
