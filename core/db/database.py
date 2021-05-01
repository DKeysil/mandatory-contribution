from collections.abc import Awaitable
from typing import Callable

from motor import motor_asyncio as motor


class Database:
    _db: motor.AsyncIOMotorDatabase = None

    @classmethod
    def init(cls, uri: str) -> None:
        cls._db = motor.AsyncIOMotorClient(uri).get_default_database()

    @classmethod
    def init_with_database(cls, database: motor.AsyncIOMotorDatabase) -> None:
        cls._db = database

    @classmethod
    async def init_with_database_getter(
            cls,
            getter: Callable[[], Awaitable[motor.AsyncIOMotorDatabase]]
    ) -> None:
        cls.init_with_database(await getter())

    @classmethod
    def get_database(cls) -> motor.AsyncIOMotorDatabase:
        return cls._db

    @classmethod
    def close(cls) -> None:
        if cls._db:
            cls._db.client.close()
