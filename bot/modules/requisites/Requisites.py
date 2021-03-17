from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from core.motor_client import SingletonClient


async def requisites_cmd(message: types.Message):
    # todo: сделать реквизиты листабельными
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer(
            'Вы не зарегистрированы в системе. Напишите /start'
        )

    if not user.get('treasurer'):
        return await message.answer('Вы не казначей.')

    region = await db.Regions.find_one({
        '_id': user.get('region')
    })

    req = region.get('payment_types')

    markup = types.InlineKeyboardMarkup()
    if req:
        for i, requisite in enumerate(req):
            markup.add(types.InlineKeyboardButton(
                text=f"{requisite[0]}",
                callback_data=f'requisites,edit,{i}'
            ))

    markup.add(types.InlineKeyboardButton(text='Добавить реквизиты',
                                          callback_data='requisites,add'))
    if not req:
        return await message.answer(
            'Реквизиты не найдены, но вы можете их добавить',
            reply_markup=markup
        )

    await message.answer(
        ('Список реквизитов.'
         '\nВы можете изменить или удалить существующие или добавить новые.'),
        reply_markup=markup
    )


async def handle_requisites_edit_cq(callback_query: types.CallbackQuery,
                                    state: FSMContext):
    db = SingletonClient.get_data_base()
    user = await db.Users.find_one(
        {'telegram_id': callback_query.from_user.id}
    )
    region = await db.Regions.find_one({
        '_id': user.get('region')
    })

    req = region.get('payment_types')
    num = callback_query.data.split(',')[2]
    requisite = req[int(num)]
    string = f"<b>Название:</b> {requisite[0]}\n<b>Данные:</b> {requisite[1]}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        text='Изменить данные', callback_data=f'requisites,change,{num}')
    )
    markup.add(types.InlineKeyboardButton(
        text='Удалить реквизиты', callback_data=f'requisites,delete,{num}')
    )
    await callback_query.message.answer(string, reply_markup=markup)
    await state.update_data(mess=callback_query.message.message_id)
    await callback_query.answer()


async def handle_requisites_delete_cq(
        callback_query: types.CallbackQuery, state: FSMContext
):
    bot = callback_query.bot
    num = int(callback_query.data.split(',')[2])

    db = SingletonClient.get_data_base()
    user = await db.Users.find_one({
        'telegram_id': callback_query.from_user.id
    })
    region = await db.Regions.find_one({
        '_id': user.get('region')
    })
    payment_types_list: list = region.get('payment_types')
    payment_types_list.pop(num)

    await db.Regions.update_one({'_id': user.get('region')}, {
        "$set": {'payment_types': payment_types_list}
    })

    markup = types.InlineKeyboardMarkup()
    for i, requisite in enumerate(payment_types_list):
        markup.add(types.InlineKeyboardButton(
            text=f"{requisite[0]}", callback_data=f'requisites,edit,{i}')
        )
    markup.add(types.InlineKeyboardButton(text='Добавить реквизиты',
                                          callback_data='requisites,add'))
    data = await state.get_data()
    mess: types.Message.message_id = data['mess']
    await bot.delete_message(chat_id=callback_query.message.chat.id,
                             message_id=mess)
    await callback_query.message.edit_text(
        'Список реквизитов.\n'
        'Вы можете изменить или удалить существующие или добавить новые.'
    )
    await callback_query.message.edit_reply_markup(reply_markup=markup)
    await callback_query.answer()


class AddRequisites(StatesGroup):
    title = State()
    numbers = State()


async def handle_requisites_add_cq(callback_query: types.CallbackQuery,
                                   state: FSMContext):
    await callback_query.message.answer('Введите название банка/кошелька')
    await AddRequisites.title.set()
    await state.update_data(message=callback_query.message.message_id)
    await state.update_data(type=callback_query.data.split(',')[1])
    try:
        await state.update_data(num=callback_query.data.split(',')[2])
        await callback_query.answer()
    except IndexError:
        await callback_query.answer()


async def set_title_msg(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)

    await message.answer(
        'Введите номер карты или реквизиты кошелька (До 40 символов)'
    )

    await AddRequisites.numbers.set()


async def set_numbers_msg(message: types.Message, state: FSMContext):
    bot = message.bot
    async with state.proxy() as data:
        title = data['title']
        numbers = message.text
        mess: types.Message.message_id = data['message']
        mess_: types.Message.message_id = data.get('mess')
        type_ = data['type']
        num = data.get('num')
    st = len(('rq,' + title + message.text).encode('utf-8'))
    if st > 64:
        return await message.answer('Должно быть короче.')

    db = SingletonClient.get_data_base()
    user = await db.Users.find_one({
        'telegram_id': message.from_user.id
    })
    region = await db.Regions.find_one({
        '_id': user.get('region')
    })
    payment_types_list = region.get('payment_types')
    if not payment_types_list:
        payment_types_list = []

    if type_ == 'add':
        payment_types_list.append([title, numbers])
    elif type_ == 'change':
        num = int(num)
        payment_types_list[num] = [title, numbers]

    await db.Regions.update_one({'_id': user.get('region')}, {
        "$set": {'payment_types': payment_types_list}
    })

    await message.answer('Реквизиты были добавлены')
    markup = types.InlineKeyboardMarkup()
    for i, requisite in enumerate(payment_types_list):
        markup.add(types.InlineKeyboardButton(
            text=f"{requisite[0]}", callback_data=f'requisites,edit,{i}')
        )
    markup.add(types.InlineKeyboardButton(text='Добавить реквизиты',
                                          callback_data='requisites,add'))
    await bot.edit_message_text(
        text=('Список реквизитов.\nВы '
              'можете изменить или удалить существующие или добавить новые.'),
        message_id=mess,
        chat_id=message.chat.id
    )
    # await mess.edit_text(
    #     'Список реквизитов.\nВы можете изменить или удалить
    #     существующие или добавить новые.')
    await bot.edit_message_reply_markup(
        reply_markup=markup, message_id=mess, chat_id=message.chat.id
    )
    # await mess.edit_reply_markup(reply_markup=markup)
    if mess_:
        await bot.delete_message(message_id=mess_, chat_id=message.chat.id)
        # await mess_.delete()
    await state.finish()
