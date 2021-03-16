from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Filter


class ConlistNavFilter(Filter):
    def check(self, cb_query: types.CallbackQuery) -> bool:
        data = cb_query.data.split(',')
        return data[0] == 'conlist' and data[1] in ('r', 'l', 'n')


def setup_filters(dp: Dispatcher) -> None:
    dp.filters_factory.bind(ConlistNavFilter,
                            event_handlers=[dp.callback_query_handlers])
