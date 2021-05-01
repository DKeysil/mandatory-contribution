import random
import string
from dataclasses import dataclass


__all__ = ('Config',)


def _generate_random_str(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits,
                                  k=length))


@dataclass
class Config:
    BOT_TOKEN: str
    BOT_DOMAIN: str
    MONGO_URI: str
    MONGO_DATABASE: str
    BOT_WH_PATH: str = _generate_random_str(12)
