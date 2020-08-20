#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Return helper
"""

def return_name(message) -> str:
    """
        Return the name, username of the person who started the conversation
        :param message
        :return: str fullname, username
    """
    return f'{message.from_user.full_name} @{message.from_user.username}'


def return_one_second(query):
    """
        Return :One second, please" to employee device
        :param query:
    """
    return query.answer('One second, please')


def return_early_duty_msg(time_now) -> str:
    """
        Create and return msg for early duty admin request
    """
    msg = f'<strong>Приветствую!</strong>\n' \
          f'Мне очень жаль, что тебе нужна информация в столь ранний час\n' \
          f'Сейчас <strong>{time_now}</strong> утра,\n' \
          f'Прямо сейчас дежурят эти люди, но всё изменится в <strong>10:00</strong>\n' \
          f'Посмотреть, кто сегодня дежурит после 10:00 можно командой ' \
          f'<strong>/duty 1</strong>.\n\n'
    return msg
