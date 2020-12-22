from bot import dp, types, FSMContext
from motor_client import SingletonClient
from loguru import logger
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime


class Send(StatesGroup):
    payment_platform = State()
    date = State()
    image = State()
    finish = State()


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['send'])
async def send(message: types.Message, state: FSMContext):
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer('Вы не зарегистрированы в системе. Напишите /start')

    markup = await payment_types_markup(user['region'])
    if not markup:
        await message.answer('Казначей еще не настроил реквизиты для оплаты')
        return await state.finish()
    await message.answer('Выберите платформу для оплаты', reply_markup=markup)
    await Send.payment_platform.set()
    await state.update_data(user_id=user['_id'])
    await state.update_data(region_id=user['region'])


async def payment_types_markup(region_id) -> types.InlineKeyboardMarkup:
    db = SingletonClient.get_data_base()
    region = await db.Regions.find_one({'_id': region_id})
    payment_types = region['payment_types']

    markup = types.InlineKeyboardMarkup()
    if not payment_types:
        return False
    for i, payment_type in enumerate(payment_types):
        markup.add(types.InlineKeyboardButton(text=payment_type[0], callback_data=f"{payment_type[0]},{payment_type[1]}"))

    return markup


@dp.callback_query_handler(state=[Send.payment_platform])
async def set_payment_type(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer(f'Реквизиты: <code>{callback_query.data.split(",")[1]}</code>')
    payment_type = callback_query.data.split(',')[0]
    await state.update_data(payment_type=payment_type)

    await callback_query.message.answer('Укажите дату и время платежа в формате <code>dd.mm.yyyy HH:MM</code>')
    await Send.date.set()


@dp.message_handler(state=[Send.date])
async def set_payment_date(message: types.Message, state: FSMContext):
    date = message.text
    try:
        date = datetime.strptime(date, '%d.%m.%Y %H:%M')
        await state.update_data(date=date)
    except ValueError:
        return await message.answer('Дата и время указаны в неправильном формате.\n\n'
                                    'Укажите дату и время платежа в формате <code>dd.mm.yyyy HH:MM</code>\n\n'
                                    'Без нее ваш платеж может быть потерян и не учтен, '
                                    'указывайте время отправки платежа правильно.')

    await message.answer('Пришлите скриншот перевода')
    await Send.image.set()


@dp.message_handler(content_types=types.ContentType.PHOTO, state=[Send.image])
async def image(message: types.Message, state: FSMContext):
    file_id = message.photo[0].file_id  # file id фотографии
    await state.update_data(file_id=file_id)
    db = SingletonClient.get_data_base()
    async with state.proxy() as data:
        user = await db.Users.find_one({'_id': data.get('user_id')})
        string = f'ФИО: {user["second_name"]} {user["first_name"]} {user["third_name"]}\n'
        amount = 600  # todo: добавить взнос частями
        string += f'Размер взноса: {amount}\n'
        string += f'Платформа оплаты: {data.get("payment_type")}\n'
        string += f"Дата платежа: {data.get('date')}"

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
            'type': data.get('payment_type'),
            'status': 'waiting',
            'payment_date': data.get('date')
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
