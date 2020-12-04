from bot import dp, types, FSMContext, bot
from motor_client import SingletonClient
from loguru import logger
from bson import ObjectId
from bot import agcm
import os
import re
import gspread
from datetime import datetime


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
    await handle_payment_callback_func(callback_query)
    db = SingletonClient.get_data_base()
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


async def handle_payment_callback_func(callback_query: types.CallbackQuery):
    db = SingletonClient.get_data_base()
    payment_id = ObjectId(callback_query.data.split(',')[1])
    payment = await db.Payments.find_one({
        '_id': payment_id
    })
    user_id = payment.get('payer')
    user = await db.Users.find_one({
        '_id': user_id
    })
    _type = callback_query.data.split('-')[1]

    if _type.startswith('confirm'):
        await callback_query.answer('Взнос был подтвержден')
        result = await db.Payments.update_one({'_id': payment_id}, {
            "$set": {
                'status': 'accepted'
            }
        })
        await update_payment_in_db(user, payment_id, status='accept')

        await bot.send_message(user.get('telegram_id'), text='👏🏻 Ваш платеж был подтвержден')
    elif _type.startswith('ban'):
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
        await update_payment_in_db(user, payment_id, status='decline')

        await bot.send_message(user.get('telegram_id'), text='🤦🏻‍♂️ Вы были заблокированы')
    else:
        await callback_query.answer('Взнос был отклонен')
        result = await db.Payments.update_one({'_id': payment_id}, {
            "$set": {
                'status': 'declined'
            }
        })
        await update_payment_in_db(user, payment_id, status='decline')

        await bot.send_message(user.get('telegram_id'), text='⁉️ Ваш платеж был отменен')


async def update_payment_in_db(user, payment_id: ObjectId, status):
    # todo: добавить цвета и авторастягивание столбцов
    # todo: закрашивать красным платежи, которые были подтверждены, но потом были отклонены
    db = SingletonClient.get_data_base()
    agc = await agcm.authorize()
    sph = await agc.open_by_key(key=os.environ['GOOGLE_SPREADSHEET_KEY'])
    logger.info(f"from user {user} payment id {payment_id}")
    region = await db.Regions.find_one({
        '_id': user['region']
    })
    logger.info(region)
    payment = await db.Payments.find_one({
        '_id': payment_id
    })
    logger.info(f"payment: {payment} region: {region}")
    logger.info(sph._ws_cache_idx)
    if not region.get('worksheet_id') and (region.get('worksheet_id') != 0):
        wks = await sph.add_worksheet(region['title'], rows=0, cols=0)
        logger.info(sph._ws_cache_idx)
        await wks.append_row(values=['id', 'ФИО', 'Телеграм', 'id платежа',
                                     'Дата платежа', 'Сумма платежа', 'Платежная система', 'Статус'])
        await db.Regions.update_one({
            '_id': region['_id']
        }, {"$set": {
            "worksheet_id": list(sph._ws_cache_idx.keys())[-1]
        }})
        region = await db.Regions.find_one({
            '_id': user['region']
        })
    else:
        wks = await sph.get_worksheet(region['worksheet_id'])
    try:
        cell = await wks.find(str(user['_id']))
    except gspread.exceptions.CellNotFound:
        cell = None
    logger.info(cell)
    if not cell:
        if status == 'accept':
            fio = f"{user['second_name']} {user['first_name']} {user['third_name']}"
            await wks.append_row([
                str(user['_id']),
                fio,
                user.get('mention'),
                str(payment['_id']),
                str(payment['payment_date']),
                payment['amount'],
                payment['type'],
                'Одобрен'
            ], nowait=True)
    else:
        end_cell = gspread.Cell(row=cell.row, col=cell.col + 6)
        cells = await wks.range(f"{cell.address}:{end_cell.address}")
        cells[3].value = str(payment['_id'])
        cells[4].value = str(payment['payment_date'])
        cells[5].value = payment['amount']
        cells[6].value = payment['type']
        logger.info(cells)
        if status == 'decline':
            accepted_payment = await db.Payments.find_one({
                'payer': payment['payer'],
                'status': 'accepted'
            })
            if not accepted_payment:
                cells.append(gspread.Cell(row=cell.row, col=cell.col + 7, value='Отклонен'))
                await wks.update_cells(cells, nowait=True)
        else:
            cells.append(gspread.Cell(row=cell.row, col=cell.col + 7, value='Одобрен'))
            await wks.update_cells(cells, nowait=True)
