# -*- coding: utf-8 -*-
"""
Build different menus
"""
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from datetime import date, datetime, timedelta
import re
from utils.jiratools import JiraConnection
from utils import logging, filters
from utils.database import PostgresPool as db
import config

logger = logging.setup()
posts_cb = filters.callback_filter()
duty_cb = filters.duty_callback()

button_main_menu = types.KeyboardButton('Главное меню', callback_data=posts_cb.new(action='main', issue='1'))
reply_main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).add(button_main_menu)

def main_menu(tg_login: str = '') -> types.InlineKeyboardMarkup:
    """
        Main menu Keyboard
        :return: main menu
    """
    try:
        url_jira_board = f'{config.jira_host}/secure/RapidBoard.jspa?rapidView=715'
        url_wiki = 'https://wiki.yooteam.ru/display/admins/ReleaseBot.Informer'
        user_rights = db().get_user_rights('tg_login', tg_login)
        button_list = [
            types.InlineKeyboardButton(text="Дежурные",
                                       callback_data=posts_cb.new(action='duty_button', issue='1')),
            types.InlineKeyboardButton("Релизная доска", url=url_jira_board),
            types.InlineKeyboardButton("Документация", url=url_wiki),
            types.InlineKeyboardButton("Вернуть релиз в очередь",
                                       callback_data=posts_cb.new(action='return_queue', issue='1')),
            types.InlineKeyboardButton("Подписки и уведомления",
                                       callback_data=posts_cb.new(action='subscribe', issue='1')),
            types.InlineKeyboardButton("Краткая инфа с релизной доски",
                                       callback_data=posts_cb.new(action='get_min_inf_board', issue='1'))
        ]
        if user_rights['is_ops'] == 1:
            button_list.append(types.InlineKeyboardButton('Взять дежурство', 
<<<<<<< HEAD
                                    callback_data=duty_cb.new(action='take_duty_date_list', ddate='1', area='1', dutyman='1')))
=======
                                        callback_data=duty_cb.new(action='take_duty_date_list', ddate='1', area='1', dutyman='1')))
>>>>>>> 6691142a102c36e9fdb2052b639ff37766d0b0ad
            button_list.append(types.InlineKeyboardButton('Мои дежурства', 
                                    callback_data=posts_cb.new(action='myduty_button', issue='1')))
        if user_rights['is_admin'] == 1:
            button_list.append(types.InlineKeyboardButton("Админское меню",
                               callback_data=posts_cb.new(action='admin_menu', issue='1')))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_list, n_cols=2))
    except Exception:
        logger.exception('main_menu_keyboard')


def subscribe_menu() -> types.InlineKeyboardMarkup:
    """
        Build menu with subscribe/unsubscribe options
    """
    button_list = [
        types.InlineKeyboardButton("События по релизам",
                                   callback_data=posts_cb.new(action='release_events', issue='1')),
        types.InlineKeyboardButton("Расписание встреч",
                                   callback_data=posts_cb.new(action='timetable_reminder', issue='1')),
        types.InlineKeyboardButton("Статистика по релизам",
                                   callback_data=posts_cb.new(action='statistics_reminder', issue='1')),
        types.InlineKeyboardButton("Уведомления о дежурствах",
                                   callback_data=posts_cb.new(action='duties_reminder', issue='1'))   
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
        types.InlineKeyboardButton('Рестарт Информера', callback_data=posts_cb.new(action='restart',
                                                                             issue='1')),
        types.InlineKeyboardButton('Включить релизы', callback_data=posts_cb.new(action='turn_on',
                                                                             issue='1')),
        types.InlineKeyboardButton('Остановить релизы', callback_data=posts_cb.new(action='turn_off',
                                                                              issue='1')),
        types.InlineKeyboardButton('Не брать новые релизы',
                                   callback_data=posts_cb.new(action='dont_touch', issue='1')),
        types.InlineKeyboardButton('Выкатить релиз', callback_data=posts_cb.new(action='release_app_list', issue='1')),
        types.InlineKeyboardButton('Откатить релиз', callback_data=posts_cb.new(action='rollback_app_list', issue='1')),
        types.InlineKeyboardButton('Перезапустить релизы', callback_data=posts_cb.new(action='retry_inprogress_releases_confirm', issue='1'))
    ]
    to_main = types.InlineKeyboardButton('Главное меню', callback_data=posts_cb.new(action='main', issue='1'))
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
        to_admin = types.InlineKeyboardButton('Админское меню', callback_data=posts_cb.new(action='admin_menu', issue='1'))
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
        to_admin = types.InlineKeyboardButton('Админское меню', callback_data=posts_cb.new(action='admin_menu', issue='1'))
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


def retry_inprogress_releases() -> types.InlineKeyboardMarkup:
    """
    """
    try:
        logger.info(f'-- RETRY INPROGRESS RELEASES CONFIRM build menu for issue')
        button_retry_inprogress_releases = [types.InlineKeyboardButton('Да, Перезапускай', callback_data=posts_cb.new(action='retry_inprogress_releases', issue='1'))]
        button_back = types.InlineKeyboardButton('Назад', callback_data=posts_cb.new(action='admin_menu', issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_retry_inprogress_releases, n_cols=1, footer_buttons=button_back))
    except Exception as e:
        logger.exception(f'Error in RETRY INPROGRESS RELEASES CONFIRM {str(e)}')


def take_duty_date_list() -> types.InlineKeyboardMarkup:
    """
    """
    try:
        dates_list = _get_list_of_dates(date.today(), 7)
        button_release_list = []
        logger.info(f'-- KEYBOARD TAKE DUTY DATE LIST build menu for {dates_list}')
        for dd in dates_list:
            dd_str = dd.strftime('%Y-%m-%d')
            dd_of_week = config.DaysOfWeek[dd.strftime('%A')].value
            button_release_list.append(types.InlineKeyboardButton(f"{dd_str} {dd_of_week}",
                                       callback_data=duty_cb.new(action='take_duty_area_list', ddate=dd_str, area='1', dutyman='1')))
        to_admin = types.InlineKeyboardButton('Главное меню', callback_data=posts_cb.new(action='main', issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_release_list, n_cols=1, footer_buttons=to_admin))
    except Exception as e:
        logger.exception(f'Error in TAKE DUTY DATE LIST {str(e)}')


def take_duty_area_list(ddate: str, dutyman: str) -> types.InlineKeyboardMarkup:
    """
    """
    try:
        user_from_db = db().get_users('tg_login', re.sub('@', '', dutyman))
        logger.info(f'--- TAKE DUTY AREA LIST {dutyman} {user_from_db}')
        area_list = get_duty_areas_for_team(user_from_db[0]['team_name'])
        button_release_list = []
        logger.info(f'-- KEYBOARD TAKE DUTY AREA LIST build menu for {area_list} {ddate}')
        for area in area_list:
            button_release_list.append(types.InlineKeyboardButton(f"{area}",
                                       callback_data=duty_cb.new(action='take_duty_confirm', ddate=ddate, area=area, dutyman='1')))
        to_admin = types.InlineKeyboardButton('Главное меню', callback_data=posts_cb.new(action='main', issue='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_release_list, n_cols=1, footer_buttons=to_admin))
    except Exception as e:
        logger.exception(f'Error in TAKE DUTY AREA LIST {str(e)}')


def take_duty_confirm(ddate, area) -> types.InlineKeyboardMarkup:
    """
    """
    try:
        logger.info(f'-- KEYBOARD TAKE DUTY CONFIRM build menu for issue {ddate} {area}')
        button_confirm = [types.InlineKeyboardButton('Да', callback_data=duty_cb.new(action='take_duty', ddate=ddate, area=area, dutyman='1'))]
        take_duty_date_list_button = types.InlineKeyboardButton('Изменить выбор', callback_data=duty_cb.new(action='take_duty_date_list', ddate='1', area='1', dutyman='1'))
        return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_confirm, n_cols=1, footer_buttons=take_duty_date_list_button))
    except Exception as e:
        logger.exception(f'Error in TAKE DUTY CONFIRM {str(e)}')


# def dev_team_members(dev_team) -> types.InlineKeyboardMarkup:
#     """
#     """
#     # try:
#     #     logger.info('-- KEYBOARD DEV TEAM MEMBERS ASK %s', dev_team)
#     #     ask_members_button = types.InlineKeyboardButton('Состав команды', callback_data=posts_cb.new(action='rollback_app_list', issue='1'))
#     #     return types.InlineKeyboardMarkup(inline_keyboard=build_menu(button_confirm, n_cols=1, footer_buttons=rollback_app_list))
#     # except Exception as e:
#     #     logger.exception('Error in KEYBOARD ROLLBACK APP CONFIRM %s', e)
#     # msg = get_dev_team_members(dev_team_name)
#     # await query.message.reply(text=msg, parse_mode=ParseMode.HTML)
#     try:
#         logger.info('-- KEYBOARD DEV TEM MEMBERS build menu for issue %s', issue)
#         kb = [types.InlineKeyboardButton('Состав команды', callback_data=posts_cb.new(action='dev_team_members', issue=dev_team))]
#         return types.InlineKeyboardMarkup(inline_keyboard=build_menu(kb, n_cols=1, footer_buttons=rollback_app_list))
#     except Exception as e:
#         logger.exception('Error in KEYBOARD DEV TEAM MEMBERS %s', e)

def get_duty_areas_for_team(team_name: str) -> set:
    """
    По названию команды выбрать все логины из Users. Затем по этим логинам собрать все зоны дежурств из duty_list.
    Нужно, чтобы понять, в каких зонах дежурят в конкретной команде
    """
    try:
        duty_areas = set()
        tg_login_set = set()
        users_from_db = db().get_users('team_name', team_name)
        for user in users_from_db:
            tg_login_set.add(user['tg_login'])
        # возьмем все дежурства за последние пару недель для данного сета пользователей
        ddate = datetime.today() - timedelta(14)
        duties = db().get_duties_for_users_set(duty_date=ddate, tg_login_set=tg_login_set)
        for duty in duties:
            duty_areas.add(duty['area'])
        return duty_areas
    except Exception as e:
        logger.exception(f'Error in get duty areas for team {str(e)}')


def _get_list_of_dates(start_date: datetime.date, delta: int) -> list:
    date_modified=start_date
    date_list=[start_date]
    while date_modified<start_date + timedelta(days=delta):
        date_modified+=timedelta(days=1) 
        date_list.append(date_modified)
    return date_list


def current_mode() -> str:
    """
        Get current mode of Bot
        :return: str with mode
    """
    run_mode = db().get_parameters('run_mode')[0]['value']

    if run_mode == 'on':
        mode = ':green_circle:  Качу релизы'
    elif run_mode == 'off':
        mode = ':red_circle:  Остановлен'
    else:
        mode = ':yellow_circle:  Выкачу то, что уже на мне, и пойду в МСМ'
    return mode
