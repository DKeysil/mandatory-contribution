from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bson import ObjectId
from loguru import logger

from core.motor_client import SingletonClient


class Registration(StatesGroup):
    name = State()
    region = State()
    federal_region = State()
    finish = State()


async def start_cmd(message: types.Message):
    logger.info('command: /start')
    telegram_id = message.from_user.id
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({
        "telegram_id": telegram_id
    })

    if user:
        result = await db.Users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"mention": message.from_user.mention}}
        )
        logger.info(
            f'user exist. update_one modified count: {result.modified_count}'
        )
        return await message.answer('Вы уже зарегистрированы')

    await message.answer('Введите <b>Фамилию Имя</b>')
    await Registration.name.set()


async def set_name_msg(message: types.Message, state: FSMContext):
    name = message.text.split(' ')
    logger.info(f"Установка имени {name}")

    if len(name) != 2:
        return await message.answer('Введите <b>Фамилию Имя</b>')

    await state.update_data(second_name=name[0])
    await state.update_data(first_name=name[1])
    await state.update_data(mention=message.from_user.mention)

    markup = await regions_keyboard()
    await message.answer(
        ('Выберите регион.\n'
         'Если вашего региона нет, попросите казначея добавить ваш регион и '
         'обновите список регионов командой /refresh.'),
        reply_markup=markup
    )
    await Registration.region.set()


async def refresh_regions_list_cmd(message: types.Message, _: FSMContext):
    markup = await regions_keyboard()
    await message.answer(
        ('Выберите регион.\n'
         'Если вашего региона нет, попросите казначея добавить ваш регион и '
         'обновите список регионов командой /refresh.'),
        reply_markup=markup
    )


async def handle_region_cq(callback_query: types.CallbackQuery,
                           state: FSMContext):
    logger.info(f'Выбор региона {callback_query.data}')
    region_id = ObjectId(callback_query.data)
    db = SingletonClient.get_data_base()
    region = await db.Regions.find_one({'_id': region_id})
    await state.update_data(region_title=region['title'])
    await state.update_data(region_id=region_id)

    if region.get("title") == "Федеральный регион":
        await callback_query.message.answer("Пришлите название вашего региона")
        await Registration.federal_region.set()
        return await callback_query.answer()

    await finish(callback_query.message, state)
    await callback_query.answer()


async def set_federal_region_msg(message: types.Message, state: FSMContext):
    logger.info(f"from {message.from_user.id} federal region {message.text}")
    await state.update_data(federal_region=message.text)
    await message.reply("Принято")
    await finish(message, state)


async def accept_cq(callback_query: types.CallbackQuery, state: FSMContext):
    db = SingletonClient.get_data_base()
    logger.info(f"from {callback_query.from_user.id}")

    async with state.proxy() as data:
        result = await db.Users.insert_one({
            'telegram_id': callback_query.from_user.id,
            'first_name': data.get('first_name'),
            'second_name': data.get('second_name'),
            'region': data.get('region_id'),
            'federal_region': data.get('federal_region'),
            'treasurer': False,
            'registration_date': int(datetime.timestamp(datetime.now())),
            'mention': data.get('mention'),
            'ban': False
        })
        logger.info(f'Start by: {callback_query.from_user.id}\n'
                    f'insert_one user in db status: {result.acknowledged}')

    await callback_query.message.edit_reply_markup()
    introduction_string = ('Вы успешно зарегистрировались.\n\n'
                           "Для отправки взноса воспользуйтесь командой "
                           "/send\nДля отмены состояния напишите /cancel")
    await callback_query.message.answer(introduction_string)
    await state.finish()
    await callback_query.answer()


async def restart_cq(callback_query: types.CallbackQuery, _: FSMContext):
    await Registration.name.set()
    logger.info(f'Start by: {callback_query.from_user.id}\nrestarted')
    await callback_query.message.answer(
        'Попробуем ещё раз.\n\nВведите <b>Фамилию Имя</b>.'
    )
    await callback_query.answer()


async def regions_keyboard() -> types.InlineKeyboardMarkup:
    db = SingletonClient.get_data_base()
    regions = db.Regions.find({})
    regions = await regions.to_list(
        length=await db.Regions.count_documents({})
    )
    logger.info(regions)
    lst = []
    for i in range(len(regions)):
        if i % 3 == 0:
            lst.append([types.InlineKeyboardButton(
                text=regions[i]['title'], callback_data=f"{regions[i]['_id']}"
            )])
        else:
            lst[i//3].append(types.InlineKeyboardButton(
                text=regions[i]['title'], callback_data=f"{regions[i]['_id']}"
            ))

    markup = types.InlineKeyboardMarkup()
    for row in lst:
        markup.row(*row)
    return markup


async def finish(message: types.Message, state: FSMContext):
    logger.info(f"from {message.from_user.id}")
    string = 'Проверьте введённые данные:\n\n'
    async with state.proxy() as data:
        string += f"ФИ: {data.get('second_name')} {data.get('first_name')}\n"
        string += f'Регион: {data.get("region_title")}\n'
        if data.get("federal_region"):
            string += f"Уточненный регион: {data.get('federal_region')}"
    await Registration.finish.set()
    await message.answer(string, reply_markup=under_event_keyboard())


def under_event_keyboard():
    markup = types.InlineKeyboardMarkup()

    button = types.InlineKeyboardButton(text="✅ Подтвердить",
                                        callback_data='Accept')
    markup.add(button)

    button = types.InlineKeyboardButton(text="❌ Начать заново",
                                        callback_data='Restart')
    markup.add(button)
    return markup
