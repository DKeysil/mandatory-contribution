import os
from collections.abc import Iterator

import pytest
from motor import motor_asyncio as motor

from core.db import Database


@pytest.fixture
async def db() -> Iterator[motor.AsyncIOMotorDatabase]:
    Database.init(os.environ['MONGO_URI'])
    db = Database.get_database()
    yield db
    await db.client.drop_database(db.name)
