from aiogram import types
from bson import ObjectId
from loguru import logger

from app.bot.handlers.check_contributions import handle_payment_callback_func
from app.motor_client import SingletonClient


async def contributions_list_cmd(message: types.Message):
    logger.info('check contributions_list')
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer(
            'Вы не зарегистрированы в системе. Напишите /start'
        )

    if not user.get('treasurer'):
        return await message.answer('Вы не казначей.')

    string = 'Выбери список каких платежей вы хотите получить'

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        text='✅ Список одобренных платежей',
        callback_data='conlist,accepted,show'
    ))
    markup.add(types.InlineKeyboardButton(
        text='🔥 Список отклоненных платежей',
        callback_data='conlist,declined,show'
    ))
    markup.add(types.InlineKeyboardButton(
        text='❌ Список забаненных пользователей',
        callback_data='conlist,banned,show'
    ))

    await message.answer(string, reply_markup=markup)


async def show_list_cb(callback_query: types.CallbackQuery):
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one(
        {'telegram_id': callback_query.from_user.id}
    )
    region = await db.Regions.find_one({'_id': user['region']})
    status = callback_query.data.split(',')[1]
    markup = types.InlineKeyboardMarkup()

    if status == 'banned':
        banned_users = await get_banned_list(region['_id'], 0)
        if not banned_users:
            return await callback_query.answer(
                'Забаненные пользователи не найдены'
            )
        for _user in banned_users:
            fio = f"{_user['second_name']} {_user['first_name'][:1]}."
            markup.add(types.InlineKeyboardButton(
                text=f"{_user['mention']} - {fio}",
                callback_data=f"conlist,banned,{_user['_id']},0,{status}")
            )
        if await get_banned_list(region['_id'], 1):
            button_1 = types.InlineKeyboardButton(
                text="❌", callback_data=f'conlist,n,0,{status}'
            )
            button_2 = types.InlineKeyboardButton(
                text="➡️", callback_data=f'conlist,r,1,{status}'
            )
            markup.row(button_1, button_2)
        string = 'Выберите пользователя для работы с ним'
    else:
        payments = await get_contributions_list(region['_id'], status, 0)
        if not payments:
            return await callback_query.answer('Платежи не найдены')

        for payment in payments:
            payer = await db.Users.find_one({'_id': payment['payer']})
            fio = f"{payer['second_name']} {payer['first_name'][:1]}."
            markup.add(types.InlineKeyboardButton(
                text=f"{fio} {payment['payment_date']}",
                callback_data=f"conlist,payment,{payment['_id']},0,{status}"
            ))

        if await get_contributions_list(region['_id'], status, 1):
            button_1 = types.InlineKeyboardButton(
                text="❌", сallback_data=f'conlist,n,0,{status}'
            )
            button_2 = types.InlineKeyboardButton(
                text="➡️", callback_data=f'conlist,r,1,{status}'
            )
            markup.row(button_1, button_2)
        string = 'Выберите платеж для работы с ним'

    markup.add(types.InlineKeyboardButton(text='Вернуться',
                                          callback_data="conlist,back"))
    await callback_query.message.edit_text(string, reply_markup=markup)


async def handle_conlist_cb_back(callback_query: types.CallbackQuery):
    string = 'Выбери список каких платежей вы хотите получить'

    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        text='✅ Список одобренных платежей',
        callback_data='conlist,accepted,show'
    ))
    markup.add(types.InlineKeyboardButton(
        text='🔥 Список отклоненных платежей',
        callback_data='conlist,declined,show'
    ))
    markup.add(
        types.InlineKeyboardButton(text='❌ Список забанненых пользователей',
                                   callback_data='conlist,banned,show'))
    # todo: добавить вывод забанненых пользователей

    await callback_query.message.edit_text(string, reply_markup=markup)


async def handle_conlist_cb_nav(callback_query: types.CallbackQuery):
    """
    Обработчик нажатия на кнопку под сообщением влево или вправо.
    Лямбда проверяет, чтобы обрабатывалось только y кнопки
    Args:
        callback_query (types.CallbackQuery): Документация на сайте телеграма
    """

    split_data = callback_query.data.split(',')
    if split_data[3] == 'banned':
        markup = await hande_conlist_banned_callback_query_markup_generator(
            callback_query
        )
    else:
        markup = await handle_conlist_callback_query_string_markup_generator(
            callback_query
        )
    await callback_query.message.edit_reply_markup(reply_markup=markup)
    await callback_query.answer()


async def hande_conlist_banned_callback_query_markup_generator(
        callback_query: types.CallbackQuery
):
    split_data = callback_query.data.split(',')
    if split_data[1] == 'n':
        return await callback_query.answer(text='Там больше ничего нет...')
    db = SingletonClient.get_data_base()
    user = await db.Users.find_one(
        {'telegram_id': callback_query.from_user.id}
    )
    page = int(split_data[2])
    status = split_data[3]
    region_id = user["region"]
    logger.info(f"banned list region_id {region_id} page {page}")
    banned_users = await get_banned_list(region_id, page)
    markup = types.InlineKeyboardMarkup()
    for _user in banned_users:
        fio = f"{_user['second_name']} {_user['first_name'][:1]}."
        markup.add(types.InlineKeyboardButton(
            text=f"{_user['mention']} - {fio}",
            callback_data=f"conlist,banned,{_user['_id']},0,{status}"
        ))
    users_l = await get_banned_list(region_id, page - 1)
    users_r = await get_banned_list(region_id, page + 1)
    if users_r or users_l:
        if users_l:
            left_button = types.InlineKeyboardButton(
                text='⬅️', callback_data=f'conlist,l,{page - 1},{status}')
        else:
            left_button = types.InlineKeyboardButton(
                text='❌', callback_data=f'conlist,n,{page},{status}')
        if users_r:
            right_button = types.InlineKeyboardButton(
                text="➡️", callback_data=f'conlist,r,{page + 1},{status}')
        else:
            right_button = types.InlineKeyboardButton(
                text='❌', callback_data=f'conlist,n,{page},{status}')
        markup.row(left_button, right_button)
    markup.add(types.InlineKeyboardButton(text='Вернуться',
                                          callback_data="conlist,back"))
    return markup


async def handle_conlist_callback_query_string_markup_generator(
        callback_query: types.CallbackQuery
):
    split_data = callback_query.data.split(',')
    if split_data[1] == 'n':
        return await callback_query.answer(text='Там больше ничего нет...')

    db = SingletonClient.get_data_base()
    page = int(split_data[2])
    status = split_data[3]
    logger.info(f"contibutions list page {page} status {status}")

    user = await db.Users.find_one(
        {'telegram_id': callback_query.from_user.id}
    )
    region = await db.Regions.find_one({'_id': user['region']})
    payments = await get_contributions_list(region['_id'], status, page)

    markup = types.InlineKeyboardMarkup()
    for payment in payments:
        payer = await db.Users.find_one({'_id': payment['payer']})
        fio = f"{payer['second_name']} {payer['first_name'][:1]}."
        markup.add(
            types.InlineKeyboardButton(
                text=f"{fio} {payment['payment_date']}",
                callback_data=(f"conlist,payment,"
                               f"{payment['_id']},{page},{status}")
            ))

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

    markup.add(types.InlineKeyboardButton(text='Вернуться',
                                          callback_data="conlist,back"))
    return markup


async def handler_payment_cb(callback_query: types.CallbackQuery):
    logger.info(f'handle conlist payment from {callback_query.from_user.id} '
                f'data {callback_query.data}')
    data = callback_query.data.split(',')
    page = data[3]
    status = data[4]
    payment_id = ObjectId(data[2])
    db = SingletonClient.get_data_base()
    payment = await db.Payments.find_one({
        '_id': payment_id
    })
    string, markup = await payment_string_markup(payment, status, page)
    file_id = payment['file_id']
    markup.add(types.InlineKeyboardButton(
        text='Вернуться',
        callback_data=f"conlist-back,{payment.get('_id')},{page},{status}"
    ))

    await callback_query.message.answer_photo(file_id, string,
                                              reply_markup=markup)
    await callback_query.message.delete()
    await callback_query.answer()


async def payment_string_markup(payment, status, page='0'):
    db = SingletonClient.get_data_base()
    user = await db.Users.find_one({
        '_id': payment['payer']
    })

    string = (f'Оплата обязательного взноса от {user.get("second_name")} '
              f'{user.get("first_name")} ({user.get("mention")})\n'
              f"Сумма: {payment.get('amount')}\n"
              f"Способ оплаты: {payment.get('type')}\n"
              f"Дата платежа: {payment.get('payment_date')}")
    markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(
        text='✅ Подтвердить платеж',
        callback_data=f'conlist-confirm,{payment.get("_id")},{page},{status}'
    )
    button_2 = types.InlineKeyboardMarkup(
        text='🔥 Забанить пользователя',
        callback_data=f'conlist-ban,{payment.get("_id")},{page},{status}'
    )
    button_3 = types.InlineKeyboardButton(
        text='❌ Отклонить платеж',
        callback_data=f'conlist-decline,{payment.get("_id")},{page},{status}'
    )

    if payment['status'] == 'declined':
        markup.add(button_1)
    else:
        markup.add(button_3)
    markup.add(button_2)
    return string, markup


async def handler_banned_cb(callback_query: types.CallbackQuery):
    logger.info(f'handle conlist banned from {callback_query.from_user.id} '
                f'data {callback_query.data}')
    data = callback_query.data.split(',')
    page = data[3]
    status = data[4]
    user_id = ObjectId(data[2])
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({
        '_id': user_id
    })

    string = f'Пользователь {user.get("second_name")} ' \
             f'{user.get("first_name")} ({user.get("mention")})\n'

    button_1 = types.InlineKeyboardButton(
        text='🥺 Разбанить пользователя',
        callback_data=f'conlist-unban,{user["_id"]},{page},{status}'
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(button_1)
    markup.add(types.InlineKeyboardButton(
        text='Вернуться',
        callback_data=f"conlist-back,{user['_id']},{page},{status}")
    )

    await callback_query.message.edit_text(text=string, reply_markup=markup)
    await callback_query.answer()


async def handle_conlist_unban_cb(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split(',')[1]
    logger.info(f"unban user {user_id}")
    db = SingletonClient.get_data_base()
    await db.Users.update_one({'_id': ObjectId(user_id)}, {
        "$set": {
            "ban": False
        }
    })
    string = 'Выберите пользователя для работы с ним'
    markup = await hande_conlist_banned_callback_query_markup_generator(
        callback_query
    )
    await callback_query.message.edit_text(text=string, reply_markup=markup)
    await callback_query.answer()


async def handle_conlist_cb(callback_query: types.CallbackQuery):
    if not callback_query.data.startswith('conlist-back'):
        await handle_payment_callback_func(callback_query)

    status = callback_query.data.split(',')[3]
    if status == 'banned':
        string = 'Выберите пользователя для работы с ним'
        markup = await hande_conlist_banned_callback_query_markup_generator(
            callback_query
        )
        await callback_query.message.edit_text(text=string,
                                               reply_markup=markup)
    else:
        string = 'Выберите платеж для работы с ним'
        markup = await handle_conlist_callback_query_string_markup_generator(
            callback_query
        )
        await callback_query.message.answer(string, reply_markup=markup)
        await callback_query.message.delete()
    await callback_query.answer()


async def get_contributions_list(region_id, status, page):
    db = SingletonClient.get_data_base()
    logger.info(f"get contrib list region_id {region_id} status {status} "
                f"page {page}")
    contributions_cursor = db.Payments.find({
        "region": ObjectId(region_id),
        'status': status
    })

    contrib_list = await contributions_cursor.to_list(
        length=await db.Payments.count_documents({})
    )

    try:
        return contrib_list[page * 5: page * 5 + 5]
    except IndexError:
        return []


async def get_banned_list(region_id, page):
    db = SingletonClient.get_data_base()
    logger.info(f"get banned list region_id {region_id} page {page}")
    banned_cursor = db.Users.find({
        "region": ObjectId(region_id),
        "ban": True
    })

    banned_list = await banned_cursor.to_list(
        length=await db.Users.count_documents({})
    )

    try:
        return banned_list[page * 2: page * 2 + 2]
    except IndexError:
        return []
