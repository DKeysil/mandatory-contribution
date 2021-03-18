from datetime import datetime
from typing import Optional

from bson import ObjectId

from core.motor_client import SingletonClient


db = SingletonClient.get_data_base().Users


async def check_is_user_registered_by_tg_id(tg_id: int) -> bool:
    return bool(await db.count({'telegram_id': tg_id}))


async def update_user_mention_by_tg_id(tg_id: int, mention: str) -> None:
    await db.update_one({'telegram_id': tg_id}, {'$set': {'mention': mention}})


async def create_user(
        tg_id: int, first_name: str, second_name: str, region: ObjectId,
        mention: str,
        federal_region: Optional[str] = None,
        treasurer: bool = False,
        ban: bool = False
) -> None:
    await db.insert_one({
        'telegram_id': tg_id,
        'first_name': first_name,
        'second_name': second_name,
        'region': region,
        'federal_region': federal_region,
        'treasurer': treasurer,
        'registration_date': int(datetime.timestamp(datetime.now())),
        'mention': mention,
        'ban': ban
    })
