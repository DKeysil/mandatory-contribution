from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType

from app.bot.filters import ConlistNavFilter
from app.bot.handlers import (check_contributions as check_contribs,
                              contributions_list as contribs_list,
                              requisites,
                              send_contribution as send_contrib,
                              start)
from app.bot.handlers.cancel import cancel_cmd
from app.bot.handlers.get_contribution import get_contribution_cmd
from app.bot.states import AddRequisites, Registration, Send


def setup_callback_handlers(dp: Dispatcher) -> None:
    """
    Регистрация хендлеров callback'ов бота.

    Хендлеры с состояниями должны быть выше других.
    :param dp:
    :return:
    """
    # хенделеры с состояниями
    dp.register_callback_query_handler(send_contrib.set_person_cb,
                                       Text(startswith='send'),
                                       state=Send.choose_person)
    dp.register_callback_query_handler(send_contrib.set_payment_type_cb,
                                       Text(startswith='rq'),
                                       state=Send.payment_platform)
    dp.register_callback_query_handler(
        send_contrib.accept_cb, text='Accept', state=Send.finish
    )
    dp.register_callback_query_handler(
        send_contrib.cancel_cb, text='Cancel', state=Send.finish
    )

    dp.register_callback_query_handler(start.handle_region_cb,
                                       state=Registration.region)
    dp.register_callback_query_handler(
        start.accept_cb, text='Accept', state=Registration.finish
    )
    dp.register_callback_query_handler(
        start.restart_cb, text='Restart', state=Registration.finish
    )

    # хендлеры без состояний
    dp.register_callback_query_handler(check_contribs.handle_payment_cb,
                                       Text(startswith='payment-'))

    dp.register_callback_query_handler(
        contribs_list.show_list_cb, Text(startswith='conlist', endswith='show')
    )
    dp.register_callback_query_handler(contribs_list.handle_conlist_cb_back,
                                       Text(startswith='conlist,back'))
    dp.register_callback_query_handler(contribs_list.handle_conlist_cb_nav,
                                       ConlistNavFilter())
    dp.register_callback_query_handler(contribs_list.handler_payment_cb,
                                       Text(startswith='conlist,payment'))
    dp.register_callback_query_handler(contribs_list.handler_banned_cb,
                                       Text(startswith='conlist,banned'))
    dp.register_callback_query_handler(contribs_list.handle_conlist_unban_cb,
                                       Text(startswith='conlist-unban'))
    dp.register_callback_query_handler(contribs_list.handle_conlist_cb,
                                       Text(startswith='conlist-'))

    dp.register_callback_query_handler(requisites.handle_requisites_edit_cb,
                                       Text(startswith='requisites,edit'))
    dp.register_callback_query_handler(requisites.handle_requisites_delete_cb,
                                       Text(startswith='requisites,delete'))
    dp.register_callback_query_handler(requisites.handle_requisites_add_cb,
                                       Text(startswith='requisites,add'))
    dp.register_callback_query_handler(requisites.handle_requisites_add_cb,
                                       Text(startswith='requisites,change'))


def setup_cmd_handlers(dp: Dispatcher) -> None:
    """
    Регистрация хендлеров комманд бота.

    Хенделеры с состояними должны быть выше других.
    :param dp:
    :return:
    """
    # хендлеры с состояниями
    dp.register_message_handler(cancel_cmd,  commands='cancel', state='*')
    dp.register_message_handler(start.start_cmd, commands='start', state='*')

    # хендлеры без состояний
    dp.register_message_handler(check_contribs.check_cmd, commands='check')

    dp.register_message_handler(contribs_list.contributions_list_cmd,
                                commands='list')

    dp.register_message_handler(get_contribution_cmd, commands='get')

    dp.register_message_handler(requisites.requisites_cmd, commands='req')

    dp.register_message_handler(send_contrib.send_cmd, commands='send')


def setup_msg_handlers(dp: Dispatcher) -> None:
    """
    Регистрация хендлеров простых сообщений боту с состояниями.
    :param dp:
    :return:
    """
    dp.register_message_handler(requisites.set_title_msg,
                                state=AddRequisites.title)
    dp.register_message_handler(requisites.set_numbers_msg,
                                state=AddRequisites.numbers)

    dp.register_message_handler(send_contrib.set_name_msg, state=Send.set_name)
    dp.register_message_handler(send_contrib.set_mention_msg,
                                state=Send.set_mention)
    dp.register_message_handler(send_contrib.set_federal_region_msg,
                                state=Send.set_federal_region)
    dp.register_message_handler(send_contrib.set_payment_date_msg,
                                state=Send.date)
    dp.register_message_handler(send_contrib.image_document_msg,
                                content_types=ContentType.DOCUMENT,
                                state=Send.image)
    dp.register_message_handler(send_contrib.image_photo_msg,
                                content_types=ContentType.PHOTO,
                                state=Send.image)

    dp.register_message_handler(start.set_name_msg, state=Registration.name)
    dp.register_message_handler(start.refresh_regions_list_cmd,
                                commands='refresh',
                                state=Registration.region)
    dp.register_message_handler(start.set_federal_region_msg,
                                state=Registration.federal_region)


def setup_handlers(dp: Dispatcher) -> None:
    """
    Установка всех хендлеров
    :param dp:
    :return:
    """
    setup_callback_handlers(dp)
    setup_cmd_handlers(dp)
    setup_msg_handlers(dp)
