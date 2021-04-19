import random
import string
import time

import bson
import pytest
from motor import motor_asyncio as motor

from core.db import models


pytestmark = pytest.mark.asyncio


def generate_user_data() -> dict:
    return {'tg_id': int(''.join(random.choices(string.digits, k=6))),
            'tg_mention': '@' + ''.join(random.choices(string.ascii_letters,
                                                       k=10)),
            'first_name': ''.join(random.choices(string.ascii_letters,
                                                 k=10)).title(),
            'last_name': ''.join(random.choices(string.ascii_letters,
                                                k=10)).title(),
            'region_id': random.randint(1, 100),
            'reg_date': int(time.time())}


@pytest.fixture
def user_data() -> dict:
    return generate_user_data()


@pytest.fixture
async def users(db: motor.AsyncIOMotorDatabase) -> list[dict]:
    users = [generate_user_data() for _ in range(10)]
    await db.users.insert_many(users)
    return users


@pytest.fixture
async def region_and_user(
        user_data: dict, db: motor.AsyncIOMotorDatabase
) -> tuple[dict, dict]:
    await db.users.insert_one(user_data)
    region_data = {'_id': user_data['region_id'],
                   'title': 'Богом забытый регион'}
    await db.regions.insert_one(region_data)
    return region_data, user_data


class TestBaseModels:
    async def test_init_and_properties(self, db):
        user_id = bson.ObjectId()
        user = models.User(user_id)
        assert user.collection
        assert user.id == user_id

    async def test_create(
            self, user_data: dict, db: motor.AsyncIOMotorDatabase
    ):
        user_id = await models.User.create(user_data)
        user = await db.users.find_one({'_id': user_id})
        assert user == user_data

    async def test_count(self, users: list[dict]):
        assert await models.User.count() == len(users)

    async def test_get_multiple(self, users: list[dict]):
        assert await models.User.get_multiple() == users

    async def test_iter(self, users: list[dict]):
        assert [user async for user in models.User.iter()] == users

    async def test_get(self, users: list[dict]):
        assert await models.User.get({'_id': users[0]['_id']}) == users[0]

    async def test_update(self, users: list[dict], user_data: dict,
                          db: motor.AsyncIOMotorDatabase):
        user = models.User(users[0]['_id'])
        await user.update(user_data)
        user = await db.users.find_one({'_id': users[0]['_id']})
        user_id = user.pop('_id')
        assert user_id == users[0]['_id']
        assert user == user_data

    async def test_delete(self, users: list[dict],
                          db: motor.AsyncIOMotorDatabase):
        await models.User(users[0]['_id']).delete()
        assert await db.users.find_one({'_id': users[0]['_id']}) is None


class TestRegion:
    async def test_init_and_properties(self, db):
        region_id = random.randint(1, 100)
        region = models.Region(region_id)
        assert region.id == region_id

    async def test_get_users(self, users: list[dict],
                             db: motor.AsyncIOMotorDatabase):
        region_id = 78
        for user in users:
            user.update({'region_id': region_id})
        await db.users.update_many({}, {'$set': {'region_id': region_id}})
        assert await models.Region(region_id).get_users() == users

    async def test_get_user(self, users: list[dict],
                            db: motor.AsyncIOMotorDatabase):
        region_id = 78
        users[0].update({'region_id': region_id})
        await db.users.update_one({'_id': users[0]['_id']},
                                  {'$set': {'region_id': region_id}})
        assert await models.Region(
            region_id
        ).get_user({'_id': users[0]['_id']}) == users[0]


class TestUser:
    async def test_get_region(self, region_and_user: tuple[dict, dict]):
        region, user = region_and_user
        assert await models.User(user['_id']).get_region() == region
