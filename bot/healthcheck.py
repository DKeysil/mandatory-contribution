from aiogram import Dispatcher
from aiogram.dispatcher.webhook import BOT_DISPATCHER_KEY
from aiohttp import web

from bot.config import Config
from core import Database


__all__ = ('healthcheck',)


CONTENT_TYPE = 'text/plain'


async def healthcheck(request: web.Request) -> web.Response:
    dp: Dispatcher = request.app[BOT_DISPATCHER_KEY]
    cfg: Config = request.app['config']

    try:
        await Database.get_database().list_collection_names()
        webhook_info = await dp.bot.get_webhook_info()
    except Exception as e:
        raise web.HTTPInternalServerError(body=str(e),
                                          content_type=CONTENT_TYPE)

    if f'{cfg.BOT_DOMAIN}/{cfg.BOT_WH_PATH.strip("/")}' != webhook_info.url:
        raise web.HTTPInternalServerError(body='Incorrect webhook.',
                                          content_type=CONTENT_TYPE)

    return web.Response(body='ok', content_type=CONTENT_TYPE)
