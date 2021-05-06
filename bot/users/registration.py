import re
import time

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot import handlers
from core.db import models


START_MSG = ('Для использования бота необходимо зарегистрироваться.\n'
             'Отправьте <code>Фамилию Имя</code> в именительном падеже.')
INCORRECT_NAME_MSG = 'Некорректные фамилия и имя. Попробуйте ещё раз.'
CHOOSE_REGION_MSG = ('Выберите ваш регион. Если его нет в списке, попросите '
                     'вашего казначея его добавить и обновите список.\n\n')
INPUT_REFINED_REGION_MSG = 'Отправьте название вашего региона.'


class Registration(StatesGroup):
    name = State()
    region = State()
    refined_region = State()
    finish = State()


def register_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(
        parse_region, CommandStart(deep_link=re.compile(r'region-\d+')),
        state=Registration.region
    )  # дип линкинг должен быть выше простого /start
    dp.register_message_handler(start_cmd, commands='start', state='*')
    dp.register_callback_query_handler(start_cq, text='start', state='*')
    dp.register_message_handler(parse_name, state=Registration.name)
    dp.register_callback_query_handler(refresh_regions,
                                       text='refresh',
                                       state=Registration.region)
    dp.register_message_handler(parse_refined_region,
                                state=Registration.refined_region)
    dp.register_callback_query_handler(create_user,
                                       text='confirm',
                                       state=Registration.finish)


async def start_cmd(msg: types.Message, state: FSMContext):
    """
    Хендлер команды /start, когда пользователь не зарегистрирован.
    """
    await state.finish()
    await msg.answer(START_MSG)
    await Registration.name.set()


async def start_cq(cq: types.CallbackQuery, state: FSMContext):
    """
    Хендлер callback'а start, когда пользователь не зарегистрирован.
    """
    await state.finish()
    await cq.message.edit_text(START_MSG)
    await Registration.name.set()


async def parse_name(msg: types.Message, state: FSMContext):
    """
    Хендлер сообщения с состоянием Registration.name.
    """
    try:
        last_name, first_name = msg.text.title().split(' ')
    except ValueError:
        await msg.answer(INCORRECT_NAME_MSG)
        return
    await state.update_data({'first_name': first_name, 'last_name': last_name})
    text = CHOOSE_REGION_MSG + await _get_region_list(msg.bot)
    rm = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton('Обновить список', callback_data='refresh')
    ]])
    await msg.answer(text, reply_markup=rm)
    await Registration.region.set()


async def _get_region_list(bot: Bot) -> str:
    """
    Получение списка регионов из БД и преобразование их в строку ссылок
    с дип линками для отображения в сообщении.
    """
    bot_username = (await bot.me).username
    return '\n'.join([f'<a href="t.me/{bot_username}?start=region-'
                      f'{region["_id"]}">{region["title"]}</a>'
                      async for region in models.Region.iter()])


async def refresh_regions(cq: types.CallbackQuery):
    """
    Хендлер callback'а refresh с состоянием Registration.region.
    """
    text = CHOOSE_REGION_MSG + await _get_region_list(cq.bot)
    rm = cq.message.reply_markup
    await cq.message.edit_text(text, reply_markup=rm)
    await cq.answer('Список регионов обновлён.')


async def parse_region(msg: types.Message, state: FSMContext):
    """
    Хендлер дип линка с состоянием Registration.region.
    """
    try:
        region_id = int(msg.text.split(' ')[1].split('-')[1])
    except (IndexError, ValueError):
        return
    region = await models.Region.get({'_id': region_id})
    if not region:
        return
    await state.update_data({'region_id': region_id,
                             'region_title': region['title']})
    if region_id == 0:
        await msg.answer(INPUT_REFINED_REGION_MSG)
        await Registration.refined_region.set()
        return
    await _finish(msg, state)


async def parse_refined_region(msg: types.Message, state: FSMContext):
    """
    Хендлер сообщения с состоянием Registration.refined_region.
    """
    await state.update_data({'refined_region': msg.text.title()})
    await _finish(msg, state)


async def _finish(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('refined_region'):
        data.update({'region_title': data['refined_region']})
    text = ('Пожалуйста, подтвердите правильность отправленных данных.\n'
            'ФИ: {last_name} {first_name}\n'
            'Регион: {region_title}').format(**data)
    rm = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(u'\u2705 Подтвердить',
                                    callback_data='confirm')],
        [types.InlineKeyboardButton(u'\u274C Начать сначала',
                                    callback_data='start')]
    ])
    await msg.answer(text, reply_markup=rm)
    await Registration.finish.set()


async def create_user(cq: types.CallbackQuery, state: FSMContext):
    """
    Хендлер callback'а accept с состоянием Registration.finish.
    """
    data = await state.get_data()
    data.pop('region_title')
    data.update({'tg_id': int(cq.from_user.id),
                 'tg_mention': cq.from_user.mention,
                 'treasurer': False,
                 'banned': False,
                 'reg_date': int(time.time())})
    await models.User.create(data)
    await state.finish()
    await cq.message.edit_text(handlers.HELP_MSG)
