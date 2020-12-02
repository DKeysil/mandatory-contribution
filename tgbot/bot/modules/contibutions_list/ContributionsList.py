from bot import dp, types, FSMContext
from motor_client import SingletonClient
from loguru import logger
from bson.objectid import ObjectId
from datetime import datetime


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['list'])
async def contributions_list(message: types.Message):
    logger.info('check contributions_list')
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer('Вы не зарегистрированы в системе. Напишите /start')

    if not user.get('treasurer'):
        return await message.answer('Вы не казначей.')

    string = 'Выбери список каких платежей вы хотите получить'

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='✅ Список одобренных платежей', callback_data='conlist,accepted,show'))
    markup.add(types.InlineKeyboardButton(text='🔥 Список отклоненных платежей', callback_data='conlist,declined,show'))
    markup.add(types.InlineKeyboardButton(text='❌ Список забанненых пользователей', callback_data='conlist,banned,show'))

    await message.answer(string, reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('conlist') and
                           callback_query.data.endswith('show'))
async def show_list(callback_query: types.CallbackQuery):
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': callback_query.from_user.id})
    region = await db.Regions.find_one({'_id': user['region']})
    status = callback_query.data.split(',')[1]
    payments = await get_contributions_list(region['_id'], status, 0)
    if not payments:
        return await callback_query.answer('Платежи не найдены')

    markup = types.InlineKeyboardMarkup()
    for payment in payments:
        payer = await db.Users.find_one({'_id': payment['payer']})
        fio = f"{payer['second_name']} {payer['first_name'][:1]}.{payer['third_name'][:1]}."
        markup.add(types.InlineKeyboardButton(text=f"{fio} {payment['payment_date']}", callback_data=f"{payment['_id']}"))

    if await get_contributions_list(region['_id'], status, 1):
        button_1 = types.InlineKeyboardButton(text="❌", callback_data=f'conlist,n,0,{status}')
        button_2 = types.InlineKeyboardButton(text="➡️", callback_data=f'conlist,r,1,{status}')
        markup.row(button_1, button_2)

    markup.add(types.InlineKeyboardButton(text='Вернуться', callback_data=f"conlist,back"))
    string = 'Выберите платеж для работы с ним'
    await callback_query.message.edit_text(string, reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.split(',')[0] == 'conlist' and
                           callback_query.data.split(',')[1] == 'back')
async def handle_conlist_callback_query(callback_query: types.CallbackQuery):
    string = 'Выбери список каких платежей вы хотите получить'

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='✅ Список одобренных платежей', callback_data='conlist,accepted,show'))
    markup.add(types.InlineKeyboardButton(text='🔥 Список отклоненных платежей', callback_data='conlist,declined,show'))
    markup.add(
        types.InlineKeyboardButton(text='❌ Список забанненых пользователей', callback_data='conlist,banned,show'))
    # todo: добавить вывод забанненых пользователей

    await callback_query.message.edit_text(string, reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.split(',')[0] == 'conlist')
async def handle_conlist_callback_query(callback_query: types.CallbackQuery):
    """
    Обработчик нажатия на кнопку под сообщением влево или вправо.
    Лямбда проверяет, чтобы обрабатывалось только y кнопки
    Args:
        callback_query (types.CallbackQuery): Документация на сайте телеграма
    """

    # todo: добавить обработку нажатия на платежи
    split_data = callback_query.data.split(',')
    if split_data[1] == 'n':
        return await callback_query.answer(text='Там больше ничего нет...')

    db = SingletonClient.get_data_base()
    page = int(split_data[2])
    status = split_data[3]
    logger.info(f"contibutions list page {page} status {status}")

    user = await db.Users.find_one({'telegram_id': callback_query.from_user.id})
    region = await db.Regions.find_one({'_id': user['region']})
    payments = await get_contributions_list(region['_id'], status, page)

    markup = types.InlineKeyboardMarkup()
    for payment in payments:
        payer = await db.Users.find_one({'_id': payment['payer']})
        fio = f"{payer['second_name']} {payer['first_name'][:1]}.{payer['third_name'][:1]}."
        markup.add(
            types.InlineKeyboardButton(text=f"{fio} {payment['payment_date']}", callback_data=f"{payment['_id']}"))

    # Проверяет, есть ли на предыдущих страницах.
    _payments = await get_contributions_list(region['_id'], status, page - 1)
    if _payments:
        left_button = types.InlineKeyboardButton(
            text='⬅️', callback_data=f'conlist,l,{page - 1},{status}')
    else:
        left_button = types.InlineKeyboardButton(
            text='❌', callback_data=f'conlist,n,{page},{status}')

    # Проверяет, есть ли пары на следующих страницах.
    _payments = await get_contributions_list(region['_id'], status, page + 1)
    if _payments:
        right_button = types.InlineKeyboardButton(
            text='➡️', callback_data=f'conlist,r,{page + 1},{status}')
    else:
        right_button = types.InlineKeyboardButton(
            text='❌', callback_data=f'conlist,n,{page},{status}')

    markup.row(left_button, right_button)

    markup.add(types.InlineKeyboardButton(text='Вернуться', callback_data=f"conlist,back"))
    _message = await callback_query.message.edit_reply_markup(reply_markup=markup)
    await callback_query.answer()


async def get_contributions_list(region_id, status, page):
    db = SingletonClient.get_data_base()
    logger.info(f"get contrib list region_id {region_id} status {status} page {page}")
    contributions_cursor = db.Payments.find({
        "region": ObjectId(region_id),
        'status': status
    })

    contrib_list = await contributions_cursor.to_list(length=await db.Payments.count_documents({}))

    try:
        return contrib_list[page * 5: page * 5 + 5]
    except IndexError:
        return []