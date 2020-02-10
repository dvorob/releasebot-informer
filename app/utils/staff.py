#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Staff helper
"""
import requests
from app.utils import logging
import app.config as config

logger = logging.setup()


def find_data_by_tg_username(tg_username):
    """
        Search data in staff.yandex-team.ru by telegram
        :param tg_username: tg_username
        :return: list of found data, json of found data
    """
    list_found = []
    logger.info('find_data_by_tg_username started for @%s', tg_username)
    try:
        url = f'{config.staff_url}/tg'
        ssl_ca = 'ssl/ca.pem'
        r = requests.post(
            url,
            verify=ssl_ca,
            json={'tg': tg_username})
        api_resp = r.json()

        if len(api_resp) == 0:
            list_found.append('Ничего на стафе не найдено...')
        else:
            list_found.append('Найдены:')
            for person in api_resp:
                output = f"Name: {person['first']} {person['last']}\n" \
                         f"Position: {person['position']}\n" \
                         f"Internal number: {person['internal']}\n"

                for department in person['departments']:
                    output += f'Department: {department}\n'

                for phone in person['phones']:
                    output += f'Phone: {phone}\n'

                for email in person['emails']:
                    if email[-10:] == 'yamoney.ru':
                        output += f'Email: {email}\n'

                for telegram in person['telegrams']:
                    output += f'Telegram: @{telegram}'

                list_found.append(output)
    except Exception:
        logger.exception('def staff_id')
        list_found.append('Error occurred, please show this message to sysops')
    return list_found, api_resp
