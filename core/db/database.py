from collections.abc import Awaitable
from typing import Callable

from motor import motor_asyncio as motor


class Database:
    _client: motor.AsyncIOMotorClient = None
    _db: str = None

    @classmethod
    def init(cls, uri: str, database: str) -> None:
        cls._client = motor.AsyncIOMotorClient(uri)
        cls._db = database

    @classmethod
    def init_with_client(
            cls, client: motor.AsyncIOMotorClient, database: str
    ) -> None:
        cls._client = client
        cls._db = database

    @classmethod
    async def init_with_client_getter(
            cls,
            getter: Callable[[], Awaitable[motor.AsyncIOMotorClient]],
            database: str
    ) -> None:
        cls.init_with_client(await getter(), database)

    @classmethod
    def get_client(cls) -> motor.AsyncIOMotorClient:
        return cls._client

    @classmethod
    def get_database(cls) -> motor.AsyncIOMotorDatabase:
        return cls.get_client()[cls._db]

    @classmethod
    def close(cls) -> None:
        if cls._client:
            cls._client.close()
