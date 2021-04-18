from collections.abc import Iterator
from typing import Union

import bson
from motor import motor_asyncio as motor

from core.db.database import Database
from core.db.models.absctract import AbstractModel


__all__ = ('BaseModel', 'BaseSepModel')


class BaseModel(AbstractModel):
    """
    Базовый класс для всех моделей.
    """
    @property
    def collection(self) -> motor.AsyncIOMotorCollection:
        return self.get_collection()

    @property
    def id(self) -> bson.ObjectId:
        return self._id

    async def update(self, data: dict) -> None:
        await self.collection.update_one({'_id': self._id}, {'$set': data})

    async def delete(self) -> None:
        await self.collection.delete_one({'_id': self._id})


class BaseSepModel(BaseModel):
    """
    Базовый класс для моделей, не зависящих от других моделей.
    """
    def __init__(self, _id: Union[bson.ObjectId, str]):
        super().__init__()
        self._id = bson.ObjectId(_id)

    @classmethod
    def get_collection(cls) -> motor.AsyncIOMotorCollection:
        return Database.get_database()[cls.__collection__]

    @classmethod
    async def count(cls, query: dict = None) -> int:
        query = query if query else {}
        return await cls.get_collection().count_documents(query)

    @classmethod
    async def get_multiple(
            cls, query: dict = None, limit: int = 20
    ) -> list[dict]:
        query = query if query else {}
        return await cls.get_collection().find(query).to_list(limit)

    @classmethod
    async def iter(cls, query: dict = None) -> Iterator[dict]:
        query = query if query else {}
        async for document in cls.get_collection().find(query):
            yield document

    @classmethod
    async def get(cls, query: dict) -> dict:
        return await cls.get_collection().find_one(query)

    @classmethod
    async def create(cls, data: dict) -> bson.ObjectId:
        return (await cls.get_collection().insert_one(data)).inserted_id
