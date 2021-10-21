#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Initialization of bot
"""
from aiogram import Bot, Dispatcher
from aiogram_aiohttp_session import AiohttpSession
import config as config

session = AiohttpSession(proxy="http://proxy.yamoney.ru:3128/")
bot = Bot(token=config.bot_token, session=session)
dp = Dispatcher(bot)