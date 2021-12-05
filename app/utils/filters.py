#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Defence filters
"""
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from utils import logging, returnHelper
from utils.database import PostgresPool as db
import aiohttp
import asyncio
import config as config
import warnings
import sys
import requests

logger = logging.setup()

async def get_session():
    session = aiohttp.ClientSession()
    return session

def callback_filter() -> CallbackData:
    """
        Create callback filter
        :return: callback data filter first argument - prefix (don't know for what this one),
        other strings as *args **kwargs - filter fields
    """
    return CallbackData("prefix", "issue", "action")


def duty_callback() -> CallbackData:
    """
        Create callback filter
    """
    return CallbackData("prefix", "ddate", "area", "action")


async def admin(message: types.message) -> bool:
    """
        Filter for admin functions
    """
    try:
        user_info = await db().search_users_by_account(str(message.from_user.username))
        if len(user_info) > 0:
            if user_info[0]['admin'] == 1 and user_info[0]['working_status'] != 'dismissed':
                return True
            elif user_info[0]['working_status'] == 'dismissed':
                await message.answer(text='Извините, но вы уволились. Вернётесь обратно и сможете насладиться нашим сервисом.')
                logger.warning('Attempt to enter the admin menu from dismissed %s',
                               returnHelper.return_name(message))
                return False
            else:
                await message.answer(text='Извините, вы не в списке админов.')
                logger.warning('Attempt to enter the admin menu from %s',
                               returnHelper.return_name(message))
                return False
        else:
            return False
    except Exception as e:
        logger.exception('-- Error in admin filter', str(e))


async def restricted(message: types.message) -> bool:
    """
        Проверка, что пользователь есть в БД бота (== он заведён в AD и активен). Если нет - это не наш юзер, отвечать ему не нужно.
    """
    try:
        user_info = await db().search_users_by_account(str(message.from_user.username))
        logger.info('restriction check for : %s ,\n from %s ,\n found in users table %s', message.from_user.username, sys._getframe().f_back.f_code.co_name, user_info)
        warning_message = f'Unauthorized access denied: {returnHelper.return_name(message)}'

            # Две проверки: 1 - что у нас в принципе есть ответ, если нет, напишем пользователю, что мы его не наши. 
            #               2 - что у найденного пользователя есть account_name в AD
        if len(user_info) > 0:
            logger.info('restricted allow for %s', user_info[0]['account_name'])
            if str(message.from_user.id) != user_info[0]['tg_id']:
                await db().set_users(user_info[0]['account_name'], full_name=None, tg_login=None, working_status=None, tg_id=str(message.from_user.id), notification=None, email=None)
            if user_info[0]['working_status'] != 'dismissed':
                return True
            else:
                await message.answer(text='Извините, но вы уволились. Не пишите мне больше, у нас теперь разная жизнь.')
                return False
        else:
            logger.info('restricted user not found %s %s ', message.from_user.username, warning_message)
            await message.answer(text='Ваш telegram-логин не найден в базе пользователей компании. Обратитесь к администраторам.')
            return False
    except Exception:
        logger.exception('exception in restricted')