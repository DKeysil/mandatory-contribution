import abc
from collections.abc import Iterator
from typing import Any

import bson
from motor import motor_asyncio as motor


class AbstractModel(abc.ABC):
    __collection__: str
    _id: Any

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @property
    @abc.abstractmethod
    def collection(self) -> motor.AsyncIOMotorCollection:
        pass

    @property
    @abc.abstractmethod
    def id(self):
        pass

    @classmethod
    @abc.abstractmethod
    def get_collection(cls, *args, **kwargs) -> motor.AsyncIOMotorCollection:
        pass

    @classmethod
    @abc.abstractmethod
    async def count(cls, *args, **kwargs) -> int:
        pass

    @classmethod
    @abc.abstractmethod
    async def get_multiple(cls, *args, **kwargs) -> list[dict]:
        pass

    @classmethod
    @abc.abstractmethod
    async def iter(cls, *args, **kwargs) -> Iterator[dict]:
        pass

    @classmethod
    @abc.abstractmethod
    async def get(cls, *args, **kwargs) -> dict:
        pass

    @classmethod
    @abc.abstractmethod
    async def create(cls, *args, **kwargs) -> bson.ObjectId:
        pass

    @abc.abstractmethod
    async def update(self, data: dict) -> None:
        pass

    @abc.abstractmethod
    async def delete(self) -> None:
        pass
