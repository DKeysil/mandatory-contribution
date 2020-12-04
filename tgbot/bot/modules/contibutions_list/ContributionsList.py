from bot import dp, types, FSMContext
from motor_client import SingletonClient
from loguru import logger
from bson.objectid import ObjectId
from datetime import datetime
from bot.modules.check_contributions.CheckContributions import handle_payment_callback_func


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
    page = 0
    payments = await get_contributions_list(region['_id'], status, 0)
    if not payments:
        return await callback_query.answer('Платежи не найдены')

    markup = types.InlineKeyboardMarkup()
    for payment in payments:
        payer = await db.Users.find_one({'_id': payment['payer']})
        fio = f"{payer['second_name']} {payer['first_name'][:1]}.{payer['third_name'][:1]}."
        markup.add(types.InlineKeyboardButton(text=f"{fio} {payment['payment_date']}", callback_data=f"conlist,payment,{payment['_id']},{page},{status}"))

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


@dp.callback_query_handler(lambda callback_query: callback_query.data.split(',')[0] == 'conlist' and
                           callback_query.data.split(',')[1] in ['r', 'l', 'n'])
async def handle_conlist_callback_query(callback_query: types.CallbackQuery):
    """
    Обработчик нажатия на кнопку под сообщением влево или вправо.
    Лямбда проверяет, чтобы обрабатывалось только y кнопки
    Args:
        callback_query (types.CallbackQuery): Документация на сайте телеграма
    """

    # todo: добавить обработку нажатия на платежи
    markup = await handle_conlist_callback_query_string_markup_generator(callback_query)
    _message = await callback_query.message.edit_reply_markup(reply_markup=markup)
    await callback_query.answer()


async def handle_conlist_callback_query_string_markup_generator(callback_query: types.CallbackQuery):
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
            types.InlineKeyboardButton(text=f"{fio} {payment['payment_date']}",
                                       callback_data=f"conlist,payment,{payment['_id']},{page},{status}"))

    # Проверяет, есть ли на предыдущих страницах.
    _payments_l = await get_contributions_list(region['_id'], status, page - 1)
    # Проверяет, есть ли пары на следующих страницах.
    _payments_r = await get_contributions_list(region['_id'], status, page + 1)
    if _payments_r or _payments_l:
        if _payments_l:
            left_button = types.InlineKeyboardButton(
                text='⬅️', callback_data=f'conlist,l,{page - 1},{status}')
        else:
            left_button = types.InlineKeyboardButton(
                text='❌', callback_data=f'conlist,n,{page},{status}')
        if _payments_r:
            right_button = types.InlineKeyboardButton(
                text='➡️', callback_data=f'conlist,r,{page + 1},{status}')
        else:
            right_button = types.InlineKeyboardButton(
                text='❌', callback_data=f'conlist,n,{page},{status}')

        markup.row(left_button, right_button)

    markup.add(types.InlineKeyboardButton(text='Вернуться', callback_data=f"conlist,back"))
    return markup


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('conlist,payment'))
async def handler_payment_callback(callback_query: types.CallbackQuery):
    logger.info(f'handle conlist payment from {callback_query.from_user.id} data {callback_query.data}')
    await callback_query.answer()
    data = callback_query.data.split(',')
    page = data[3]
    status = data[4]
    payment_id = ObjectId(data[2])
    db = SingletonClient.get_data_base()
    payment = await db.Payments.find_one({
        '_id': payment_id
    })
    user = await db.Users.find_one({
        '_id': payment['payer']
    })

    string = f'Оплата обязательного взноса от {user.get("second_name")} {user.get("first_name")} {user.get("third_name")} ({user.get("mention")})\n'
    string += f"Сумма: {payment.get('amount')}\n"
    string += f"Способ оплаты: {payment.get('type')}\n"
    string += f"Дата платежа: {payment.get('payment_date')}"
    markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(text='✅ Подтвердить платеж',
                                          callback_data=f'conlist-confirm,{payment.get("_id")},{page},{status}')
    button_2 = types.InlineKeyboardMarkup(text='🔥 Забанить пользователя',
                                          callback_data=f'conlist-ban,{payment.get("_id")},{page},{status}')
    button_3 = types.InlineKeyboardButton(text='❌ Отклонить платеж',
                                          callback_data=f'conlist-decline,{payment.get("_id")},{page},{status}')

    if payment['status'] == 'declined':
        markup.add(button_1)
    else:
        markup.add(button_3)
    markup.add(button_2)
    markup.add(types.InlineKeyboardButton(text='Вернуться', callback_data=f"conlist-back,{payment.get('_id')},{page},{status}"))

    await callback_query.message.answer(string, reply_markup=markup)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('conlist-'))
async def handle_conlist_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    if not callback_query.data.startswith('conlist-back'):
        await handle_payment_callback_func(callback_query)

    string = 'Выберите платеж для работы с ним'
    markup = await handle_conlist_callback_query_string_markup_generator(callback_query)
    await callback_query.message.answer(string, reply_markup=markup)
    await callback_query.message.delete()


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