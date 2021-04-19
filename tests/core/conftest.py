import os
from collections.abc import Iterator

import pytest
from motor import motor_asyncio as motor

from core.db import Database


@pytest.fixture
async def db() -> Iterator[motor.AsyncIOMotorDatabase]:
    Database.init(os.environ['MONGO_URI'], os.environ['MONGO_DB'])
    yield Database.get_database()
    await Database.get_client().drop_database(os.environ['MONGO_DB'])
