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
