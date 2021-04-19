from typing import Union

import bson

from core.db.models.base import BaseSepModel


__all__ = ('Region', 'User')


class Region(BaseSepModel):
    """
    Пример данных:
    {
       _id: 74,
       title: "Челябинская область"
    }
    """
    __collection__ = 'regions'

    def __init__(self, _id: int):
        self._id = _id

    @property
    def id(self) -> int:
        return self._id

    async def get_users(
            self, query: dict = None, limit: int = 20
    ) -> list[dict]:
        query = query if query else {}
        query |= {'region_id': self._id}
        return await User.get_multiple(query=query, limit=limit)

    async def get_user(self, query: dict) -> dict:
        query |= {'region_id': self._id}
        return await User.get(query)

    async def get_contributions(
            self, query: dict = None, limit: int = 20
    ) -> list[dict]:
        """
        TODO
        """
        pass

    async def get_contribution(
            self, contribution_id: Union[bson.ObjectId, str]
    ) -> dict:
        """
        TODO
        """
        pass

    async def create_contribution(self, data: dict) -> bson.ObjectId:
        """
        TODO
        """
        pass

    async def get_requisites(self, query: dict = None) -> list[dict]:
        """
        TODO
        """
        pass

    async def get_requisite(
            self, requisite_id: Union[bson.ObjectId, str]
    ) -> dict:
        """
        TODO
        """
        pass

    async def create_requisite(self, data: dict) -> bson.ObjectId:
        """
        TODO
        """
        pass


class User(BaseSepModel):
    """
    Пример данных:
    {
       _id: ObjectID(607c17d7049276af47adff05),
       tg_id: 246256258,
       tg_mention: "@DKeysil",
       first_name: "Дмитрий",
       last_name: "Кисель",
       region_id: 78,
       treasurer: false,
       banned: false,
       reg_date: 1618745803
    }
    """
    __collection__ = 'users'

    async def get_region(self) -> dict:
        user = await self.get({'_id': self._id})
        return await Region.get({'_id': user['region_id']})

    async def get_payments(self, contribution_id: bson.ObjectId) -> list[dict]:
        """
        TODO
        """
        pass
