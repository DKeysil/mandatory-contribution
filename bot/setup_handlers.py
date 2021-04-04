"""Временный модуль для более корректной установки хендлеров."""
from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.filters import OrFilter

from bot import handlers, payments, users
from bot.modules import (contributions, contributions_list,
                         get_contribution, requisites)


def setup_cq_handlers(dp: Dispatcher) -> None:
    """
    Установка хендлеров callback'ов.
    :param dp:
    :return:
    """
    dp.register_callback_query_handler(payments.handle_payment_cq,
                                       text_startswith='payment-')

    dp.register_callback_query_handler(contributions_list.show_list_cq,
                                       text_startswith='conlist',
                                       text_endswith='show')
    dp.register_callback_query_handler(contributions_list.handle_conlist_cq,
                                       text_startswith='conlist,back')
    dp.register_callback_query_handler(
        contributions_list.handle_conlist_cq_nav,
        contributions_list.ConlistNavFilter()
    )
    dp.register_callback_query_handler(contributions_list.handler_payment_cq,
                                       text_startswith='conlist,payment')
    dp.register_callback_query_handler(contributions_list.handler_banned_cq,
                                       text_startswith='conlist,banned')
    dp.register_callback_query_handler(
        contributions_list.handle_conlist_unban_cq,
        text_startswith='conlist-unban'
    )
    dp.register_callback_query_handler(
        contributions_list.handle_conlist_callback, text_startswith='conlist-'
    )

    dp.register_callback_query_handler(requisites.handle_requisites_edit_cq,
                                       text_startswith='requisites,edit')
    dp.register_callback_query_handler(requisites.handle_requisites_delete_cq,
                                       text_startswith='requisites,delete')
    dp.register_callback_query_handler(
        requisites.handle_requisites_add_cq,
        OrFilter(Text(startswith='requisites,add'),
                 Text(startswith='requisites,change'))
    )


def setup_cmd_handlers(dp: Dispatcher) -> None:
    """
    Установка хенделров комманд.
    :param dp:
    :return:
    """
    dp.register_message_handler(contributions.check_cmd,
                                commands='check')

    dp.register_message_handler(contributions_list.contributions_list_cmd,
                                commands='list')

    dp.register_message_handler(get_contribution.get_contribution_cmd,
                                commands='get')

    dp.register_message_handler(requisites.requisites_cmd, commands='req')


def setup_msg_handlers(dp: Dispatcher) -> None:
    """
    Установка хендлеров обычных сообщений.
    :param dp:
    :return:
    """
    dp.register_message_handler(requisites.set_title_msg,
                                state=requisites.AddRequisites.title)
    dp.register_message_handler(requisites.set_numbers_msg,
                                state=requisites.AddRequisites.numbers)


def setup_handlers(dp: Dispatcher) -> None:
    """
    Установка всех хендлеров.
    :param dp:
    :return:
    """
    handlers.setup_handlers(dp)
    users.setup_handlers(dp)
    payments.setup_handlers(dp)
    setup_cq_handlers(dp)
    setup_cmd_handlers(dp)
    setup_msg_handlers(dp)
