#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Initialization of bot
"""
from aiogram import Bot, Dispatcher
import app.config as config


def initialization() -> tuple:
    """
        Initialization of bot
        :return: tuple dispatcher, bot
    """
    token = config.bot_token
    bot = Bot(token=token)
    return Dispatcher(bot), bot
