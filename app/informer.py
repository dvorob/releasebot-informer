#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Telegram bot for employee of Yandex.Money
"""
from ast import excepthandler
import aiohttp
import config
import keyboard as keyboard
import asyncio
import json
import random
import re
import requests
import sys
import warnings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Dispatcher, executor, types
from aiogram.types import ParseMode, ChatActions, Update, ContentType
from aiogram.utils.emoji import emojize
from aiogram.utils.exceptions import ChatNotFound, BotBlocked
from aiogram.utils.markdown import bold
from aiogram.utils.markdown import quote_html
from aiohttp import web
from enum import Enum
from utils.jiratools import JiraConnection, JiraTransitions, jira_get_approvers_list, jira_get_watchers_list
from utils import logging, returnHelper, initializeBot, filters, couch_client
from utils.initializeBot import dp, bot
from utils.database import PostgresPool as db
import utils.messages as messages
from datetime import timedelta, datetime
from requests_ntlm import HttpNtlmAuth

loop = asyncio.get_event_loop()


@initializeBot.dp.errors_handler()
async def errors_handler(update: Update, exception: Exception):
    """
    """
    try:
        raise exception
    except Exception as e:
        logger.exception("Cause exception {e} in update {update}", e=e, update=update)
    return True


@initializeBot.dp.message_handler(filters.restricted, filters.admin, commands=['promo'])
async def marketing_send(message: types.Message):
    """Массовая рассылка спама, информинга. Для ручной отправки.
    """
    logger.info('Marketing send was started')
    #chats = await db().get_all_tg_id()
    logger.debug(chats)
    for chat_id in chats:
        try:
            #if chat_id["admin"] == 1:
            await initializeBot.bot.send_message(chat_id=chat_id["tg_id"], text=emojize(messages.spam), parse_mode=ParseMode.HTML)
        except Exception as exc:
            logger.exception('Marketing sending error %s %s ', chat_id, str(exc))


@initializeBot.dp.message_handler(filters.restricted, commands=['help'])
async def help_description(message: types.Message):
    """/help - выдает статичное сообщение с подсказкой по работе с ботом.
    """
    logger.info(f'Help function was called by {returnHelper.return_name(message)}'
                f' {vars(message.from_user)} {vars(message.chat)}')
    try:
        msg = messages.help_common % message.from_user.full_name

        user_info = await db().search_users_by_account(message.from_user.username)
        if len(user_info)>0:
            if user_info[0]['is_admin'] == 1:
                msg += messages.help_admin
        logger.info(msg)
        await message.answer(text=emojize(msg), reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception('Help sending error %s', str(e))


@initializeBot.dp.message_handler(filters.restricted, commands=['write_my_chat_id'])
async def write_chat_id(message: types.Message):
    """
        {@tg_username: tg_chat_id}
        Using for private notifications
    """
    logger.info('write chat id started for : %s %s %s %s', message.from_user.username, message.from_user.id, message.chat.title, message.chat.id)
    try:
        tg_login = message.chat.title if message.chat.title else message.from_user.username
        await db().set_user_tg_id(tg_login=tg_login, tg_id=str(message.chat.id))
    except Exception as e:
        logger.exception(f'write chat id exception {str(e)}')


# /duty command from chatbot
@initializeBot.dp.message_handler(filters.restricted, commands=['duty'])
async def duty_admin(message: types.Message):
    """
        Информация о дежурных на дату (N, по умолчанию N = 0, т.е. на сегодня)
        Берется из xerxes.duty_list (таблица заполняется модулем Assistant, раз в час на основании календаря AdminsOnDuty)
    """
    try:
        logger.info('def duties admin started: %s %s %s', returnHelper.return_name(message), message.chat.title, message.chat.id)
        message.bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.typing)
        cli_args = message.text.split()
        # если в /duty передан аргумент в виде кол-ва дней отступа, либо /duty без аргументов
        after_days = int(cli_args[1]) if (len(cli_args) == 2 and float(cli_args[1]).is_integer()) else 0
        duty_date = get_duty_date(datetime.today()) + timedelta(after_days)
        msg = await create_duty_message(duty_date)
        await message.answer(msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception('error in duty admin %s', str(e))


# /myduty command from chatbot
@initializeBot.dp.message_handler(filters.restricted, commands=['myduty'])
async def duty_admin_personal(message: types.Message):
    """
        Информация о дежурных на дату (N, по умолчанию N = 0, т.е. на сегодня)
        Берется из xerxes.duty_list (таблица заполняется модулем Assistant, раз в час на основании календаря AdminsOnDuty)
    """
    try:
        logger.info('def my duty admin started: %s', message.from_user.username)
        message.bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.typing)
        duty_date = get_duty_date(datetime.today())
        msg = await create_duty_message_personal(duty_date, re.sub('@', '', message.from_user.username))
        await message.answer(msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)

        message.bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.typing)
    except Exception as e:
        logger.exception('error in duty admin %s', str(e))


# /timetable command from chatbot
@initializeBot.dp.message_handler(filters.restricted, commands=['timetable', 'meet', 'meetings'])
async def timetable_personal(message: types.Message):
    """
    """
    try:
        cli_args = message.text.split()
        after_days = int(cli_args[1]) if (len(cli_args) == 2 and int(cli_args[1]) > 0) else 0

        user_from_db = db().get_users('tg_id', message.from_user.id)

        if len(user_from_db) > 0:

            header = {'email': user_from_db[0]['email'], 'afterdays': str(after_days)}
            logger.info('timetable personal: %s %s', message.from_user.username, header)

            session = await get_session()
            async with session.get(config.api_get_timetable, headers=header) as resp:
                data = await resp.json(content_type=None)
            msg = data['message']
            if data['status'] == 'error':
                if len(user_from_db) > 0:
                    msg = f"Уважаемый {user_from_db[0]['first_name']} {user_from_db[0]['middle_name']}!\n" + msg
            logger.debug('get timetable personal from api: %s %s', resp.status, resp.json())
        else:
            msg = f"Не нашел данных о {message.from_user.username} в своей БД.\n" + returnHelper.return_quotations()
        await message.answer(msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        logger.exception('error in timetable personal %s', str(e))
        user_from_db = db().get_users('tg_id', message.from_user.id)
        if len(user_from_db) > 0:
            await message.answer(messages.timetable_error.format(user_from_db[0][first_name], user_from_db[0][middle_name]),
                                 reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)


async def create_duty_message(duty_date) -> str:
    dutymen_array = await db().get_duty(duty_date)
    msg = ''

    if len(dutymen_array) > 0:
        if int(datetime.today().strftime("%H")) < 10:
            msg += f":warning: После 10:00 дежурные сменятся.\n\n"
        msg += f"<b>Дежурят на {duty_date.strftime('%Y-%m-%d')}:</b>\n"
        for d in dutymen_array:
            d['tg_login'] = '@' + d['tg_login'] if len(d['tg_login']) > 0 else ''
            msg += f"\n· {d['full_text']} <b>{d['tg_login']}</b>"

        logger.debug('I find duty admin for date %s %s', duty_date.strftime('%Y-%m-%d %H %M'), msg)
    else:
        msg = f"Никого не нашлось в базе бота, посмотрите в календарь AdminsOnDuty.\n" + returnHelper.return_quotations()
    return emojize(msg)


async def create_duty_message_personal(duty_date, tg_login) -> str:
    dutymen_array = await db().get_duty_personal(duty_date, tg_login)
    if len(dutymen_array) > 0:
        msg = f"Дежурства начиная с <b>{duty_date.strftime('%Y-%m-%d')}</b> для @{tg_login}:\n"

        for d in dutymen_array:
            msg += f"\n· {d['area']} - <b>{d['duty_date']}</b>"
        logger.info('I find duty admin for date %s %s', duty_date.strftime('%Y-%m-%d %H %M'), msg)
    else:
        msg = f"Никого не нашлось в базе бота, посмотрите в календарь AdminsOnDuty \n" + returnHelper.return_quotations()
    return msg


def get_duty_date(date):
    # Если запрошены дежурные до 10 утра, то это "вчерашние дежурные"
    # Это особенность дежурств в Департаменте
    if int(datetime.today().strftime("%H")) < int(10):
        return date - timedelta(1)
    else:
        return date


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='send_message_to_admsys_menu'), filters.restricted)
async def send_message_to_admsys_menu(query: types.CallbackQuery, callback_data: str) -> str:
    """
        Create msg with releases in the progress and in the Admsys queue
    """
    try:
        msg = 'Ваше сообщение будет отправлено в рабочий чат ADMSYS, после чего с вами свяжутся (но это неточно).'
        await query.message.reply(msg, reply_markup=keyboard.admsys_send_menu, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f'Error in send message to admsys {str(e)}')


async def send_message_to_admsys():
    """
        Create msg with releases in the progress and in the Admsys queue
    """
    try:
        logger.info(f'-- SEND MESSAGE TO ADMSYS {query.message} {query.message.from_user}')
        await bot.send_message(chat_id='279933948', text='HEY!', disable_notification=True)
    except Exception as e:
        logger.exception(f'Error in send message to admsys {str(e)}')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='get_min_inf_board'), filters.restricted)
async def get_min_inf_board_button(query: types.CallbackQuery, callback_data: str) -> str:
    """
        Create msg with releases in the progress and in the Admsys queue
    """
    del callback_data
    try:
        logger.info('get_min_inf аed from: %s', returnHelper.return_name(query))
        await returnHelper.return_one_second(query)

        async def count_issues() -> str:
            """
                Request to Jira and format msg
            """
            issues_releases_progress = JiraConnection().jira_search(config.search_issues_work)

            issues_admsys = JiraConnection().jira_search(
                'project = DEPLOY AND issuetype = "Release (conf)" AND '
                'status IN (Open, "Waiting release") ORDER BY Rank ASC'
            )
            msg = f'\n - В процессе выкладки: <b>{len(issues_releases_progress)}</b>'
            msg += f'\n - В ожидании релиза: <b>{len(issues_admsys)}</b>'
            return msg

        information_from_jira = await count_issues()
        await query.message.answer(text=information_from_jira, reply_markup=to_main_menu(),
                                   parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('get_min_inf_board_button')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='meetings_today'), filters.restricted)
async def meetings_today(query: types.CallbackQuery, callback_data: str):
    """
    Кнопка, выдающая встречи на сегодня. Аналог команды /meet
    """
    del callback_data
    try:
        user_from_db = db().get_users('tg_id', query.message.chat.id)
        if len(user_from_db) > 0:
            header = {'email': user_from_db[0]['email'], 'afterdays': '0'}
            logger.info('timetable personal: %s %s', query.message.chat.username, header)
            session = await get_session()
            async with session.get(config.api_get_timetable, headers=header) as resp:
                data = await resp.json(content_type=None)
            msg = data['message']
            if data['status'] == 'error':
                if len(user_from_db) > 0:
                    msg = f"Уважаемый {user_from_db[0]['first_name']} {user_from_db[0]['middle_name']}!\n" + msg
            logger.debug('get timetable personal from api: %s %s', resp.status, resp.json())
        else:
            msg = f"Не нашел данных о {query.message.from_user.username} в своей БД.\n" + returnHelper.return_quotations()
        await query.message.answer(msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        logger.exception('error in timetable personal %s', str(e))
        user_from_db = db().get_users('tg_id', query.message.chat.id)
        if len(user_from_db) > 0:
            await query.message.answer(messages.timetable_error.format(user_from_db[0][first_name], user_from_db[0][middle_name]),
                                 reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='duty_button'), filters.restricted)
async def duty_button(query: types.CallbackQuery, callback_data: str):
    """
        Button with duty admin now
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    del callback_data
    try:
        logger.info('duty_button started from: %s', returnHelper.return_name(query))
        msg = ''
        if int(datetime.today().strftime("%H")) < int(10):
            msg += messages.duty_morning_hello % datetime.today().strftime("%H:%M")

        msg += await create_duty_message(get_duty_date(datetime.today()))
        msg += '\n\nЕсли вы хотите узнать дежурных через N дней, отправьте команду /duty N\n\n'
        await query.message.answer(text=msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('duty_button')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='myduty_button'), filters.restricted, filters.is_ops)
async def myduty_button(query: types.CallbackQuery, callback_data: str):
    """
        Информация о дежурствах пользователя
    """
    try:
        logger.info('def myduty admin started: %s', query.from_user.username)
        duty_date = get_duty_date(datetime.today())
        msg = await create_duty_message_personal(duty_date, re.sub('@', '', query.from_user.username))
        await query.message.answer(msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception('error in duty admin %s', str(e))


def to_main_menu() -> types.InlineKeyboardMarkup:
    """
        Return to main menu button
    """
    keyboard_main_menu = [[types.InlineKeyboardButton('Main menu',
                                                      callback_data=keyboard.posts_cb.new(action='main', issue='1'))]]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_main_menu)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='main'), filters.restricted)
async def main_menu(query: types.CallbackQuery, callback_data: str):
    """
        Main menu
    """
    del callback_data
    try:
        logger.info('main_menu started')
        await query.message.answer(text=emojize(messages.main_menu),
                                   reply_markup=keyboard.main_menu(tg_login=query.from_user.username),
                                   parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception('Main menu %s', str(e))


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='admin_menu'), filters.restricted, filters.admin)
async def admin_menu(query: types.CallbackQuery, callback_data: str):
    """
        Open admin menu
    """
    del callback_data
    try:
        logger.info('admin menu opened by %s', returnHelper.return_name(query))
        msg = f'<b>Статус: </b>{keyboard.current_mode()}'
        await query.message.reply(text=emojize(msg), reply_markup=keyboard.admin_menu(),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('admin_menu')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='restart'), filters.restricted, filters.admin)
async def restart(query: types.CallbackQuery, callback_data: str):
    """
        Restart pod with bot
    """
    try:
        del callback_data
        await returnHelper.return_one_second(query)
        dp.stop_polling()
        logger.warning('Bot was restarted... by %s', returnHelper.return_name(query))
        sys.exit(1)
    except Exception:
        logger.exception('restart')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='turn_off'), filters.restricted, filters.admin)
async def stop_bot(query: types.CallbackQuery, callback_data: str):
    """
        Turn off bot
    """
    try:
        del callback_data
        logger.info('-- STOP BOT %s' , returnHelper.return_name(query))
        db().set_parameters('run_mode', 'off')
        msg = messages.bot_was_stopped_manually % returnHelper.return_name(query)
        releases_in_progress = JiraConnection().jira_search(config.search_issues_started)
        rl_list = [rl.key for rl in releases_in_progress]
        data = {'jira_tasks': rl_list, 'text': msg, 'inform_approvers': True, 'disable_notification': False}
        await inform_users_from_jira_ticket(data)
        await query.message.reply('Релизный бот остановлен. Сам не запустится.')
    except Exception as e:
        logger.exception(f'Error in stop bot {str(e)}')


@initializeBot.dp.message_handler(filters.restricted, filters.admin, commands=['lock', 'unlock'])
async def lock_app_release(message: types.Message):
    """
    """
    logger.info('lock app release started by %s %s', returnHelper.return_name(message), message.get_full_command())
    incoming = message.text.split()
    if len(incoming) == 2:
        if message.get_full_command()[0].find('lock') == 1:
            locked_app = {"lock": incoming[1], "unlock": ""}
        elif message.get_full_command()[0].find('unlock') == 1:
            locked_app = {"lock": "", "unlock": incoming[1]}
        locked_app['locked_by'] = "@" + str(message.from_user.username)
        logger.info(f'lock app release sent {locked_app} {str(message.from_user.username)} {type(message.from_user.username)}')
        await lock_releases(locked_app)
        get_app = db().get_application_metainfo(incoming[1])
        logger.info('lock app release %s ', get_app)
        if 'bot_enabled' in get_app:
            msg = f"Релизы {get_app['app_name']} <b>разблокированы</b>" if get_app['bot_enabled'] else f"Релизы {get_app['app_name']} <b>заблокированы</b>"
            msg += f"\n\n<u>Информация о {get_app['app_name']} в БД бота</u>: \n{get_app}"
        else:
            msg = f"Не нашлось сведений о приложении в моей БД. Звоните Чесновскому.\n" + returnHelper.return_quotations()
        await message.answer(text=msg, parse_mode=ParseMode.HTML)


@initializeBot.dp.message_handler(filters.restricted, filters.admin, commands=['show_locks'])
async def show_locked_apps(message: types.Message):
    """

    """
    logger.info('show locked apps started by %s %s', returnHelper.return_name(message), message.get_full_command())
    locked_apps = db().get_applications('bot_enabled', False, 'equal')
    logger.info(locked_apps)
    if len(locked_apps) > 0:
        msg = f'Следующие приложения <b>заблокированы</b> для выкладки ботом:'
        for app in locked_apps:
            msg += f"\n<b> {app['app_name']} </b> , заблокировал {app['locked_by']}"
    else:
        user_from_db = db().get_users('tg_id', message.from_user.id)
        if len(user_from_db) > 0:
            msg = f"Уважаемый {user_from_db[0]['first_name']} {user_from_db[0]['middle_name']}, заблокированных приложений нет."
        else:
            msg = f'Нет заблокированных приложений.'
    await message.answer(msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)


async def lock_releases(locked_app):
    logger.info(f'-- LOCK RELEASE {locked_app}')
    try:
        session = await get_session()
        resp = requests.post(config.api_lock_unlock, data=json.dumps(locked_app))
        logger.info('lock send locked app to api, status is: %s', resp)
        return True
    except Exception as exc:
        logger.exception(f'lock_unlock_task {str(exc)}')
        return str(exc)


##############################################################################################
#              Кнопки админского меню
##############################################################################################

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='turn_on'), filters.restricted, filters.admin)
async def start_bot(query: types.CallbackQuery, callback_data: str):
    """
        Сменить режим бота на выкладку релизов
    """
    del callback_data
    logger.warning('%s started bot', returnHelper.return_name(query))
    db().set_parameters('run_mode', 'on')
    msg = messages.bot_was_started_manually % returnHelper.return_name(query)
    releases_in_progress = JiraConnection().jira_search(config.search_issues_started)
    rl_list = [rl.key for rl in releases_in_progress]
    data = {'jira_tasks': rl_list, 'text': msg, 'inform_approvers': True, 'disable_notification': False}
    await inform_users_from_jira_ticket(data)
    await query.message.reply('Релизный бот запущен.')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='dont_touch'), filters.restricted, filters.admin)
async def dont_touch_releases(query: types.CallbackQuery, callback_data: str):
    """
        Don't touch releases on Jira board
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    del callback_data
    logger.warning('%s pressed button Don\'t touch new release',
                   returnHelper.return_name(query))
    db().set_parameters('run_mode', 'last')
    await query.message.reply('Новые релизы брать не буду. Всё, что уже на мне в Jira - докачу.')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='release_app_list'), filters.restricted, filters.admin)
async def release_app_list(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    #issue_key = callback_data['issue_key']
    logger.info('-- RELEASE APP LIST menu opened by %s %s', returnHelper.return_name(query), callback_data)
    msg = f'Релизы, которые я могу выкатить (находятся в статусе Waiting на доске):'
    await query.message.reply(text=msg, reply_markup=keyboard.release_app_list(), parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='release_app'), filters.restricted, filters.admin)
async def release_app(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    logger.info('-- RELEASE APP started by %s %s', returnHelper.return_name(query), callback_data)
    msg = f"Точно выкатываем {callback_data['issue']} ?"
    await query.message.reply(text=msg, reply_markup=keyboard.release_app_confirm(callback_data['issue']), parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='release_app_confirm'), filters.restricted, filters.admin)
async def release_app_confirm(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    logger.info('-- RELEASE APP CONFIRM started by %s %s', returnHelper.return_name(query), callback_data)
    try:
        logger.info('Assign %s to Releasebot', callback_data['issue'])
        JiraConnection().assign_issue(callback_data['issue'], config.jira_user)
        JiraConnection().add_comment(callback_data['issue'], f"Назначен на бота неким {returnHelper.return_name(query)}")
    except Exception as e:
        logger.exception('Error in RELEASE APP CONFIRM %s', e)
    await query.answer(f"Съел релиз {callback_data['issue']}, перевариваю.")


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='rollback_app_list'), filters.restricted, filters.admin)
async def rollback_app_list(query: types.CallbackQuery, callback_data: str):
    """
        Выставить у релиза резолюцию "Rollback"
    """
    logger.info('-- ROLLBACK APP LIST menu opened by %s %s', returnHelper.return_name(query), callback_data)
    msg = f'Релизы, которые я могу откатить (выехали хотя бы на один хост на доске):'
    await query.message.reply(text=msg, reply_markup=keyboard.rollback_app_list(), parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='rollback_app'), filters.restricted, filters.admin)
async def rollback_app(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    logger.info('-- ROLLBACK APP started by %s %s', returnHelper.return_name(query), callback_data)
    msg = f"Точно откатываем {callback_data['issue']} ?"
    await query.message.reply(text=msg, reply_markup=keyboard.rollback_app_confirm(callback_data['issue']), parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='rollback_app_confirm'), filters.restricted, filters.admin)
async def rollback_app_confirm(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    logger.info('-- ROLLBACK APP CONFIRM started by %s %s', returnHelper.return_name(query), callback_data)
    try:
        JiraConnection().transition_issue_with_resolution(callback_data['issue'], JiraTransitions.FULL_RESOLVED.value, {'id': '10300'})
        JiraConnection().add_comment(callback_data['issue'], f"Откатывает некий {returnHelper.return_name(query)}")
    except Exception as e:
        logger.error('Error in ROLLBACK APP CONFIRM %s', e)
    await query.answer(f"Откатываю релиз {callback_data['issue']}. Потому что я красавчик.")


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='retry_inprogress_releases_confirm'), filters.restricted, filters.admin)
async def retry_inprogress_releases_confirm(query: types.CallbackQuery, callback_data: str):
    """
        Сбросить признак retry для всех релизов в рабочих статусах. 
        Если было массовое падение релизов, после починки поможет боту взять их все ещё раз в работу.
    """
    try:
        logger.info(f'-- RETRY INPROGRESS RELEASES CONFIRM started by {returnHelper.return_name(query)}, {callback_data}')
        msg = "Включить авто-ретрай всех релизов в процессе выкладки? Бот запустит их только в том случае, если последняя джоба в статусе FAILED."
        await query.message.reply(text=msg, reply_markup=keyboard.retry_inprogress_releases(), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error('Error in ROLLBACK APP CONFIRM %s', e)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='retry_inprogress_releases'), filters.restricted, filters.admin)
async def retry_inprogress_releases(query: types.CallbackQuery, callback_data: str):
    """
        Сбросить признак retry для всех релизов в рабочих статусах. 
        Если было массовое падение релизов, после починки поможет боту взять их все ещё раз в работу.
    """
    logger.info(f'-- RETRY INPROGRESS RELEASES started by {returnHelper.return_name(query)}, {callback_data}')
    try:
        releases_inprogress = JiraConnection().jira_search(config.search_issues_work)
        for rl in releases_inprogress:
            db().set_release_retries_count(jira_task=rl.key, retries=0)
    except Exception as e:
        logger.error(f'Error in RETRY INPROGRESS RELEASES {str(e)}')
    await query.message.reply(f"Все упавшие релизы будут перезапущены.")


@initializeBot.dp.callback_query_handler(keyboard.duty_cb.filter(action='take_duty_date_list'), filters.restricted, filters.is_ops)
async def take_duty_date_list(query: types.CallbackQuery, callback_data: dict):
    """
        Список дат для взятия дежурства на себя
    """
    logger.info('-- TAKE DUTY DATE LIST menu opened by %s %s', returnHelper.return_name(query), callback_data)
    msg = f'Выберите дату для дежурства:'
    await query.message.reply(text=msg, reply_markup=keyboard.take_duty_date_list(), parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.duty_cb.filter(action='take_duty_area_list'), filters.restricted, filters.is_ops)
async def take_duty_area_list(query: types.CallbackQuery, callback_data: dict):
    """
        Взять дежурство
    """
    logger.info('-- TAKE DUTY AREA LIST started by %s %s', returnHelper.return_name(query), callback_data)
    msg = f"Выберите зону ответственности:"
    await query.message.reply(text=msg, 
                              reply_markup=keyboard.take_duty_area_list(ddate=callback_data['ddate'], dutyman=query.from_user.username), 
                              parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.duty_cb.filter(action='take_duty_confirm'), filters.restricted, filters.is_ops)
async def take_duty_confirm(query: types.CallbackQuery, callback_data: dict):
    """
        Подтвердить взятие дежурства
    """
    logger.info('-- TAKE DUTY CONFIRM started by %s %s', returnHelper.return_name(query), callback_data)
    day_of_week = config.DaysOfWeek[datetime.strptime(callback_data['ddate'], '%Y-%m-%d').strftime('%A')].value
    msg = f"Забираете дежурство {callback_data['ddate']} {day_of_week} - {callback_data['area']} ?"
    await query.message.reply(text=msg, reply_markup=keyboard.take_duty_confirm(callback_data['ddate'], callback_data['area']), parse_mode=ParseMode.HTML)


@initializeBot.dp.callback_query_handler(keyboard.duty_cb.filter(action='take_duty'), filters.restricted, filters.is_ops)
async def take_duty(query: types.CallbackQuery, callback_data: str):
    """
       Взять дежурство (вызов в API)
    """
    logger.info('-- TAKE DUTY started by %s %s', returnHelper.return_name(query), callback_data)
    try:
        take_duty_msg = {}
        user_from_db = db().get_users('tg_id', query.message.chat.id)
        take_duty_msg['person'] = user_from_db[0]['full_name']
        take_duty_msg['duty_date'] = callback_data['ddate']
        take_duty_msg['area'] = callback_data['area']
        take_duty_msg['account_name'] = user_from_db[0]['account_name']
        take_duty_msg['tg_login'] = user_from_db[0]['tg_login']
        logger.info(f'Sending msg to take_duty api {take_duty_msg}')
        resp = requests.post(config.api_take_duty, data=json.dumps(take_duty_msg))
        logger.info(f'TAKE DUTY response from API {resp}')
    except Exception as e:
        logger.error(f'Error in TAKE DUTY {str(e)}')
    await query.answer(f"Назначил на вас дежурство. Спасибо.")


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='dev_team_members'), filters.restricted)
async def dev_team_members_answer(query: types.CallbackQuery, callback_data: str):
    """
    """
    #issue_key = callback_data['issue_key']
    logger.info('-- DEV TEAM MEMBERS started by %s %s', returnHelper.return_name(query), callback_data)
    try:
        msg = await get_dev_team_members(callback_data['issue'])
    except Exception as e:
        logger.error('Error in DEV TEAM MEMBERS %s', e)
    logger.info(msg)
    await query.message.reply(msg, parse_mode=ParseMode.HTML)

def dev_team_members(dev_team) -> types.InlineKeyboardMarkup:
    """
    """
    keyboard_main_menu = [[types.InlineKeyboardButton('Состав команды',
                                                      callback_data=keyboard.posts_cb.new(action='dev_team_members', issue=dev_team))]]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_main_menu)


##############################################################################################

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='return_queue'), filters.restricted)
async def return_to_queue(query: types.CallbackQuery, callback_data: str):
    """
        Create menu with Jira task which can be returned or will write msg
        "Now there is nothing to return to the queue"
    """
    del callback_data
    try:
        await returnHelper.return_one_second(query)
        if waiting_assignee_issues := JiraConnection().jira_search(config.waiting_assignee_releases):
            msg = 'This is Jira task, which may be returned to the queue'
            markup = keyboard.return_queue_menu(waiting_assignee_issues)
            await query.message.reply(text=msg,
                                      reply_markup=markup,
                                      parse_mode=ParseMode.HTML)
        else:
            msg = 'Now there is <b>nothing</b> to return to the queue'
            await query.message.reply(text=msg,
                                      reply_markup=to_main_menu(),
                                      parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('return_to_queue')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='return_release'), filters.restricted)
async def process_return_queue_callback(query: types.CallbackQuery, callback_data: str):
    """
        Получит callback_data["issue"] (через keyboard.return_queue_menu)
        Вернет таску в начало очереди, если это сделал один из согласующих.
    """
    try:
        await returnHelper.return_one_second(query)
        jira_issue_id = callback_data['issue']
        # Получить список согласующих
        chat_id_recipients = jira_get_approvers_list(jira_issue_id)
        logger.info('chat_id_recipients: %s', chat_id_recipients)

        msg = f'Вернул в очередь <b>{jira_issue_id}</b>. Попробую выкатить позже.'
        # Передвинем таску в начало доски и снимем её с бота
        jira_object = JiraConnection()
        jira_object.assign_issue(jira_issue_id, None)
        jira_object.transition_issue(jira_issue_id, JiraTransitions.FULL_WAIT.value)
        jira_object.add_comment(jira_issue_id, "Задача была возвращена в очередь одним из согласующих через телеграм.")

        await query.message.reply(text=msg, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('process_return_queue_callback')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='subscribe'), filters.restricted)
async def subscribe_events(query: types.CallbackQuery, callback_data: str):
    """
    Подписать пользователя на события
    {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    del callback_data
    try:
        logger.info('subscribe_events opened by %s', returnHelper.return_name(query))
        msg = 'Вы можете подписаться на уведомления обо всех релизах. ' \
              'Уведомления о ваших релизах будут работать в любом случае, от них отписаться нельзя.'
        user_from_db = db().get_users('tg_id', query.message.chat.id)
        user_subscriptions = await get_current_user_subscription(user_from_db[0]['account_name'])
        msg += '\n\n<b>Ваши текущие подписки</b>:\n' + user_subscriptions
        await query.message.reply(text=msg, reply_markup=keyboard.subscribe_menu(),
                                  parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("subscribe")


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='release_events'), filters.restricted)
async def release_events(query: types.CallbackQuery, callback_data: str):
    """
    """
    try:
        del callback_data
        logger.info('-- RELEASE EVENTS a %s chat %s ', query.message.chat.type, query.message.chat)
        user_from_db = db().get_users('tg_id', query.message.chat.id)
        user_subscriptions = await db().get_user_subscriptions(user_from_db[0]['account_name'])
        if 'release_events' in user_subscriptions:
            await db().delete_user_subscription(user_from_db[0]['account_name'], 'release_events')
            msg = 'Вы отписаны от уведомлений по всем релизам.'
        else:
            await db().set_user_subscription(user_from_db[0]['account_name'], 'release_events')
            msg = 'Вы подписаны на уведомления по всем релизам.'

        user_subscriptions = await get_current_user_subscription(user_from_db[0]['account_name'])
        msg += '\n\n<b>Ваши подписки</b>:\n' + user_subscriptions
        await query.message.reply(text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("-- RELEASE EVENTS %s", e)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='timetable_reminder'), filters.restricted)
async def timetable_reminder(query: types.CallbackQuery, callback_data: str):
    """
    """
    try:
        del callback_data
        logger.info('-- TIMETABLE REMINDER %s chat %s ', query.message.chat.type, query.message.chat)
        if (query.message.chat.type == 'private'):
            user_from_db = db().get_users('tg_id', query.message.chat.id)
            user_subscriptions = await db().get_user_subscriptions(user_from_db[0]['account_name'])
            if 'timetable' in user_subscriptions:
                await db().delete_user_subscription(user_from_db[0]['account_name'], 'timetable')
                msg = 'Вы отписаны от напоминаний о расписании встреч.'
            else:
                await db().set_user_subscription(user_from_db[0]['account_name'], 'timetable')
                msg = 'Вы подписаны на напоминания о расписании встреч.'
        else:
            msg = 'Подписаться на календарь можно только для аккаунтов в AD'
            logger.info('Подписаться на календарь можно только для аккаунтов в AD %s', query.message.chat.id)
        
        user_subscriptions = await get_current_user_subscription(user_from_db[0]['account_name'])
        msg += '\n\n<b>Ваши подписки</b>:\n' + user_subscriptions
        await query.message.reply(text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("Error in TIMETABLE REMINDER %s", e)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='statistics_reminder'), filters.restricted)
async def statistics_reminder(query: types.CallbackQuery, callback_data: str):
    """
    """
    try:
        del callback_data
        logger.info('-- STATISTICS REMINDER %s chat %s ', query.message.chat.type, query.message.chat)
        user_from_db = db().get_users('tg_id', query.message.chat.id)
        user_subscriptions = await db().get_user_subscriptions(user_from_db[0]['account_name'])
        if 'statistics' in user_subscriptions:
            await db().delete_user_subscription(user_from_db[0]['account_name'], 'statistics')
            msg = 'Вы отписаны от рассылки статистики по релизам.'
        else:
            await db().set_user_subscription(user_from_db[0]['account_name'], 'statistics')
            msg = 'Вы подписаны на рассылку статистики по релизам.'
        
        user_subscriptions = await get_current_user_subscription(user_from_db[0]['account_name'])
        msg += '\n\n<b>Ваши подписки</b>:\n' + user_subscriptions
        await query.message.reply(text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("Error in STATISTICS REMINDER %s", e)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='duties_reminder'), filters.restricted)
async def duties_reminder(query: types.CallbackQuery, callback_data: str):
    """
    """
    try:
        del callback_data
        logger.info('-- DUTIES REMINDER a %s chat %s ', query.message.chat.type, query.message.chat)
        user_from_db = db().get_users('tg_id', query.message.chat.id)
        user_subscriptions = await db().get_user_subscriptions(user_from_db[0]['account_name'])
        if 'duties' in user_subscriptions:
            await db().delete_user_subscription(user_from_db[0]['account_name'], 'duties')
            msg = 'Вы отписаны от уведомлений по собственным дежурствам.'
        else:
            await db().set_user_subscription(user_from_db[0]['account_name'], 'duties')
            msg = 'Вы подписаны на уведомления по собственным дежурствам.'

        user_subscriptions = await get_current_user_subscription(user_from_db[0]['account_name'])
        msg += '\n\n<b>Ваши подписки</b>:\n' + user_subscriptions
        await query.message.reply(text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("-- DUTIES REMINDER %s", e)


@initializeBot.dp.message_handler(filters.restricted, commands=['app'])
async def app_info(message: types.Message):
    """
    Вытащить инфу о приложении из БД Бота
    """
    logger.info( '-- APP INFO started by %s', returnHelper.return_name(message))
    incoming = message.text.split()
    try:
        if len(incoming) >= 2:
            app_name_list = incoming[1:]
            msg = '<u><b>Результаты поиска</b></u>:'
            msg_additional = ''
            for app_name in app_name_list:
                app_info = db().get_application_metainfo(app_name)
                last_release = db().get_last_deploy_task_number(app_name)
                logger.info('Got application metainfo %s', app_info)
                if len(app_info) > 0:
                    msg += f'\n Имя приложения: <strong>{app_info["app_name"]}</strong>'
                    msg += f'\n Периметр: <strong>{app_info["perimeter"]}</strong>'
                    msg += f'\n Режим выкладки: <strong>{app_info["release_mode"]}</strong>'
                    msg += f'\n Администраторы: <strong>{app_info["admins_team"]}</strong>'
                    msg += f'\n Разработчики: <a href="/dev_team {app_info["dev_team"]}">{app_info["dev_team"]}</a>'
                    msg += f'\n Релизные очереди: <strong>{app_info["queues"].replace(",", ", ")}</strong>'
                    msg += f"\n <a href='https://wiki.yooteam.ru/display/admins/ReleaseBot.ReleaseMaster#ReleaseBot.ReleaseMaster-%D0%A0%D0%B5%D0%B6%D0%B8%D0%BC%D1%8B%D0%B2%D1%8B%D0%BA%D0%BB%D0%B0%D0%B4%D0%BA%D0%B8Modes'>Подробнее о параметрах</a>\n"
                    if len(last_release) > 0:
                        msg+= f"Последний успешный релиз: <a href='{config.jira_host}/browse/{last_release}'>{last_release}</a>\n\n"
                    else:
                        msg+= f"Последний успешный релиз: не найден\n\n"
                    if app_info["bot_enabled"]:
                        msg += f'\n :green_circle: Бот <strong>включен</strong> для приложения'
                    else:
                        msg += f'\n :red_circle: Бот <strong>выключен</strong> для приложения, заблокировал <strong>{app_info["locked_by"]}</strong>'
                    locking_rl = get_lock_reasons(app_name)
                    if (len(locking_rl) > 0):
                        msg += f'\n :red_circle: Релиз <strong>заблокирован</strong> следующими компонентами:'
                        for rl in locking_rl:
                            if rl["app_name"] != app_name:
                                msg += f'\n • <strong>{rl["app_name"]}</strong> (очереди: {rl["queues"].replace(",", ", ")})'
                            else:
                                msg_additional = f'\n :yellow_circle: <a href=\"https://jira.yooteam.ru/browse/{rl["jira_task"]}\">{rl["fullname"]}</a> Компонент в процессе выкладки на доске'
                        msg += msg_additional
                        msg += f'\n Детали можно найти на <a href="https://jira.yooteam.ru/secure/RapidBoard.jspa?rapidView=1557">релизной доске</a>'
                    else:
                        msg += f'\n :green_circle: Релизная очередь приложения свободна'                    
                    dev_team_name = app_info["dev_team"]
                else:
                    msg = 'Приложение не найдено'
        else:
            msg = 'Ошибка: задайте имя приложения. \n' + returnHelper.return_quotations()
        if 'dev_team_name' in locals():
            if dev_team_name is not None:
                await message.answer(text=emojize(msg), reply_markup=dev_team_members(dev_team_name), parse_mode=ParseMode.HTML)
                return True
        await message.answer(text=emojize(msg), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception('Error in APP INFO %s', e)


@initializeBot.dp.message_handler(filters.restricted, commands=['dev_team', 'command', 'devteam', 'team'])
async def dev_team_info(message: types.Message):
    """
    Вытащить инфу о приложении из БД Бота
    """
    logger.info( '-- DEV TEAM INFO started by %s', returnHelper.return_name(message))
    incoming = message.text.split()
    try:
        if len(incoming) == 2:
            dev_team_name = incoming[1]
            msg = await get_dev_team_members(dev_team_name)
        else:
            msg = 'Ошибка: задайте название одной команды'
        await message.answer(text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception('Error in DEV TEAM INFO %s', e)


@initializeBot.dp.message_handler(filters.restricted, filters.admin, commands=['where_app', 'where'])
async def where_app_hosts(message: types.Message):
    """
    Запросить список гипервизоров, где в данный момент находится приложение
    """
    logger.info( '-- WHERE APP HOSTS info started by %s', returnHelper.return_name(message))
    incoming = message.text.split()
    try:
        if len(incoming) >= 2:
            app_name_list = incoming[1:]
            msg = '<u><b>Результаты поиска</b></u>:'
            for app_name in app_name_list:
                msg += f'\n <strong>{ await couch_client.search_lxc_for_app(app_name) }</strong> \n'
        else:
            msg = 'Error: app_name not found'
        await message.answer(text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception('Error in WHERE APP HOSTS %s', e)


@initializeBot.dp.message_handler(filters.restricted, commands=['who'])
async def get_user_info(message: types.Message):
    """
    Ручки поиска по БД. Светят наружу в API. 
    /who Выдать информацию по пользователю из таблицы xerxes.users
    """
    logger.info('-- GET USER INFO started by %s', returnHelper.return_name(message))
    incoming = message.text.split()
    if (len(incoming) == 2) or (len(incoming) == 3):
        probably_username  = incoming[1:]
        try:
            if bool(re.search('[а-яА-Я]', probably_username[0])):
                user_info = await db().search_users_by_fullname(probably_username)
            else:
                # Уберем почту с конца строки, затем уберем @ если был задан ТГ-логин с собакой
                probably_username = re.sub('@yamoney.ru|@yoomoney.ru|@', '', probably_username[0])
                user_info = await db().search_users_by_account(probably_username)
            logger.info('get user info found %s', user_info)
            if len(user_info) > 0:
                msg = '<u><b>Нашёл</b></u>:'
                for user in user_info:
                    msg += f'\n Логин AD: <strong>{user["account_name"]}</strong>'
                    msg += f'\n Имя: <strong>{user["full_name"]}</strong>'
                    msg += f'\n Стафф: <a href=\"{config.staff_url}/#/{user["staff_login"]}\"><strong>{user["staff_login"]}</strong></a>'
                    msg += f'\n Почта: <strong>{user["email"]}</strong>'
                    msg += f'\n Телеграм: <strong>@{user["tg_login"]}</strong>'
                    msg += f'\n Телеграм ID: <strong>{user["tg_id"]}</strong>'
                    msg += f'\n Рабочий статус: <strong>{user["working_status"]}</strong>'
                    if user['team_name'] != None:
                        msg += f'\n Отдел: <strong>{user["team_name"]}</strong>'
                    if user['department'] != None:
                        msg += f'\n Департамент: <strong>{user["department"]}</strong>'
                    user_teams = await get_user_membership(user["account_name"])
                    if len(user_teams) > 0:
                        for t in user_teams:
                            msg += f'\n Команда: <strong>{t["dev_team"]} ({t["team_name"]})</strong>'
                    msg += '\n'
            else:
                msg = 'Пользователей в моей базе не найдено'
        except Exception as e:
            logger.exception('Error GET USER INFO %s', e)
    else:
        msg = 'Пожалуйста, попробуйте еще раз: /who username'
    await message.answer(text=msg, parse_mode=ParseMode.HTML)


@initializeBot.dp.message_handler(filters.restricted, commands=['start'])
async def show_main_menu_button(message: types.Message):
    """
    """
    await message.reply("Hi!", reply_markup=keyboard.reply_main_menu)


async def send_message_to_tg_chat(chat_id: str, message: str, silence=True, parse_mode=ParseMode.HTML, 
                                  escape_html: bool = False, emoji: bool = False):
    """
    Обёртка поверх bot.send_message
    """
    try:
        logger.info(f"Sending for chat_id {chat_id} {parse_mode} {escape_html} {message} {silence} {emoji}")
        if escape_html:
            message = quote_html(message)
        if emoji:
            message = emojize(message)
        if len(message) > 4096:
            message = message[0:4000]
            # лимит сообщения в ТГ - 4096 символов. Т.к. мы можем обрезать html тег (что приведет к ошибке отправки)
            # следует обрезать строчку целиком. Например так
            offset = re.search(r'\n',message[::-1])
            if offset != None:
                message = message[:-offset.end()]
            message = message + '\n ...\nСООБЩЕНИЕ БЫЛО ОБРЕЗАНО - ПРЕВЫШЕНА ДЛИНА'
        await bot.send_message(chat_id=chat_id, text=message, 
                    disable_notification=silence, parse_mode=parse_mode)
    except BotBlocked:
        logger.info('YM release bot was blocked by %s', chat_id)
    except ChatNotFound:
        logger.error('Chat not found with: %s', chat_id)
    except Exception as e:
        logger.exception('Error sending to chat_id %s', str(e))


async def send_message_to_users(request):
    """
    # Внешняя ручка рассылки
    {'accounts': [list of account_names], 'jira_tasks': [list of tasks_id], 'text': str, 
      'inform_approvers': True, 'inform_watchers': True, 'text_jira': str, 'escape_html': bool}
    'inform_approvers': True - отправит уведомление согласующим таски. Номер таски обязателене
    'inform_watchers': True - отправит уведомление наблюдающим за таской. Номер таски обязателене
    """
    data_json = await request.json()
    logger.info(f"-- SEND MESSAGE TO USERS {data_json}")
    if 'disable_notification' in data_json:
        disable_notification = data_json['disable_notification']
    else:
        disable_notification = False

    if 'escape_html' in data_json:
        escape_html = data_json['escape_html']
    else:
        escape_html = False

    if 'emoji' in data_json:
        emoji = data_json['emoji']
    else:
        emoji = False

    if 'polite' in data_json:
        polite = data_json['polite']
    else:
        polite = False

    if 'accounts' in data_json:
        if type(data_json['accounts']) == str:
            data_json['accounts'] = [data_json['accounts']]

        for acc in data_json['accounts']:
            user_from_db = db().get_users('account_name', re.sub('@yamoney.ru|@yoomoney.ru|@', '', acc))
            if len(user_from_db) > 0:
                if user_from_db[0]['tg_id'] != None and user_from_db[0]['working_status'] != 'dismissed':
                    msg = _make_message_polite(data_json['text'], user_from_db[0]) if polite else data_json['text']
                    await send_message_to_tg_chat(chat_id=user_from_db[0]['tg_id'], message=msg, silence=disable_notification, 
                                                parse_mode=ParseMode.HTML, escape_html=escape_html, emoji=emoji)

    if 'jira_tasks' in data_json:
        await inform_users_from_jira_ticket(data_json)
    return web.json_response()


async def inform_users_from_jira_ticket(data_json: dict, disable_notification: str = True, escape_html: str = False, emoji: str = True):
    """
    """
    for task in data_json['jira_tasks']:
        if 'inform_approvers' in data_json and 'text' in data_json:
            logger.info('Go inform_approvers %s', data_json['inform_approvers'])
            if data_json['inform_approvers'] == True and len(data_json['text']) > 0:
                email_approvers = jira_get_approvers_list(task)
                for email in email_approvers:
                    user_from_db = db().get_users('account_name', email)
                    if len(user_from_db) > 0:
                        if user_from_db[0]['tg_id'] != None and user_from_db[0]['working_status'] != 'dismissed':
                            await send_message_to_tg_chat(chat_id=user_from_db[0]['tg_id'], message=data_json['text'], 
                                                            silence=disable_notification, parse_mode=ParseMode.HTML, escape_html=escape_html, emoji=emoji)
        if 'inform_watchers' in data_json and 'text' in data_json:
            if data_json['inform_watchers'] == True and len(data_json['text']) > 0:
                email_watchers = jira_get_watchers_list(task)
                for email in email_watchers:
                    user_from_db = db().get_users('account_name', email)
                    if len(user_from_db) > 0:
                        if user_from_db[0]['tg_id'] != None and user_from_db[0]['working_status'] != 'dismissed':
                            await send_message_to_tg_chat(chat_id=user_from_db[0]['tg_id'], message=data_json['text'], 
                                                            silence=disable_notification, parse_mode=ParseMode.HTML, escape_html=escape_html, emoji=emoji)
        if 'text_jira' in data_json:
            try:
                logger.info('Leave comment to %s %s', JiraConnection().issue(task), data_json['text_jira'] )
                JiraConnection().add_comment(JiraConnection().issue(task), data_json['text_jira'])
            except Exception as e:
                logger.exception('Error send message to users when commenting jira task %s', str(e))


async def get_dev_team_members(dev_team) -> str:
    logger.info('GET DEV TEAM MEMBERS for %s', dev_team)
    msg = '<u><b>Результаты поиска</b></u>:'
    tt_api_uri = config.tt_api_url + f"?team={dev_team.upper()}&onlyActualTeamsData"
    tt_api_response = requests.get(
        tt_api_uri,
        auth=HttpNtlmAuth(config.jira_user, config.jira_pass),
        verify=False)
    for d in tt_api_response.json():
        msg += f"\n <u>Логин</u>: <a href='{config.staff_url}/#/{d['user']['login']}'><strong>{d['user']['login']}</strong></a>"
        msg += f"\n Имя: <strong>{d['user']['name']}</strong>"
        msg += f"\n Позиция: <strong>{d['position']['name']}</strong>"
        msg += f"\n Департамент: <strong>{d['department']['name']}</strong>"
        # Поищем tg-логин пользователя
        user_from_db = db().get_users('account_name', d['user']['login'])
        if len(user_from_db) > 0:
            if user_from_db[0]['tg_login'] != None and user_from_db[0]['working_status'] != 'dismissed':
                msg += f"\n Telegram: <strong>@{user_from_db[0]['tg_login']}</strong>"
        msg += f"\n"
    return msg


async def get_user_membership(login) -> str:
    logger.info('GET USER MEMBERSHIP for %s', login)
    teams = []
    try:
        tt_api_uri = config.tt_api_url + f"?teammate={login}&onlyActualTeamsData"
        tt_api_response = requests.get(
            tt_api_uri,
            auth=HttpNtlmAuth(config.jira_user, config.jira_pass),
            verify=False)
        for d in tt_api_response.json():
            if d['user']['login'] == login:
                teams.append({'dev_team': d['team']['key'], 'team_name': d['team']['name']})
    except Exception as e:
        logger.exception('Erorr in get user memebershi %s', str(e))
    finally:
        return teams


async def get_user_from_staff(login) -> dict:
    users_dict = {}
    users_dict = requests.get(f'{config.staff_url}/1c82_lk/hs/staff/v1/persons/{login}', 
                            auth=HttpNtlmAuth(config.jira_user, config.jira_pass), verify=False)
    return users_dict.json()


async def inform_duty(request):
    """
    Внешняя ручка для информирования дежурных
    {'areas': ['ADMSYS(портал)', ...], 'message': str}
    areas - задаются в календаре AdminsOnDuty, перед именем дежурного
    """
    data_json = await request.json()
    logger.info(f"-- INFORM DUTY {data_json}")
    if 'areas' in data_json:
        try:
            for area in data_json['areas']:
                escape_html = data_json.get('escape_html', False)
                silence = data_json.get('silence', False)
                await inform_today_duty(area=area, message=data_json['message'], escape_html=escape_html, silence=silence)
        except Exception as e:
            logger.exception('Error inform duty %s', e)
    return web.json_response()


async def inform_subscribers(request):
    """
    Внешняя ручка для информирования подписанных на информинги =)
    {'notification': 'release_events', 'message': str}
    notification можно найти в таблице Xerxes.Users в соответствующем поле
    """
    data_json = await request.json()
    logger.info(f"-- INFORM SUBSCRIBERS {data_json}")

    if 'emoji' in data_json:
        emoji = data_json['emoji']
    else:
        emoji = False

    if 'notification' in data_json:
        subscribers = await db().get_all_users_with_subscription(data_json['notification'])
        logger.info('Inform subscribers going through list %s', subscribers)
        for user in subscribers:
            try:
                logger.debug(f"Inform subscribers sending message to {user['tg_login']}, {user['tg_id']}, {data_json['text']}")
                if user['tg_id'] and user['working_status'] != 'dismissed':
                    await send_message_to_tg_chat(chat_id=user['tg_id'], message=data_json['text'], 
                                                  silence=True, parse_mode=ParseMode.HTML, emoji=emoji)
            except BotBlocked:
                logger.info('Error Inform subscribers bot was blocked by %s', user)
            except ChatNotFound:
                logger.error('Error Inform subscribers Chat not found: %s', user)        
            except Exception as e:
                logger.exception('Error inform subscribers %s', e)
    return web.json_response()


async def lock_apps(request):
    """
    Внешняя ручка для блокировки приложений
    {'lock': ['shiro', 'shop'], 'unlock': ['makeupd']}
    Если засунуть в нее одно и то же приложение, то финальным отработает unlock
    """
    data_json = await request.json()
    logger.info(f"-- LOCK APPS {data_json}")
    locked_app = {'lock': '', 'unlock': ''}
    processed_apps = []
    if 'lock' in data_json:
        locked_app["lock"] = ','.join(data_json['lock'])
        processed_apps = processed_apps + data_json['lock']
    if 'unlock' in data_json:
        locked_app["unlock"] = ','.join(data_json['unlock'])
        processed_apps = processed_apps + data_json['unlock']
    locked_app["locked_by"] = 'from_api'
    await lock_releases(locked_app)
    app_statuses = []
    for app in processed_apps:
        get_app = db().get_application_metainfo(app)
        app_statuses.append(get_app)
    logger.info('-- Lock apps app statuses %s', app_statuses)
    return web.json_response(app_statuses)


def get_lock_reasons(app_name):
    """
    Проверка блокировок релиза. Для app_name вернет список приложений, которые в данные момент в процессе
    релиза и блокируют хотя бы одну релизную очередь app_name.
    """
    try:
        releases_started = JiraConnection().jira_search(config.search_issues_started)
        rl_board_dict = {}
        locking_rl = []
        app_info = db().get_application_metainfo(app_name)
        for rl in releases_started:
            app_name_version_json = _app_name_regex(rl.fields.summary)
            rl_board_dict[app_name_version_json['name']] = {"fullname": rl.fields.summary, "jira_task": rl.key}
        for rl_app in db().get_many_applications_metainfo(list(rl_board_dict.keys())):
            if (any(elem in rl_app['queues'].split(',') for elem in app_info['queues'].split(','))):
                rl_app.update(rl_board_dict[rl_app['app_name']])
                locking_rl.append(rl_app)
        logger.info(f'Debug for lock_reasons {app_info} \n {rl_board_dict} \n {locking_rl}')
        return locking_rl
    except Exception as e:
        logger.exception('Error in get lock reasons %s', e)
        return []

async def inform_today_duty(area: str, message: str, escape_html: bool = False, silence: bool = False):
    """
    Функция отправки сообщения сегодняшнему дежурному
    """
    dutymen_array = await db().get_duty_in_area(get_duty_date(datetime.today()), area)
    logger.info('-- INFORM TODAY DUTY %s %s', dutymen_array, message)
    if len(dutymen_array) > 0:
        for d in dutymen_array:
            try:
                dutymen = db().get_users('account_name', d['account_name'])
                logger.info('informing duty %s %s %s', dutymen[0]['tg_id'], dutymen[0]['tg_login'], message)
                await send_message_to_tg_chat(chat_id=dutymen[0]['tg_id'], message=message, parse_mode=ParseMode.HTML, 
                                              silence=silence, escape_html=escape_html)
            except BotBlocked:
                logger.info('YM release bot was blocked by %s', d['tg_login'])
            except ChatNotFound:
                logger.error('Chat not found with: %s', d['tg_login'])
            except Exception as e:
                logger.exception('Error in INFORM TODAY DUTY %s', e)  

async def get_app_external(request):
    """
    Запросить инфу о приложении из БД бота
    """
    try:
        app_name = request.match_info.get('app_name', None)
        if not app_name:
            return web.HTTPBadRequest(body='app_name shoud be defined')
        app_info = get_app_info(app_name)
        return web.json_response(app_info)
    except Exception as e:
        logger.exception('Error in get app %s', str(e))


async def apps(request):
    """
    Запросить инфу о приложениях из БД бота
    """
    logger.info(f"-- APPS {request}")
    try:
        app_name = request.rel_url.query.get('app_name', None)
        # Если параметр зоны ответственности не задан, вернем все дежурных
        logger.info(f"-- GET APP {app_name}")
        if app_name:
            app_info = get_app_info(app_name)
        else:
            # Отберём все приложения, по которым есть COM. Это должны быть 100% боевых приложений, за исключением мусора
            app_info = db().get_all_applications()
        return web.json_response(app_info)
    except Exception as e:
        logger.exception(f'Error in apps {str(e)}')


async def get_duty_external(request):
    """
    Запросить инфу о приложении из БД бота
    """
    try:
        area = request.match_info.get('area', None)
        # Если параметр зоны ответственности не задан, вернем все дежурных
        if not area:
            dutymen_array = await db().get_duty(get_duty_date(datetime.today()))
        else:
            dutymen_array = await db().get_duty_in_area(get_duty_date(datetime.today()), area)

        logger.info(f"-- GET DUTY EXTERNAL {request} {dutymen_array}")
        response = []
        if len(dutymen_array) > 0:
            for d in dutymen_array:
                response.append(d['account_name'])
        return web.json_response(response)
    except Exception as e:
        logger.exception('Error in get app external %s', str(e))


@initializeBot.dp.message_handler(filters.restricted, commands=['menu'])
async def call_main_menu(message: types.Message):
    try:
        await message.answer(text=emojize(messages.main_menu),
                                    reply_markup=keyboard.main_menu(tg_login=message.from_user.username),
                                    parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f'Error in call main menu {str(e)}')


@initializeBot.dp.message_handler(filters.restricted)
async def unknown_message(message: types.Message):
    """
    """
    logger.info('-- UNKNOWN MESSAGE start %s %s', message, message.chat)
    try:
        user_from_db = db().get_users('tg_login', message.from_user.username)

        if (message.chat.type == 'private'):
            if message.text == 'Главное меню':
                await message.reply(text=emojize(messages.main_menu),
                                    reply_markup=keyboard.main_menu(tg_login=message.from_user.username),
                                    parse_mode=ParseMode.HTML)
            elif message.text == 'Написать Linux-админам':
                await send_message_to_admsys()
            else:
                msg = f'Я не знаю, как ответить на {message.text} :astonished:\n Список того, что я умею - /help'
                if len(user_from_db) > 0:
                    msg = _make_message_polite(message=msg, user=user_from_db[0])
                # чтобы не спамил на реплаи в группах, а только в личку 
                logger.info('-- UNKNOWN MESSAGE HERE')
                await message.reply(emojize(msg), reply_markup=keyboard.reply_main_menu, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f'Error in unknown_message {str(e)}')


def get_app_info(app_name: str) -> dict:
    try:
        app_info = db().get_application_metainfo(app_name)
        if len(app_info) > 0:
            app_info['version'] = db().get_last_success_app_version(app_name)
        return app_info
    except Exception as e:
        logger.exception(f'Erorr in get app info {str(e)}')


def _app_name_regex(issue_summary: str) -> dict:
    """
    ('currency-storage+1.3.1')
    Распарсить имя компоненты и версию из summary джира-тикета
    Return {'name': 'currency-storage', 'version': '1.3.1'}
    """
    app = re.match('^([0-9a-z-]+)[+=]([0-9a-zA-Z-.]+)$', issue_summary.strip())
    output = {'name': app[1], 'version': app[2]} if app else {'name': issue_summary, 'version': False}
    return output


def _make_message_polite(message: str, user: dict) -> str:
    """
    Добавить к сообщению вежливое обращение к пользователю
    """
    male_appeals = ['Уважаемый', 'Досточтимый', 'Дорогой', 'Господин', 'Сэр']
    female_appeals = ['Уважаемая', 'Досточтимая', 'Дорогая']
    undefined_appeals = ['']
    if user['gender'] == 'Мужской':
        prefix = random.choice(male_appeals)
    elif user['gender'] == 'Женский':
        prefix = random.choice(female_appeals)
    else:
        prefix = random.choice(undefined_appeals)
    return prefix + f" {user['first_name']} {user['middle_name']}, \n" + message


async def get_current_user_subscription(account_name) -> str:
    """
    """
    user_subscriptions = await db().get_user_subscriptions(account_name)
    msg = ''
    for subs in user_subscriptions:
        if subs == 'release_events':
            msg += ' - Все события о релизах\n'
        elif subs == 'statistics':
            msg += ' - Статистика по релизам вечером\n'
        elif subs == 'timetable':
            msg += ' - Напоминание о встречах утром\n'
        elif subs == 'duties':
            msg += ' - Напоминание о своих <a href="https://wiki.yooteam.ru/display/admins/ReleaseBot.Assistant#ReleaseBot.Assistant-%D0%94%D0%B5%D0%B6%D1%83%D1%80%D1%81%D1%82%D0%B2%D0%B0">дежурствах</a> (только ДЭ и СБ)\n'
        elif subs == 'none':
            msg += ''
        else:
            msg += subs + '\n'
    return msg


async def on_startup(dispatcher):
    """
        Start up function
    """
    try:
        logger.info('- - - - Start bot - - - - -')

        scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
        scheduler.start()
    except Exception:
        logger.exception('on_startup')
        scheduler.shutdown()


async def on_shutdown(dispatcher):
    """
        Shutdown Bot
    """
    del dispatcher
    logger.info('Shutdown')


async def get_session():
    """
        Create aiohttp Client Session
    """
    session = aiohttp.ClientSession()
    return session


def start_webserver():
    app = web.Application()
    runner = web.AppRunner(app)
    app.add_routes([web.post('/send_message', send_message_to_users)])
    app.add_routes([web.post('/inform_duty', inform_duty)])
    app.add_routes([web.post('/inform_subscribers', inform_subscribers)])
    app.add_routes([web.post('/lock_apps', lock_apps)])
    app.add_routes([web.get('/get_app/{app_name}', get_app_external)])
    app.add_routes([web.get('/apps', apps)])
    app.add_routes([web.get('/get_duty/{area}', get_duty_external)])
    app.add_routes([web.get('/get_duty', get_duty_external)])
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, port=8100)
    loop.run_until_complete(site.start())

if __name__ == '__main__':

    keyboard.posts_cb = filters.callback_filter()
    keyboard.duty_cb = filters.duty_callback()
    # Disable insecure SSL Warnings
    warnings.filterwarnings('ignore')

    logger = logging.setup()
    start_webserver()
    executor.start_polling(initializeBot.dp, on_startup=on_startup, on_shutdown=on_shutdown)
