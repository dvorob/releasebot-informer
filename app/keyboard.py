#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Build different menus
"""
from aiogram import types
from app.utils import logging, filters, aero

logger = logging.setup()
posts_cb = filters.callback_filter()

def admin_menu() -> types.InlineKeyboardMarkup:
    """
        Build admin menu keyboard
        :return: admin keyboard
    """
    # issue = '1' - hack for correct work posts_cb filter
    button_admin_list = [
        types.InlineKeyboardButton('Restart Informer', callback_data=posts_cb.new(action='restart',
                                                                             issue='1')),
        types.InlineKeyboardButton('Turn on bot', callback_data=posts_cb.new(action='turn_on',
                                                                             issue='1')),
        types.InlineKeyboardButton('Turn off bot', callback_data=posts_cb.new(action='turn_off',
                                                                              issue='1')),
        types.InlineKeyboardButton('Don\'t touch new release',
                                   callback_data=posts_cb.new(action='dont_touch',
                                                              issue='1')),
    ]
    to_main = types.InlineKeyboardButton('Main menu', callback_data=posts_cb.new(action='main',
                                                                                 issue='1'))
    return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_admin_list,
                                                                 n_cols=2, footer_buttons=to_main))


def main_menu() -> types.InlineKeyboardMarkup:
    """
        Main menu Keyboard
        :return: main menu
    """
    try:
        url_jira_board = 'https://jira.yamoney.ru/secure/RapidBoard.jspa?rapidView=715'
        url_kibana = 'https://kibana.yamoney.ru/goto/2319c2bcfb9ae9fda8e9669ef73830b4'
        url_wiki = 'https://wiki.yamoney.ru/x/03AAD'
        button_list = [
            types.InlineKeyboardButton(text="Show duty admin",
                                       callback_data=posts_cb.new(action='duty_button', issue='1')),
            types.InlineKeyboardButton("Open release board",
                                       url=url_jira_board),
            types.InlineKeyboardButton("Open documentation", url=url_wiki),
            types.InlineKeyboardButton("Open logs page",
                                       url=url_kibana),
            types.InlineKeyboardButton(text="Open admin menu",
                                       callback_data=posts_cb.new(action='admin_menu',
                                                                  issue='1')),
            types.InlineKeyboardButton("Return task to the queue",
                                       callback_data=posts_cb.new(action='return_queue',
                                                                  issue='1')),
            types.InlineKeyboardButton("Subscribe to events",
                                       callback_data=posts_cb.new(action='subscribe', issue='1')),
            types.InlineKeyboardButton("Get minimum information from release board",
                                       callback_data=posts_cb.new(action='get_min_inf_board',
                                                                  issue='1')),
        ]
        footer = types.InlineKeyboardButton("Get extended information from release board",
                                            callback_data=posts_cb.new(action='get_ext_inf_board',
                                                                       issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_list, n_cols=2,
                                                                     footer_buttons=footer))
    except Exception:
        logger.exception('main_menu_keyboard')


def subscribe_menu() -> types.InlineKeyboardMarkup:
    """
        Build menu with subscribe/unsubscribe options
        :return:
    """
    button_list = [
        types.InlineKeyboardButton("Subscribe to all events",
                                   callback_data=posts_cb.new(action='subscribe_all',
                                                              issue='1')),
        types.InlineKeyboardButton("Unsubscribe",
                                   callback_data=posts_cb.new(action='unsubscribe_all',
                                                              issue='1'))
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_list, n_cols=2))


def return_queue_menu(waiting_assignee_issues) -> types.InlineKeyboardMarkup:
    """
        Build menu with Jira task which can be returned to the queue
        :return:
    """
    button_list = []
    for issue in waiting_assignee_issues:
        # issue.key = ADMSYS-12345 issue.fields.summary = donator+1.1.1
        logger.debug('debug info jira %s %s', issue.key, issue.fields.summary)
        text_button = f'{issue.key}\n({issue.fields.summary})'
        button_list.append(types.InlineKeyboardButton(text=text_button,
                                                      callback_data=posts_cb.new(
                                                          issue=str(issue.key),
                                                          action="return_release")
                                                      )
                           )
    return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_list, n_cols=2))


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None) -> list:
    """
        Helper function for build menu
        :param buttons: button
        :param n_cols: number of colons
        :param header_buttons:
        :param footer_buttons:
        :return: menu button
    """
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    logger.debug('build_menu: %s', menu)
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def current_mode() -> str:
    """
        Get current mode of Bot
        :return: str with mode
    """
    spiky_mode = Spike.read(item='deploy', aerospike_set='remaster')

    if spiky_mode['run'] == 2:
        mode = 'Working'
    elif spiky_mode['run'] == 0:
        mode = 'Stopped'
    else:
        mode = 'Don\'t touching new releases'

    return mode
