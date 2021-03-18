from typing import Any, Dict, List

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Row
from aiogram_dialog.widgets.text import Const, Format, Jinja
from bson import ObjectId

from core.regions import get_region_by_id, get_regions_list
from core.users import create_user


class Registration(StatesGroup):
    name = State()
    region = State()
    federal_region = State()
    finish = State()


async def wrap_regions_to_buttons() -> List[Button]:
    regions = await get_regions_list()
    result = []
    for region in regions:
        result.append(Button(
            Const(region['title']), str(region['_id']), get_region
        ))
    return result


class RegionButtonGroup(Group):
    async def _render_keyboard(
            self, data: Dict, manager: DialogManager
    ) -> List[List[types.InlineKeyboardButton]]:
        self.buttons = await wrap_regions_to_buttons()
        return await super()._render_keyboard(data, manager)


async def get_data(dialog_manager: DialogManager, **_) -> Dict[str, Any]:
    keys = ('first_name', 'second_name', 'region_id', 'region_title')
    result = {}
    for key in keys:
        result.update({key: dialog_manager.context.data(key)})
    federal_region = dialog_manager.context.data('federal_region', None)
    if federal_region:
        result.update({'federal_region': federal_region})
    result['region_id'] = ObjectId(result['region_id'])
    return result


async def input_name(
        msg: types.Message, dialog: Dialog, manager: DialogManager
) -> None:
    name = msg.text.split(' ')
    if len(name) != 2:
        await dialog.switch_to(Registration.name, manager)
        return
    manager.context.set_data('first_name', name[0])
    manager.context.set_data('second_name', name[1])
    await wrap_regions_to_buttons()
    await dialog.next(manager)


async def refresh_regions(msg: types.Message, *_) -> None:
    if not msg.text == '/refresh':
        return
    await wrap_regions_to_buttons()


async def get_region(
        cq: types.CallbackQuery, _, manager: DialogManager
) -> None:
    region_id = ObjectId(cq.data)
    manager.context.set_data('region_id', region_id)
    region = await get_region_by_id(region_id)
    manager.context.set_data('region_title', region['title'])
    if region['title'] == 'Федеральный регион':
        await manager.dialog().next(manager)
        return
    await manager.dialog().switch_to(Registration.finish, manager)


async def input_federal_region(
        msg: types.Message, dialog: Dialog, manager: DialogManager
) -> None:
    manager.context.set_data('federal_region', msg.text)
    await dialog.next(manager)


async def accept_finish(
        cq: types.CallbackQuery, _, manager: DialogManager
) -> None:
    data = await get_data(manager)
    data.update({'region': data.pop('region_id')})
    data.pop('region_title')
    await create_user(tg_id=cq.from_user.id, mention=cq.from_user.mention,
                      **data)

    await cq.message.edit_text(
        'Регистрация пройдена.\n'
        'Отправьте /help, чтобы узнать о возможностях бота.'
    )
    await manager.done()


async def restart_finish(
        cq: types.CallbackQuery, _, manager: DialogManager
) -> None:
    await cq.answer('Попробуем ещё раз.')
    await manager.start(Registration.name, reset_stack=True)


reg_dialog = Dialog(
    Window(
        Const('Для использования бота необходимо зарегистрироваться.'),
        Const('Отправьте <code>Имя Фамилию</code> в именительном падеже.'),
        MessageInput(input_name),
        state=Registration.name,
    ),
    Window(
        Const('Выберите регион.'),
        Const('Если вашего региона нет, попросите казначея его добавить и '
              'обновите список командой /refresh.'),
        MessageInput(refresh_regions),
        RegionButtonGroup('', keep_rows=False, width=3),
        state=Registration.region
    ),
    Window(
        Const('Пришлите название вашего региона.'),
        MessageInput(input_federal_region),
        state=Registration.federal_region
    ),
    Window(
        Const('Проверьте введённые данные:\n'),
        Format('ФИ: {first_name} {second_name}'),
        Format('Регион: {region_title}'),
        Jinja('{% if federal_region %}Уточнённый регион: {{ federal_region }}'
              '{% endif %}'),
        Row(
            Button(Const(u'\u2705 Подтвердить'), 'accept', accept_finish),
            Button(Const(u'\u274C Начать сначала'), 'restart', restart_finish)
        ),
        state=Registration.finish,
        getter=get_data
    )
)
