#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Initialization of bot
"""
from aiogram import Bot, Dispatcher
import config as config

PROXY_URL="http://proxy.yamoney.ru:3128/"
bot = Bot(token=config.bot_token, proxy=PROXY_URL, disable_web_page_preview=True)
dp = Dispatcher(bot)