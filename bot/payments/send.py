from datetime import datetime
from typing import Any, Dict, List

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Row
from aiogram_dialog.widgets.text import Const, Format

from core.payments import create_payment
from core.regions import get_region_by_id
from core.users import get_user_by_tg_id, get_user_by_tg_username


class Send(StatesGroup):
    choose_payer = State()
    set_another_payer = State()
    payment_platform = State()
    amount = State()
    payment_date = State()
    screenshot = State()
    finish = State()


def wrap_payment_platforms_to_buttons(
        platforms: Dict[int, str]
) -> List[Button]:
    result = []
    for number, platform in platforms.items():
        result.append(Button(
            Const(platform), str(number), get_payment_platform
        ))
    return result


class PaymentPlatformButtonGroup(Group):
    async def _render_keyboard(
            self, data: dict, manager: DialogManager
    ) -> List[List[types.InlineKeyboardButton]]:
        self.buttons = wrap_payment_platforms_to_buttons(
            manager.context.data('payment_platforms', None)
        )
        return await super()._render_keyboard(data, manager)


async def set_region_payment_platforms(manager: DialogManager) -> None:
    payer = await get_user_by_tg_id(manager.context.data('payer', None))
    region = await get_region_by_id(payer['region'])
    platforms = region['payment_platforms']
    result = {}
    for number, platform in enumerate(platforms):
        result.update({number: platform[0]})
    manager.context.set_data('payment_platforms', result)


async def get_data(dialog_manager: DialogManager, **_) -> Dict[str, Any]:
    keys = ('payer', 'real_payer', 'payment_platform', 'amount',
            'payment_date', 'screen_id', 'screen_url')
    data = {k: dialog_manager.context.data(k, None) for k in keys}
    payer = await get_user_by_tg_id(data['payer'])
    real_payer = await get_user_by_tg_id(data['real_payer'])
    data.update({'payer': payer['_id'],
                 'first_name': payer['first_name'],
                 'last_name': payer['last_name'],
                 'real_payer': real_payer['_id'],
                 'payment_platform': data['payment_platform'][0]})
    return data


async def get_payer(
        cq: types.CallbackQuery, dialog: Dialog, manager: DialogManager
) -> None:
    manager.context.set_data('real_payer', cq.from_user.id)
    if cq.data == 'self':
        manager.context.set_data('payer', cq.from_user.id)
        await set_region_payment_platforms(manager)
        await dialog.switch_to(Send.payment_platform, manager)
        return
    await dialog.next(manager)


async def input_another_payer(
        msg: types.Message, dialog: Dialog, manager: DialogManager
) -> None:
    try:
        payer = int(msg.text)
        payer = await get_user_by_tg_id(payer)
    except ValueError:
        payer = msg.text.lstrip('@')
        payer = await get_user_by_tg_username(payer)

    if not payer:
        await msg.answer('Пользователь не найден. Возможно, он ещё не '
                         'зарегистрирован.\n\nОтменить платёж: /cancel')
        return

    manager.context.set_data('payer', payer['telegram_id'])
    await set_region_payment_platforms(manager)
    await dialog.next(manager)


async def get_payment_platform(
        cq: types.CallbackQuery, dialog: Dialog, manager: DialogManager
) -> None:
    platforms = manager.context.data('payment_platforms', None)
    platform = platforms.get(cq.data)
    manager.context.set_data('payment_platform', platform)
    await dialog.next(manager)


async def get_requisites(dialog_manager: DialogManager, **_) -> str:
    payment_platform = dialog_manager.context.data('payment_platform', None)
    return payment_platform[1]


async def get_amount(
        msg: types.Message, dialog: Dialog, manager: DialogManager
) -> None:
    try:
        amount = int(msg.text)
    except ValueError:
        await msg.answer('Вы должны ввести число, попробуйте ещё раз.')
        return
    manager.context.set_data('amount', amount)
    await dialog.next(manager)


async def get_payment_date(
        msg: types.Message, dialog: Dialog, manager: DialogManager
) -> None:
    incorrect_date = ('Вы прислали некорректные дату и время. Попробуйте ещё '
                      'раз.')
    if not msg.text:
        await msg.answer(incorrect_date)
        return
    try:
        datetime.strptime(msg.text, '%d.%m.%Y %H:%M')
    except ValueError:
        await msg.answer(incorrect_date)
        return

    manager.context.set_data('payment_date', msg.text)
    await dialog.next(manager)


async def get_screenshot(
        msg: types.Message, dialog: Dialog, manager: DialogManager
) -> None:
    if not msg.photo:
        await msg.answer('Вы должны прислать <b>сжатое</b> изображение. '
                         'Попробуйте ещё раз.')
        return
    manager.context.set_data('screen_id', msg.photo[-1].file_id)
    screen_url = await msg.photo[-1].get_url()
    manager.context.set_data('screen_url', screen_url)
    await dialog.next(manager)


async def accept_finish(
        cq: types.CallbackQuery, _, manager: DialogManager
) -> None:
    data = await get_data(manager)
    data.pop('first_name')
    data.pop('last_name')
    data.update({'payment_date': datetime.strptime(data['payment_date'],
                                                   '%d.%m.%Y %H:%M')})
    data.pop('screen_url')
    await create_payment(**data)
    await cq.message.edit_text('Информация о платеже отправлена.')
    await manager.done()


async def restart_finish(
        cq: types.CallbackQuery, _, manager: DialogManager
) -> None:
    await cq.answer('Попробуем ещё раз.')
    await manager.start(Send.choose_payer, reset_stack=True)


send_dialog = Dialog(
    Window(
        Const('Выберите, какой взнос вы собираетесь отправить.'),
        Row(
            Button(Const('За себя'), 'self', get_payer),
            Button(Const('За другого человека'), 'another', get_payer)
        ),
        state=Send.choose_payer
    ),
    Window(
        Const('Введите Telegram ID или username человека, для которого '
              'учитывается платёж.\n'),
        Const('<i>Telegram ID можно получить, отправив боту команду /id.</i>'),
        MessageInput(input_another_payer),
        state=Send.set_another_payer
    ),
    Window(
        Const('Выберите платёжную систему.'),
        PaymentPlatformButtonGroup(keep_rows=True, width=3),
        state=Send.payment_platform
    ),
    Window(
        Format('Реквизиты для оплаты: <code>{}</code>.\n'),
        Const('Теперь отправьте сумму перевода в рублях.'),
        MessageInput(get_amount),
        state=Send.amount,
        getter=get_requisites
    ),
    Window(
        Const('Пришлите дату и время перевода в формате '
              '<code>дд.мм.гггг ЧЧ:ММ</code>.'),
        Const('Пример: <code>01.01.2021 15:30</code>.'),
        MessageInput(get_payment_date),
        state=Send.payment_date
    ),
    Window(
        Const('Пришлите скриншот перевода.'),
        MessageInput(get_screenshot),
        state=Send.screenshot
    ),
    Window(
        Format('<a href="{screen_url}">&#8203;</a>'),
        Const('Проверьте отправленные данные:\n'),
        Format('ФИ: {first_name} {last_name}'),
        Format('Платформа оплаты: {payment_platform}'),
        Format('Размер платежа: {amount}'),
        Format('Время и дата: {payment_date}'),
        Row(
            Button(Const(u'\u2705 Подтвердить'), 'accept', accept_finish),
            Button(Const(u'\u274C Начать сначала'), 'restart', restart_finish)
        ),
        state=Send.finish
    )
)
