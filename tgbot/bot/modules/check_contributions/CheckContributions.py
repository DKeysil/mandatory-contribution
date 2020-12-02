from bot import dp, types, FSMContext, bot
from motor_client import SingletonClient
from loguru import logger
from bson import ObjectId
from bot import spreadsheet
import pygsheets


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['check'])
async def check(message: types.Message, state: FSMContext):
    logger.info('check new payments')
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer('Вы не зарегистрированы в системе. Напишите /start')

    if not user.get('treasurer'):
        return await message.answer('Вы не казначей.')

    payment = db.Payments.find({
        'region': user.get('region'),
        'status': 'waiting'
    }).sort('title', 1)
    payment = await payment.to_list(length=1)

    logger.info(payment)

    if not payment:
        return await message.answer('Новых платежей не поступало')

    payment = payment[0]
    file_id, string, markup = await generate_contribution_string_photo_markup(payment.get('_id'))
    await message.answer_photo(file_id, string, reply_markup=markup)


async def generate_contribution_string_photo_markup(payment_id: ObjectId):
    db = SingletonClient.get_data_base()
    payment = await db.Payments.find_one({
        '_id': payment_id
    })
    user = await db.Users.find_one({
        '_id': payment.get('payer')
    })
    logger.info(user)

    string = f'Оплата обязательного взноса от {user.get("second_name")} {user.get("first_name")} {user.get("third_name")} ({user.get("mention")})\n'
    string += f"Сумма: {payment.get('amount')}\n"
    string += f"Способ оплаты: {payment.get('type')}\n"
    string += f"Дата платежа: {payment.get('payment_date')}"
    markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton(text='✅ Подтвердить платеж',
                                          callback_data=f'payment-confirm,{payment.get("_id")}')
    button_2 = types.InlineKeyboardMarkup(text='🔥 Забанить пользователя',
                                          callback_data=f'payment-ban,{payment.get("_id")}')
    button_3 = types.InlineKeyboardButton(text='❌ Отклонить платеж',
                                          callback_data=f'payment-decline,{payment.get("_id")}')
    markup.row(button_1)
    markup.row(button_2, button_3)
    return payment.get('file_id'), string, markup


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('payment-'))
async def handle_payment_callback(callback_query: types.CallbackQuery):
    db = SingletonClient.get_data_base()
    payment_id = ObjectId(callback_query.data.split(',')[1])
    payment = await db.Payments.find_one({
        '_id': payment_id
    })
    user_id = payment.get('payer')
    user = await db.Users.find_one({
        '_id': user_id
    })

    if callback_query.data.startswith('payment-confirm'):
        await callback_query.answer('Взнос был подтвержден')
        result = await db.Payments.update_one({'_id': payment_id}, {
            "$set": {
                'status': 'accepted'
            }
        })
        await update_payment_in_db(user, payment_id)

        await bot.send_message(user.get('telegram_id'), text='👏🏻 Ваш платеж был подтвержден')
    elif callback_query.data.startswith('payment-ban'):
        await callback_query.answer('Пользователь был забанен в боте')
        result = await db.Users.update_one({'_id': user_id}, {
            '$set': {
                'ban': True
            }
        })

        result = await db.Payments.update_one({'_id': payment_id}, {
            "$set": {
                'status': 'declined'
            }
        })

        await bot.send_message(user.get('telegram_id'), text='🤦🏻‍♂️ Вы были заблокированы')
    else:
        await callback_query.answer('Взнос был отклонен')
        result = await db.Payments.update_one({'_id': payment_id}, {
            "$set": {
                'status': 'declined'
            }
        })

        await bot.send_message(user.get('telegram_id'), text='⁉️ Ваш платеж был отменен')

    user = await db.Users.find_one({'telegram_id': callback_query.from_user.id})
    payment = await db.Payments.find_one({
        'region': user.get('region'),
        'status': 'waiting'
    })

    if not payment:
        await callback_query.message.edit_caption(caption=callback_query.message.caption)
        return await callback_query.message.answer('Новых платежей не поступало')

    file_id, string, markup = await generate_contribution_string_photo_markup(payment.get('_id'))

    media = types.InputMediaPhoto(media=file_id, caption=string)
    await callback_query.message.edit_media(media, reply_markup=markup)


async def update_payment_in_db(user, payment_id: ObjectId):
    # todo: добавить цвета и авторастягивание столбцов
    db = SingletonClient.get_data_base()
    logger.info(f"from user {user} payment id {payment_id}")
    region = await db.Regions.find_one({
        '_id': user['region']
    })
    payment = await db.Payments.find_one({
        '_id': payment_id
    })
    logger.info(f"payment: {payment} region: {region}")
    try:
        wks = spreadsheet.worksheet_by_title(region['title'])
    except pygsheets.exceptions.WorksheetNotFound:
        wks = spreadsheet.add_worksheet(region['title'])
        wks.insert_rows(row=0, values=['id', 'ФИО', 'Телеграм', 'id платежа',
                                       'Дата платежа', 'Сумма платежа', 'Платежная система'])

    cell = wks.find(str(user['_id']))
    if not cell:
        fio = f"{user['second_name']} {user['first_name']} {user['third_name']}"
        wks.append_table([
            str(user['_id']),
            fio,
            user.get('mention'),
            str(payment['_id']),
            str(payment['payment_date']),
            payment['amount'],
            payment['type']
        ], dimension='ROWS')
    else:
        cell = cell[0]
        wks.update_values(crange=(cell.row, cell.col + 3),
                          values=[[str(payment['_id'])],
                                  [str(payment['payment_date'])],
                                  [payment['amount']],
                                  [payment['type']]],
                          majordim='COLUMNS')
