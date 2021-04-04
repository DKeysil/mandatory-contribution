from datetime import datetime
from typing import Optional

from bson import ObjectId

from core.motor_client import SingletonClient


db = SingletonClient.get_data_base().Users


async def get_user_by_tg_id(tg_id: int) -> Optional[dict]:
    return await db.find_one({'telegram_id': tg_id})


async def get_user_by_tg_username(username: str) -> Optional[dict]:
    return await db.find_one({'telegram_username': username})


async def create_user(
        tg_id: int, first_name: str, last_name: str, region: ObjectId,
        tg_username: Optional[str] = None,
        federal_region: Optional[str] = None,
        treasurer: bool = False,
        ban: bool = False
) -> ObjectId:
    return await db.insert_one({
        'telegram_id': tg_id,
        'telegram_username': tg_username,
        'first_name': first_name,
        'last_name': last_name,
        'region': region,
        'federal_region': federal_region,
        'treasurer': treasurer,
        'registration_date': datetime.utcnow(),
        'ban': ban
    })
