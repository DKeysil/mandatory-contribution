from aiogram import types
from bson import ObjectId
from bson.errors import InvalidId
from loguru import logger

from app.bot.handlers.contributions_list import payment_string_markup
from app.motor_client import SingletonClient


async def get_contribution_cmd(message: types.Message):
    logger.info(f'get contribution from {message.from_user.id}')
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer(
            'Вы не зарегистрированы в системе. Напишите /start'
        )

    if not user.get('treasurer'):
        return await message.answer('Вы не казначей.')

    if not message.get_args():
        return await message.answer('Не указан айди платежа')

    try:
        payment_id = ObjectId(message.get_args().split(' ')[0])
    except InvalidId:
        return await message.answer('Указан неверный айди')

    payment = await db.Payments.find_one({'_id': payment_id})

    if user['region'] != payment['region']:
        return await message.answer('У вас нет доступа к этому региону')

    if not payment:
        return await message.answer('Платеж не найден')

    string, markup = await payment_string_markup(payment,
                                                 status=payment['status'])
    markup.add(types.InlineKeyboardButton(
        text='Список платежей',
        callback_data=(f"conlist-back,{payment.get('_id')},"
                       f"0,{payment['status']}")
    ))
    file_id = payment['file_id']

    await message.answer_photo(file_id, string, reply_markup=markup)
