from bot import dp, types, FSMContext
from motor_client import SingletonClient
from loguru import logger
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime


class Send(StatesGroup):
    payment_platform = State()
    image = State()
    finish = State()


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['send'])
async def send(message: types.Message, state: FSMContext):
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer('Вы не зарегистрированы в системе. Напишите /start')

    markup = await payment_types_markup(user['region'])
    await message.answer('Выберите платформу для оплаты', reply_markup=markup)
    await Send.payment_platform.set()
    await state.update_data(user_id=user['_id'])


async def payment_types_markup(region_id) -> types.InlineKeyboardMarkup:
    db = SingletonClient.get_data_base()
    region = await db.Regions.find_one({'_id': region_id})
    payment_types = region['payment_types']

    markup = types.InlineKeyboardMarkup()
    for payment_type in payment_types:
        markup.add(types.InlineKeyboardButton(text=payment_type, callback_data=payment_type))

    return markup


@dp.callback_query_handler(state=[Send.payment_platform])
async def set_payment_type(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    payment_type = callback_query.data
    await state.update_data(payment_type=payment_type)

    await callback_query.message.answer('Пришлите скриншот перевода')
    await Send.image.set()


@dp.message_handler(content_types=types.ContentType.PHOTO, state=[Send.image])
async def image(message: types.Message, state: FSMContext):
    file_id = message.photo[0].file_id  # file id фотографии
    await state.update_data(file_id=file_id)
    db = SingletonClient.get_data_base()
    async with state.proxy() as data:
        user = await db.Users.find_one({'_id': data.get('user_id')})
        string = f'Имя и фамилия: {user["first_name"]} {user["second_name"]}\n'
        amount = 600  # todo: добавить взнос частями
        string += f'Размер взноса: {amount}\n'
        string += f'Платформа оплаты: {data.get("payment_type")}\n'

    await message.answer_photo(file_id,
                               caption=f'Проверьте отправленные данные:\n\n{string}',
                               reply_markup=under_event_keyboard())

    await Send.finish.set()


def under_event_keyboard():
    markup = types.InlineKeyboardMarkup()

    button = types.InlineKeyboardButton(text="✅ Подтвердить", callback_data='Accept')
    markup.add(button)

    button = types.InlineKeyboardButton(text="❌ Отменить", callback_data='Cancel')
    markup.add(button)
    return markup


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'Accept', state=[Send.finish])
async def accept_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    db = SingletonClient.get_data_base()

    async with state.proxy() as data:
        result = await db.Payments.insert_one({
            'payer': data.get('user_id'),
            'amount': 600,  # Стандартно 600, потом todo: добавить взнос частями
            'region': data.get('region_id'),
            'date': int(datetime.timestamp(datetime.now())),
            'file_id': data.get('file_id'),
            'type': data.get('payment_type')
        })
        logger.info(f'Start by: {callback_query.message.from_user.id}\n'
                    f'insert_one user in db status: {result.acknowledged}')

    await callback_query.message.edit_reply_markup()
    await callback_query.message.answer('Вы отправили информацию о взносе.')
    await state.finish()


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'Cancel', state=[Send.finish])
async def cancel_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.finish()
    logger.info(f'Start by: {callback_query.message.from_user.id}\ncancel')
    await callback_query.message.answer('Отправка взноса была отменена')
