from datetime import datetime
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loguru import logger

from bot.modules.check_contributions.CheckContributions import (
    update_payment_in_db
)
from core.motor_client import SingletonClient


class Send(StatesGroup):
    choose_person = State()
    set_name = State()
    set_mention = State()
    set_federal_region = State()
    payment_platform = State()
    date = State()
    image = State()
    finish = State()


async def send_cmd(message: types.Message):
    logger.info(f"send from {message.from_user.id}")
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer(
            'Вы не зарегистрированы в системе. Напишите /start'
        )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Отправить взнос от себя",
                                          callback_data="send,self"))
    markup.add(types.InlineKeyboardButton(
        "Отправить взнос за другого человека", callback_data="send,another"
    ))
    await message.answer("Выберите, какой взнос вы собираетесь отправить:",
                         reply_markup=markup)
    await Send.choose_person.set()


async def set_person_cq(callback_query: types.CallbackQuery,
                        state: FSMContext):
    await callback_query.message.edit_reply_markup()
    logger.info(f"from {callback_query.from_user.id}")
    db = SingletonClient.get_data_base()
    user = await db.Users.find_one(
        {'telegram_id': callback_query.from_user.id}
    )
    if callback_query.data.endswith("self"):
        markup = await payment_types_markup(user['region'])
        if not markup:
            await callback_query.message.answer(
                'Казначей еще не настроил реквизиты для оплаты'
            )
            return await state.finish()
        await callback_query.message.answer('Выберите платформу для оплаты',
                                            reply_markup=markup)
        await Send.payment_platform.set()
        await state.update_data(person="self")

    elif callback_query.data.endswith("another"):
        await callback_query.message.answer(("Пришлите <b>Фамилию Имя</b> "
                                             "человека, для которого "
                                             "учитывается взнос"))
        await Send.set_name.set()
        await state.update_data(person="another")

    await state.update_data(user_id=user['_id'])
    await state.update_data(region_id=user['region'])
    await callback_query.answer()


async def set_name_msg(message: types.Message, state: FSMContext):
    name = message.text.split(' ')
    logger.info(f"Установка имени {name} from {message.from_user.id}")
    if len(name) != 2:
        return await message.answer('Введите <b>Фамилию Имя</b>')

    await state.update_data(second_name=name[0])
    await state.update_data(first_name=name[1])

    await Send.set_mention.set()
    await message.answer(
        ('Введите телеграм тег пользователя в формате: <b>@тег</b>\n'
         'Если его нет, то нажмите кнопку "Отсутствует"'),
        reply_markup=types.ReplyKeyboardMarkup(
            [[types.KeyboardButton("Отсутствует")]]
        )
    )


async def set_mention_msg(message: types.Message, state: FSMContext):
    logger.info(f"set mention from {message.from_user.id}")
    await message.answer("Данные сохранены.",
                         reply_markup=types.ReplyKeyboardRemove())
    mention = message.text
    await state.update_data(mention=mention)

    db = SingletonClient.get_data_base()
    user = await db.Users.find_one({'telegram_id': message.from_user.id})

    if user.get('federal_region'):
        await Send.set_federal_region.set()
        return await message.answer("Пришлите название федерального региона")

    markup = await payment_types_markup(user['region'])
    if not markup:
        await message.answer('Казначей еще не настроил реквизиты для оплаты')
        return await state.finish()
    await message.answer('Выберите платформу для оплаты', reply_markup=markup)
    await Send.payment_platform.set()


async def set_federal_region_msg(message: types.Message, state: FSMContext):
    logger.info(f"from {message.from_user.id}")
    await state.update_data(federal_region=message.text)
    await message.reply("Принято")

    db = SingletonClient.get_data_base()
    user = await db.Users.find_one({'telegram_id': message.from_user.id})

    markup = await payment_types_markup(user['region'])
    if not markup:
        await message.answer('Казначей еще не настроил реквизиты для оплаты')
        return await state.finish()
    await message.answer('Выберите платформу для оплаты', reply_markup=markup)
    await Send.payment_platform.set()


async def payment_types_markup(
        region_id
) -> Union[bool, types.InlineKeyboardMarkup]:
    logger.info(f"markup for {region_id}")
    db = SingletonClient.get_data_base()
    region = await db.Regions.find_one({'_id': region_id})
    payment_types = region['payment_types']

    markup = types.InlineKeyboardMarkup()
    logger.error(payment_types)
    if not payment_types:
        return False
    for payment_type in payment_types:
        markup.add(types.InlineKeyboardButton(
            text=payment_type[0],
            callback_data=f"rq,{payment_type[0]},{payment_type[1]}")
        )

    return markup


async def set_payment_type_cq(callback_query: types.CallbackQuery,
                              state: FSMContext):
    logger.info(f"from {callback_query.from_user.id}")
    await callback_query.message.answer(
        f'Реквизиты: <code>{callback_query.data.split(",")[2]}</code>'
    )
    payment_type = callback_query.data.split(',')[1]
    await state.update_data(payment_type=payment_type)

    await callback_query.message.answer(
        'Укажите дату и время платежа в формате <code>dd.mm.yyyy HH:MM</code>'
    )
    await Send.date.set()
    await callback_query.answer()


async def set_payment_date_msg(message: types.Message, state: FSMContext):
    date = message.text
    logger.info(f"date {date} from {message.from_user.id}")
    try:
        date = datetime.strptime(date, '%d.%m.%Y %H:%M')
        await state.update_data(date=date)
    except ValueError:
        return await message.answer(
            'Дата и время указаны в неправильном формате.\n\n'
            'Укажите дату и время платежа в формате <code>dd.mm.yyyy HH:MM'
            '</code>\n\n'
            'Без нее ваш платеж может быть потерян и не учтен, '
            'указывайте время отправки платежа правильно.'
        )

    await Send.image.set()
    await message.answer('Пришлите скриншот перевода')


async def image_document_msg(message: types.Message, _: FSMContext):
    await message.reply(
        "Необходимо прислать сжатое фото. "
        "При отправлении фото нажмите галочку \"Сжать фото\" (Compress images)"
    )


async def image_photo_msg(message: types.Message, state: FSMContext):
    file_id = message.photo[0].file_id  # file id фотографии
    await state.update_data(file_id=file_id)
    db = SingletonClient.get_data_base()
    async with state.proxy() as data:
        if data.get("person") == "self":
            user = await db.Users.find_one({'_id': data.get('user_id')})
            string = f'ФИ: {user["second_name"]} {user["first_name"]}\n'
        else:
            user = {
                "first_name": data.get("first_name"),
                "second_name": data.get("second_name"),
                "mention": data.get("mention")
            }
            string = f'ФИ: {user["second_name"]} {user["first_name"]}\n'
            string += f'Тег: {user["mention"]}\n'

        amount = 200  # todo: добавить взнос частями
        string += f'Размер взноса: {amount}\n'
        string += f'Платформа оплаты: {data.get("payment_type")}\n'
        date = data.get('date').strftime("%d.%m.%Y %H:%M")
        string += f"Дата платежа: {date}"

    await message.answer_photo(
        file_id,
        caption=f'Проверьте отправленные данные:\n\n{string}',
        reply_markup=under_event_keyboard()
    )

    await Send.finish.set()


def under_event_keyboard():
    markup = types.InlineKeyboardMarkup()

    button = types.InlineKeyboardButton(text="✅ Подтвердить",
                                        callback_data='Accept')
    markup.add(button)

    button = types.InlineKeyboardButton(text="❌ Отменить",
                                        callback_data='Cancel')
    markup.add(button)
    return markup


async def accept_cq(callback_query: types.CallbackQuery, state: FSMContext):
    logger.info(f"from {callback_query.from_user.id}")
    db = SingletonClient.get_data_base()

    async with state.proxy() as data:
        if await db.Payments.find_one({'file_id': data.get('file_id'),
                                       'region': data.get('region_id'),
                                       'payment_date': data.get('date')}):
            await callback_query.message.edit_reply_markup()
            await callback_query.message.answer(
                'Вы отправили информацию о взносе.'
            )
            await state.finish()
            return await callback_query.answer('Ваш платеж уже учтен')
        if data.get("person") == "self":
            logger.info("self")
            user = await db.Users.find_one({'_id': data.get('user_id')})
            user_id = user.get("_id")
        else:
            logger.info("another")
            dct = {
                "first_name": data.get("first_name"),
                "second_name": data.get("second_name"),
                "mention": data.get("mention"),
                "payer": data.get('user_id'),
                'region': data.get('region_id'),
                'registration_date': datetime.now().timestamp()
            }
            if region := data.get("federal_region"):
                dct.update({
                    "federal_region": region
                })

            result = await db.Users.insert_one(dct)
            user_id = result.inserted_id
            user = await db.Users.find_one({
                '_id': user_id
            })

        result = await db.Payments.insert_one({
            'payer': user_id,
            # todo: добавить взнос частями
            'amount': 200,  # Стандартно 600
            'region': data.get('region_id'),
            'date': int(datetime.timestamp(datetime.now())),
            'file_id': data.get('file_id'),
            'type': data.get('payment_type'),
            'status': 'waiting',
            'payment_date': data.get('date')
        })

        await update_payment_in_db(user, result.inserted_id, 'waiting')
        logger.info(f'Send contribution by: {callback_query.from_user.id}\n'
                    f'insert_one user in db status: {result.acknowledged}')

    await callback_query.message.edit_reply_markup()
    await callback_query.message.answer('Вы отправили информацию о взносе.')
    await state.finish()
    await callback_query.answer()


async def cancel_cq(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    logger.info(f'Start by: {callback_query.from_user.id}\ncancel')
    await callback_query.message.answer('Отправка взноса была отменена')
    await callback_query.answer()
