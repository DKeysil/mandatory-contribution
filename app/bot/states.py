from aiogram.dispatcher.filters.state import State, StatesGroup


class AddRequisites(StatesGroup):
    title = State()
    numbers = State()


class Send(StatesGroup):
    choose_person = State()
    set_name = State()
    set_mention = State()
    set_federal_region = State()
    payment_platform = State()
    date = State()
    image = State()
    finish = State()


class Registration(StatesGroup):
    name = State()
    region = State()
    federal_region = State()
    finish = State()
