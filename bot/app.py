from typing import Optional

import click
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher.webhook import (BOT_DISPATCHER_KEY,
                                        get_new_configured_app)
from aiohttp import web

from bot.config import Config
from bot.healthcheck import healthcheck
from core import Database


def setup_middlewares(dp: Dispatcher) -> None:
    pass


def setup_filters(dp: Dispatcher) -> None:
    pass


def register_handlers(dp: Dispatcher) -> None:
    pass


def create_dp(cfg: Config) -> Dispatcher:
    bot = Bot(cfg.BOT_TOKEN, parse_mode='html')
    storage = MongoStorage(uri=cfg.MONGO_URI, db_name=cfg.MONGO_DATABASE)
    dp = Dispatcher(bot, storage=storage)
    return dp


def create_app(cfg: Config) -> web.Application:
    dp = create_dp(cfg)
    app = get_new_configured_app(dp, '/' + cfg.BOT_WH_PATH.strip('/'))

    app['config'] = cfg

    app.router.add_route('GET', '/healthcheck', healthcheck)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app


async def on_startup(app: web.Application) -> None:
    dp: Dispatcher = app[BOT_DISPATCHER_KEY]
    cfg: Config = app['config']

    await Database.init_with_database_getter(dp.storage.get_db)

    await dp.bot.set_webhook(f'{cfg.BOT_DOMAIN}/{cfg.BOT_WH_PATH.strip("/")}')


async def on_cleanup(app: web.Application) -> None:
    dp: Dispatcher = app[BOT_DISPATCHER_KEY]

    await dp.storage.close()
    await dp.storage.wait_closed()

    await dp.bot.session.close()


@click.command()
@click.option(
    '--bot-token',
    metavar='TOKEN', type=str, envvar='BOT_TOKEN',
    help='Token for Telegram Bot API access.'
)
@click.option(
    '--bot-domain',
    metavar='DOMAIN', type=str, envvar='BOT_DOMAIN',
    help='Domain for getting webhooks from Telegram Bot API.'
)
@click.option(
    '--bot-wh-path',
    metavar='PATH', type=str, required=False, envvar='BOT_WH_PATH',
    help=('Path for getting webhooks from Telegram Bot API. '
          'By default, a string of random characters is generated.')
)
@click.option(
    '--mongo-uri',
    metavar='URI', type=str, envvar='MONGO_URI',
    help='Mongo database URI.'
)
@click.option(
    '--mongo-database',
    metavar='NAME', type=str, envvar='MONGO_DATABASE',
    help='Name of mongo database.'
)
def main(
        bot_token: str, bot_domain: str, bot_wh_path: Optional[str],
        mongo_uri: str, mongo_database: str
) -> None:
    kwargs = {'BOT_WH_PATH': bot_wh_path}
    kwargs = {k: v for k, v in kwargs.items() if v}
    cfg = Config(
        bot_token, bot_domain,
        mongo_uri, mongo_database,
        **kwargs
    )
    app = create_app(cfg)
    web.run_app(app)
