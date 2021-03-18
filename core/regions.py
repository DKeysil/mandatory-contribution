from typing import List

from bson import ObjectId

from core.motor_client import SingletonClient


db = SingletonClient.get_data_base().Regions


async def get_regions_list() -> List[dict]:
    regions = await db.find({})
    return await regions.to_list(length=await db.count_documents({}))


async def get_region_by_id(document_id: ObjectId) -> dict:
    return await db.find({'_id': document_id})
