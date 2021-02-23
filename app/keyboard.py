# -*- coding: utf-8 -*-
"""
Build different menus
"""
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from utils.jiratools import JiraConnection
from utils import logging, filters
from utils.database import PostgresPool as db
import config

logger = logging.setup()
posts_cb = filters.callback_filter()

def main_menu() -> types.InlineKeyboardMarkup:
    """
        Main menu Keyboard
        :return: main menu
    """
    try:
        url_jira_board = 'https://jira.yamoney.ru/secure/RapidBoard.jspa?rapidView=715'
        url_kibana = 'https://kibana.yamoney.ru/goto/2319c2bcfb9ae9fda8e9669ef73830b4'
        url_wiki = 'https://wiki.yamoney.ru/display/admins/ReleaseBot.Informer'
        button_list = [
            types.InlineKeyboardButton(text="Дежурные",
                                       callback_data=posts_cb.new(action='duty_button', issue='1')),
            types.InlineKeyboardButton("Релизная доска",
                                       url=url_jira_board),
            types.InlineKeyboardButton("Документация", url=url_wiki),
            types.InlineKeyboardButton("Логи бота",
                                       url=url_kibana),
            types.InlineKeyboardButton(text="Админское меню",
                                       callback_data=posts_cb.new(action='admin_menu',
                                                                  issue='1')),
            types.InlineKeyboardButton("Вернуть релиз в очередь",
                                       callback_data=posts_cb.new(action='return_queue',
                                                                  issue='1')),
            types.InlineKeyboardButton("Подписки и уведомления",
                                       callback_data=posts_cb.new(action='subscribe', issue='1')),
            types.InlineKeyboardButton("Краткая инфа с релизной доски",
                                       callback_data=posts_cb.new(action='get_min_inf_board',
                                                                  issue='1')),
        ]
        footer = types.InlineKeyboardButton("Расширенная инфа с релизной доски",
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
        types.InlineKeyboardButton("События по релизам",
                                   callback_data=posts_cb.new(action='release_events',
                                                              issue='1')),
        types.InlineKeyboardButton("Расписание встреч",
                                   callback_data=posts_cb.new(action='timetable_reminder',
                                                              issue='1')),
        types.InlineKeyboardButton("Статистика по релизам",
                                   callback_data=posts_cb.new(action='statistics_reminder',
                                                              issue='1'))
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_list, n_cols=1))


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
    try:
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        logger.debug('-- BUILD MENU: %s', menu)
        if header_buttons:
            menu.insert(0, [header_buttons])
        if footer_buttons:
            menu.append([footer_buttons])
        return menu
    except Exception as e:
        logger.exception('Error in BUILD MENU %s', e)
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
                                   callback_data=posts_cb.new(action='dont_touch', issue='1')),
        types.InlineKeyboardButton('Release', callback_data=posts_cb.new(action='release_app_list', issue='1')),
        types.InlineKeyboardButton('Rollback', callback_data=posts_cb.new(action='rollback_app_list', issue='1'))
    ]
    to_main = types.InlineKeyboardButton('Main menu', callback_data=posts_cb.new(action='main',
                                                                                 issue='1'))
    return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_admin_list,
                                                                 n_cols=2, footer_buttons=to_main))

def release_app_list() -> types.InlineKeyboardMarkup:
    """
        Build admin menu keyboard
        :return: admin keyboard
    """
    try:
        issues = JiraConnection().jira_search(config.issues_waiting)
        button_release_list = []
        logger.info('-- KEYBOARD RELEASE APP LIST build menu for %s', issues)
        if len(issues) > 0:
            for issue in issues:
                button_release_list.append(types.InlineKeyboardButton(f'{issue.key} {issue.fields.summary}', 
                                           callback_data=posts_cb.new(action='release_app', issue=issue.key)))
        to_admin = types.InlineKeyboardButton('Admin menu', callback_data=posts_cb.new(action='admin_menu', issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_release_list, n_cols=1, footer_buttons=to_admin))
    except Exception as e:
        logger.exception('Error in KEYBOARD RELEASE APP LIST %s', e)

def release_app_confirm(issue) -> types.InlineKeyboardMarkup:
    """
    """
    try:
        logger.info('-- KEYBOARD RELEASE APP CONFIRM build menu for issue %s', issue)
        button_confirm = [types.InlineKeyboardButton('Точно', callback_data=posts_cb.new(action='release_app_confirm', issue=issue))]
        release_app_list = types.InlineKeyboardButton('К списку релизов', callback_data=posts_cb.new(action='release_app_list', issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_confirm, n_cols=1, footer_buttons=release_app_list))
    except Exception as e:
        logger.exception('Error in KEYBOARD RELEASE APP CONFIRM %s', e)

def rollback_app_list() -> types.InlineKeyboardMarkup:
    """
        Build admin menu keyboard
        :return: admin keyboard
    """
    try:
        issues = JiraConnection().jira_search(config.issues_confirm_full_resolved)
        button_release_list = []
        logger.info('-- KEYBOARD ROLLBACK APP LIST build menu for %s', issues)    
        if len(issues) > 0:
            for issue in issues:
                button_release_list.append(types.InlineKeyboardButton(f'{issue.key} {issue.fields.summary}',
                                           callback_data=posts_cb.new(action='rollback_app', issue=issue.key)))
        to_admin = types.InlineKeyboardButton('Admin menu', callback_data=posts_cb.new(action='admin_menu', issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_release_list, n_cols=1, footer_buttons=to_admin))
    except Exception as e:
        logger.exception('Error in KEYBOARD ROLLBACK APP LIST %s', e)

def rollback_app_confirm(issue) -> types.InlineKeyboardMarkup:
    """
    """
    try:
        logger.info('-- KEYBOARD ROLLBACK APP CONFIRM build menu for issue %s', issue)
        button_confirm = [types.InlineKeyboardButton('Точно', callback_data=posts_cb.new(action='rollback_app_confirm', issue=issue))]
        rollback_app_list = types.InlineKeyboardButton('К списку релизов', callback_data=posts_cb.new(action='rollback_app_list', issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_confirm, n_cols=1, footer_buttons=rollback_app_list))
    except Exception as e:
        logger.exception('Error in KEYBOARD ROLLBACK APP CONFIRM %s', e)

def current_mode() -> str:
    """
        Get current mode of Bot
        :return: str with mode
    """
    run_mode = db().get_parameters('run_mode')[0]['value']

    if run_mode == 'on':
        mode = 'Working'
    elif run_mode == 'off':
        mode = 'Stopped'
    else:
        mode = 'Don\'t touching new releases'

    return mode
