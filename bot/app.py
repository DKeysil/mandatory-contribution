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
    storage = MongoStorage(cfg.MONGO_HOST, cfg.MONGO_PORT, cfg.MONGO_DATABASE,
                           username=cfg.MONGO_USER,
                           password=cfg.MONGO_PASSWORD)
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

    await Database.init_with_client_getter(dp.storage.get_client,
                                           cfg.MONGO_DATABASE)

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
    '--mongo-host',
    metavar='HOST', type=str, envvar='MONGO_HOST',
    help='Mongo database host. Default value is "localhost".'
)
@click.option(
    '--mongo-port',
    metavar='PORT', type=int, envvar='MONGO_PORT',
    help='Mongo database port. Default value is 27017.'
)
@click.option(
    '--mongo-database',
    metavar='NAME', type=str, envvar='MONGO_DATABASE',
    help='Name of mongo database.'
)
@click.option(
    '--mongo-user',
    metavar='USERNAME', type=str, envvar='MONGO_USER',
    help='Username for access to mongo database.'
)
@click.option(
    '--mongo-password',
    metavar='PASSWORD', type=str, envvar='MONGO_PASSWORD',
    help='Password for access to mongo database.'
)
def main(
        bot_token: str, bot_domain: str, bot_wh_path: Optional[str],
        mongo_host: str, mongo_port: int, mongo_database: str,
        mongo_user: str, mongo_password: str
) -> None:
    kwargs = {'MONGO_HOST': mongo_host,
              'MONGO_PORT': mongo_port,
              'BOT_WH_PATH': bot_wh_path}
    kwargs = {k: v for k, v in kwargs.items() if v}
    cfg = Config(
        bot_token, bot_domain,
        mongo_database, mongo_user, mongo_password,
        **kwargs
    )
    app = create_app(cfg)
    web.run_app(app)
