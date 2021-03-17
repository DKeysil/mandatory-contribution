"""Временный модуль для более корректной установки хендлеров."""
from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.filters import OrFilter
from aiogram.types import ContentType

from bot.modules import (check_contributions, contributions_list,
                         get_contribution, requisites, send_contribution,
                         start)
from bot.modules.cancel import cancel_cmd


def setup_cq_handlers(dp: Dispatcher) -> None:
    """
    Установка хендлеров callback'ов.

    Хендлеры с состояниями должны быть выше остальных.
    :param dp:
    :return:
    """
    # хендлеры с состояниями
    dp.register_callback_query_handler(
        send_contribution.set_person_cq,
        state=send_contribution.Send.choose_person,
        text_startswith='send'
    )
    dp.register_callback_query_handler(
        send_contribution.set_payment_type_cq,
        state=send_contribution.Send.payment_platform,
        text_startswith='rq'
    )
    dp.register_callback_query_handler(send_contribution.accept_cq,
                                       state=send_contribution.Send.finish,
                                       text='Accept')
    dp.register_callback_query_handler(send_contribution.cancel_cq,
                                       state=send_contribution.Send.finish,
                                       text='Cancel')

    dp.register_callback_query_handler(start.handle_region_cq,
                                       state=start.Registration.region)
    dp.register_callback_query_handler(start.accept_cq,
                                       state=start.Registration.finish,
                                       text='Accept')
    dp.register_callback_query_handler(start.restart_cq,
                                       state=start.Registration.finish,
                                       text='Restart')

    # хендлеры без состояний
    dp.register_callback_query_handler(check_contributions.handle_payment_cq,
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

    Хендлеры с состояниями должны быть выше остальных.
    :param dp:
    :return:
    """
    # хендлеры с состояниями
    dp.register_message_handler(cancel_cmd, commands='cancel', state='*',)

    dp.register_message_handler(start.refresh_regions_list_cmd,
                                commands='refresh',
                                state=start.Registration.region)

    # хенделеры без состояний
    dp.register_message_handler(check_contributions.check_cmd,
                                commands='check')

    dp.register_message_handler(contributions_list.contributions_list_cmd,
                                commands='list')

    dp.register_message_handler(get_contribution.get_contribution_cmd,
                                commands='get')

    dp.register_message_handler(requisites.requisites_cmd, commands='req')

    dp.register_message_handler(send_contribution.send_cmd, commands='send')

    dp.register_message_handler(start.start_cmd, commands='start')


def setup_msg_handlers(dp: Dispatcher) -> None:
    """
    Установка хендлеров обычных сообщений.

    Хендлеры с сотояниями должны быть выше остальных.
    :param dp:
    :return:
    """
    dp.register_message_handler(requisites.set_title_msg,
                                state=requisites.AddRequisites.title)
    dp.register_message_handler(requisites.set_numbers_msg,
                                state=requisites.AddRequisites.numbers)

    dp.register_message_handler(send_contribution.set_name_msg,
                                state=send_contribution.Send.set_name)
    dp.register_message_handler(send_contribution.set_mention_msg,
                                state=send_contribution.Send.set_mention)
    dp.register_message_handler(
        send_contribution.set_federal_region_msg,
        state=send_contribution.Send.set_federal_region
    )
    dp.register_message_handler(send_contribution.set_payment_date_msg,
                                state=send_contribution.Send.date)
    dp.register_message_handler(send_contribution.image_document_msg,
                                content_types=ContentType.DOCUMENT,
                                state=send_contribution.Send.image)
    dp.register_message_handler(send_contribution.image_photo_msg,
                                content_types=ContentType.PHOTO,
                                state=send_contribution.Send.image)

    dp.register_message_handler(start.set_name_msg,
                                state=start.Registration.name)
    dp.register_message_handler(start.set_federal_region_msg,
                                state=start.Registration.federal_region)


def setup_handlers(dp: Dispatcher) -> None:
    """
    Установка всех хендлеров.
    :param dp:
    :return:
    """
    setup_cq_handlers(dp)
    setup_cmd_handlers(dp)
    setup_msg_handlers(dp)
