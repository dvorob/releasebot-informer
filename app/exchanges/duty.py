#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realize exchange methods
"""

from exchangelib import DELEGATE, Configuration, Credentials, \
    Account, EWSDateTime, EWSTimeZone
import app.config as config
from app.utils import logging

__all__ = ['ExchangeConnect']

logger = logging.setup()


class ExchangeConnect:
    """
        Connect to exchange server, has 2 methods
        - find_duty_exchange
        - timezone
    """
    def __init__(self):
        self.ex_cred = Credentials(config.ex_user, config.ex_pass)
        self.ex_cfg = Configuration(server=config.ex_host, credentials=self.ex_cred)
        self.ex_acc = Account(primary_smtp_address=config.ex_cal, config=self.ex_cfg,
                              access_type=DELEGATE, autodiscover=False)

    def find_duty_exchange(self, d_start, d_end) -> str:
        """
            Get duty information from Exchange AdminsOnDuty calendar.
            :param d_start:
            :param d_end:
            :return: msg with duty admin
        """
        logger.info('find_duty_exchange started')

        result = ''

        for msg in self.ex_acc.calendar.view(start=d_start, end=d_end) \
                .only('start', 'end', 'subject') \
                .order_by('start', 'end', 'subject'):
            body = msg.subject[:150]

            if result == '':
                result = '- %s' % body
            else:
                result += '\n- %s' % body

        logger.debug('Information about duty %s', result)
        return result

    @staticmethod
    def timezone() -> EWSDateTime:
        """
            Current time in Moscow timezone
            :return: EWSDateTime object with time
        """
        moscow_timezone = EWSTimeZone.timezone('Europe/Moscow')
        now_moscow = EWSDateTime.now(tz=moscow_timezone)
        return now_moscow
