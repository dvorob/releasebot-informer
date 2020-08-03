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
import aiohttp
import asyncio
import app.config as config
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
        headers = {'username': str(message.from_user.username)}

        session = await get_session()
        async with session.get(config.api_get_user_info, headers=headers) as resp:
            req_user = await resp.json()

            logger.info('restricted check for : %s , response from api %s', tg_username, req_user)
            warning_message = f'Unauthorized access denied: {returnHelper.return_name(message)}'

            if req_user:
                if 'account_name' in req_user:
                    logger.info('restricted allow for %s', req_user['account_name'])
                    return False
                else:
                    logger.info('restricted user not found %s %s', tg_username, warning_message)
                    await message.answer(text='Извини, мне сказали, ты больше не с нами.')
                    # End decorator if it falls under the condition
                    return True
            else:
                logger.info('restricted no req_user')
    except Exception:
        logger.exception('exception in restricted')