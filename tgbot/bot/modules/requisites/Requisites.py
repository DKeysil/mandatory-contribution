from bot import dp, types, FSMContext
from motor_client import SingletonClient
from loguru import logger
from aiogram.dispatcher.filters.state import State, StatesGroup


@dp.message_handler(lambda message: message.chat.type == 'private', commands=['req'])
async def requisites(message: types.Message, state: FSMContext):
    # todo: сделать реквизиты листабельными
    db = SingletonClient.get_data_base()

    user = await db.Users.find_one({'telegram_id': message.from_user.id})
    if not user:
        return await message.answer('Вы не зарегистрированы в системе. Напишите /start')

    if not user.get('treasurer'):
        return await message.answer('Вы не казначей.')

    region = await db.Regions.find_one({
        '_id': user.get('region')
    })

    req = region.get('payment_types')

    markup = types.InlineKeyboardMarkup()
    if req:
        for i, requisite in enumerate(req):
            markup.add(types.InlineKeyboardButton(text=f"{requisite[0]}", callback_data=f'requisites,edit,{i}'))

    markup.add(types.InlineKeyboardButton(text='Добавить реквизиты', callback_data='requisites,add'))
    if not req:
        return await message.answer('Реквизиты не найдены, но вы можете их добавить', reply_markup=markup)

    await message.answer('Список реквизитов.\nВы можете изменить или удалить существующие или добавить новые.',
                         reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('requisites,edit'))
async def handle_requisites_edit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    db = SingletonClient.get_data_base()
    user = await db.Users.find_one({'telegram_id': callback_query.from_user.id})
    region = await db.Regions.find_one({
        '_id': user.get('region')
    })

    req = region.get('payment_types')
    num = callback_query.data.split(',')[2]
    requisite = req[int(num)]
    string = f"<b>Название:</b> {requisite[0]}\n<b>Данные:</b> {requisite[1]}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Изменить данные', callback_data=f'requisites,change,{num}'))
    markup.add(types.InlineKeyboardButton(text='Удалить реквизиты', callback_data=f'requisites,delete,{num}'))
    await callback_query.message.answer(string, reply_markup=markup)
    await state.update_data(mess=callback_query.message)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('requisites,delete'))
async def handle_requisites_delete_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
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

    result = await db.Regions.update_one({'_id': user.get('region')}, {
        "$set": {'payment_types': payment_types_list}
    })

    markup = types.InlineKeyboardMarkup()
    for i, requisite in enumerate(payment_types_list):
        markup.add(types.InlineKeyboardButton(text=f"{requisite[0]}", callback_data=f'requisites,edit,{i}'))
    markup.add(types.InlineKeyboardButton(text='Добавить реквизиты', callback_data='requisites,add'))
    data = await state.get_data()
    mess: types.Message = data['mess']
    await mess.delete()
    await callback_query.message.edit_text('Список реквизитов.\nВы можете изменить или удалить существующие или добавить новые.')
    await callback_query.message.edit_reply_markup(reply_markup=markup)


class AddRequisites(StatesGroup):
    title = State()
    numbers = State()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('requisites,add') or
                           callback_query.data.startswith('requisites,change'))
async def handle_requisites_add_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer('Введите название банка/кошелька')
    await AddRequisites.title.set()
    await state.update_data(message=callback_query.message)
    await state.update_data(type=callback_query.data.split(',')[1])
    try:
        await state.update_data(num=callback_query.data.split(',')[2])
    except IndexError:
        pass


@dp.message_handler(state=[AddRequisites.title])
async def set_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)

    await message.answer('Введите номер карты или реквизиты кошелька (До 40 символов)')

    await AddRequisites.numbers.set()


@dp.message_handler(state=[AddRequisites.numbers])
async def set_numbers(message: types.Message, state: FSMContext):
    if len(message.text) > 40:
        return await message.answer('Должно быть короче.\nВведите номер карты или реквизиты кошелька (До 40 символов)')
    async with state.proxy() as data:
        title = data['title']
        numbers = message.text
        mess: types.Message = data['message']
        mess_: types.Message = data.get('mess')
        type_ = data['type']
        num = data.get('num')

    db = SingletonClient.get_data_base()
    user = await db.Users.find_one({
        'telegram_id': message.from_user.id
    })
    region = await db.Regions.find_one({
        '_id': user.get('region')
    })
    payment_types_list = region.get('payment_types') if region.get('payment_types') else []

    if type_ == 'add':
        payment_types_list.append([title, numbers])
    elif type_ == 'change':
        num = int(num)
        payment_types_list[num] = [title, numbers]

    result = await db.Regions.update_one({'_id': user.get('region')}, {
        "$set": {'payment_types': payment_types_list}
    })

    await message.answer('Реквизиты были добавлены')
    markup = types.InlineKeyboardMarkup()
    for i, requisite in enumerate(payment_types_list):
        markup.add(types.InlineKeyboardButton(text=f"{requisite[0]}", callback_data=f'requisites,edit,{i}'))
    markup.add(types.InlineKeyboardButton(text='Добавить реквизиты', callback_data='requisites,add'))
    await mess.edit_text(
        'Список реквизитов.\nВы можете изменить или удалить существующие или добавить новые.')
    await mess.edit_reply_markup(reply_markup=markup)
    if mess_:
        await mess_.delete()
    await state.finish()
