#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Defence filters
"""
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from app.utils import logging
from app.utils import ioAerospike as Spike
from app.utils import returnHelper
import app.config as config


logger = logging.setup()


def callback_filter() -> CallbackData:
    """
        Create callback filter
        :return: callback data filter first argument - prefix (don't know for what this one),
        other strings as *args **kwargs - filter fields
    """
    return CallbackData("prefix", "issue", "action")


async def admin(message: types.message) -> bool:
    """
        Filter for admin functions
        :param message:
        :return: True or false
    """
    try:
        if message.from_user.id not in config.bot_master.values():
            await message.answer(text='You are not admin')
            logger.warning('Attempt to enter the admin menu from %s',
                           returnHelper.return_name(message))
            return False
        return True
    except Exception:
        logger.exception('admin filter')


async def restricted(message: types.message) -> bool:
    """
        Universal access restriction function
        :param message: main function
        :return: Error msg to telegram or main function
    """
    try:
        tg_username = message.from_user.username
        logger.info('tg_username: %s', tg_username)
        all_employee_json = Spike.read(item='access_denied',
                                       aerospike_set='access_denied')
        # Create list with possible usernames in aerospike
        list_of_tg_usernames = [tg_username, tg_username.lower()]
        logger.debug('list_of_tg_usernames: %s', list_of_tg_usernames)
        warning_message = f'Unauthorized access denied: {returnHelper.return_name(message)}'
        # Will know how username was saved in aerospike - upper or lower case?
        # If none of the two options - Unauthorized access denied,
        # else check to is_dismissed
        list_of_aerospike_answers = list()
        for various_tg_usernames in list_of_tg_usernames:
            list_of_aerospike_answers.append(all_employee_json['all_employee'].get(various_tg_usernames, None))
        logger.debug('list_of_answers: %s', list_of_aerospike_answers)

        # If employee exist, list_of_answers will be [None, dict_with_info]
        # or [dict_with_info, dict_with_info] else [None, None]
        # Заменить на вызов ручки проверки, наш ли это сотрудник, работает ли он
        if list_of_aerospike_answers[0] == list_of_aerospike_answers[1] is None:
            # logger.warning(warning_message)
            # msg = 'Извини, мне сказали, ты больше не с нами.'
            # await message.answer(text=msg)
            # return False
            return True
        else:
            # When one of the list elements is dict, we found true_tg_username
            for index, _ in enumerate(list_of_aerospike_answers):
                if isinstance(list_of_aerospike_answers[index], dict):
                    true_tg_username = list_of_aerospike_answers[index]
                    logger.debug('true_tg_username: %s', true_tg_username)

            if true_tg_username['is_dismissed'] is True:
                logger.warning(warning_message)
                msg = 'Извини, мне сказали, ты больше не с нами.'
                await message.answer(text=msg)
                # End decorator if it falls under the condition
                return False
            else:
                return True
    except Exception:
        logger.exception('restricted')