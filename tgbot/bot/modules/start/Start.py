from bot import dp, types, FSMContext
from motor_client import SingletonClient
from loguru import logger
from datetime import datetime
from aiogram.dispatcher.filters.state import State, StatesGroup
from bson import ObjectId


class Registration(StatesGroup):
    name = State()
    region = State()
    finish = State()


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['start'])
async def start(message: types.Message):
    logger.info('command: /start')
    telegram_id = message.from_user.id
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({
        "telegram_id": telegram_id
    })
    telegram_name = message.from_user.full_name

    if user:
        result = await db.Users.update_one({"telegram_id": telegram_id}, {"$set": {"telegram_name": telegram_name}})
        logger.info(f'user exist. update_one modified count: {result.modified_count}')
        return await message.answer('Вы уже зарегистрированы')

    await message.answer('Введите <b>Имя</b> и <b>Фамилию</b>')
    await Registration.name.set()


@dp.message_handler(state=[Registration.name])
async def set_name(message: types.Message, state: FSMContext):
    name = message.text.split(' ')
    logger.info(f"Установка имени {name}")

    if len(name) != 2:
        return await message.answer('Введите <b>Имя</b> и <b>Фамилию</b>')

    await state.update_data(first_name=name[0])
    await state.update_data(second_name=name[1])

    markup = await regions_keyboard()
    await message.answer('Выберите регион', reply_markup=markup)
    await Registration.region.set()


@dp.callback_query_handler(state=[Registration.region])
async def handle_region_callback(callback_query: types.CallbackQuery, state: FSMContext):
    region_id = ObjectId(callback_query.data)
    db = SingletonClient.get_data_base()
    region = await db.Regions.find_one({'_id': region_id})
    await state.update_data(region_title=region['title'])
    await state.update_data(region_id=region_id)

    await finish(callback_query.message, state)


async def regions_keyboard() -> types.InlineKeyboardMarkup:
    db = SingletonClient.get_data_base()
    regions = db.Regions.find({})
    regions = await regions.to_list(length=await db.Regions.count_documents({}))
    lst = []
    for i in range(len(regions)):
        if i % 3 == 0:
            lst.append([types.InlineKeyboardButton(text=regions[i]['title'], callback_data=f"{regions[i]['_id']}")])
        else:
            lst[i//3].append(types.InlineKeyboardButton(text=regions[i]['title'], callback_data=f"{regions[i]['_id']}"))
    markup = types.InlineKeyboardMarkup(lst)
    return markup


async def finish(message: types.Message, state: FSMContext):
    string = 'Проверьте введённые данные:\n\n'
    async with state.proxy() as data:
        string += f"Имя Фамилия: {data.get('first_name')} {data.get('second_name')}\n"
        string += f'Регион: {data.get("region_title")}\n'
    await Registration.finish.set()
    await message.answer(string, reply_markup=under_event_keyboard())


def under_event_keyboard():
    markup = types.InlineKeyboardMarkup()

    button = types.InlineKeyboardButton(text="✅ Подтвердить", callback_data='Accept')
    markup.add(button)

    button = types.InlineKeyboardButton(text="❌ Начать заново", callback_data='Restart')
    markup.add(button)
    return markup


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'Accept', state=[Registration.finish])
async def accept_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    db = SingletonClient.get_data_base()

    async with state.proxy() as data:
        result = await db.Users.insert_one({
            'telegram_id': data.get('telegram_id'),
            'first_name': data.get('first_name'),
            'second_name': data.get('second_name'),
            'region': data.get('region_id'),
            'treasurer': False,
            'registration_date': int(datetime.timestamp(datetime.now()))
        })
        logger.info(f'Start by: {callback_query.message.from_user.id}\n'
                    f'insert_one user in db status: {result.acknowledged}')

    await callback_query.message.edit_reply_markup()
    await callback_query.message.answer('Вы успешно зарегистрировались.')
    await state.finish()


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'Restart', state=[Registration.finish])
async def restart_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await Registration.name.set()
    logger.info(f'Start by: {callback_query.message.from_user.id}\nrestarted')
    await callback_query.message.answer('Попробуем ещё раз.\n\nВведите <b>Фамилию Имя Отчество</b>.')
