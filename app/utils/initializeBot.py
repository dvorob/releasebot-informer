#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Initialization of bot
"""
from aiogram import Bot, Dispatcher
import config as config

bot = Bot(token=config.bot_token)
dp = Dispatcher(bot)