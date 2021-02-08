#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Telegram bot for employee of Yandex.Money
"""
import aiohttp
import config
import keyboard as keyboard
import asyncio
import json
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
from aiohttp import web
from enum import Enum
from utils.jiratools import JiraConnection, JiraTransitions, jira_get_approvers_list
from utils import logging, returnHelper, initializeBot, filters, couch_client
from utils.initializeBot import dp, bot
from utils.database import PostgresPool as db
from datetime import timedelta, datetime

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
    """
        Will show description all commands, handled by /help
        :param message: _ContextInstanceMixin__context_instance
    """
    logger.info('Marketing send was started')
    msg = emojize(f'Привет! :raised_hand:\n'
                  f'Я переехал на свою внутреннюю базу данных пользователей.\n'
                  f'Все телеграм-логины и id (есть и такая сущность), которые мне были известны, тоже переехали в неё.\n'
                  f'Если вы получили это сообщение -- у вас всё в порядке и уведомляния работают.\n'
                  f'Если кому-то из ваших коллег не приходят уведомления, отправьте им эту инструкцию:\n'
                  f'--------------------------\n'
                  f'1. Спросите у меня <b>/who "nickname" </b>,\n'
                  f'(вместо "nickname" можно подставить тг-логин, AD-логин или корпоративную почту).\n'
                  f'Если я вас узнаю, я верну сообщение с заполненными параметрами, среди которых должны быть заполнены:\n'
                  f'<b>Telegram Login</b> и <b>Telegram ID </b>:\n'
                  f'2. Если что-то среди этих параметров не заполнено, нажмите <b>/start</b> и затем спросите <b>/who ...</b> еще раз.\n'
                  f'3. Если это не помогло, зайдите, пожалуйста, в Диму Воробьёва -- @dvorob .\n'
                  f'--------------------------\n'
                  f'Хорошего дня!\n')
    #chats = await db().get_all_tg_id()
    logger.debug(chats)
    for chat_id in chats:
        try:
            #if chat_id["admin"] == 1:
            await initializeBot.bot.send_message(chat_id=chat_id["tg_id"], text=msg, parse_mode=ParseMode.HTML)
        except Exception as exc:
            logger.exception('Marketing sending error %s %s ', chat_id, str(exc))

@initializeBot.dp.message_handler(filters.restricted, commands=['help'])
async def help_description(message: types.Message):
    """
        Will show description all commands, handled by /help
        :param message: _ContextInstanceMixin__context_instance
    """
    logger.info('help function was called by %s', returnHelper.return_name(message))
    logger.info('Message %s', vars(message.from_user))
    logger.info('Message %s', vars(message.chat))
    msg = emojize(f'Привет, <b>{message.from_user.full_name}</b>! :raised_hand:\n'
                  f'\nЧтобы начать со мной взаимодействовать, нужно быть сотрудником компании.\n'
                  f'Если ты с нами, скорее всего, мы уже знакомы. Проверить это можно, спросив меня:\n'
                  f'<b>/who мой_никнейм</b> (вместо мой_никней можно указать логин в ТГ, корпоративную учетку или имя (полное) с фамилией).\n'
                  f'Если в ответе ты видишь корректный логин, всё Ок.\n'
                  f'Если Telegram ID не заполнен, нажми <u><b>/start</b></u> .\n'
                  f'Во всех остальных случаях обратись к администраторам группы Admsys.\n'
                  f'\nВот список всего, что я умею:\n'
                  f'<u>/start</u> -- запишет твой Telegram-ID в базу (нужно, чтобы отправлять тебе уведомления от бота).\n'
                  f'<u>/duty </u><b>N</b> -- покажет дежурных через N дней; N задавать необязательно, по умолчанию отобразятся деурные на сегодня.\n'
                  f'<u>/who </u><b>username</b> -- найдет инфо о пользователе; работает с ТГ-логином, аккаунтом или почтой.\n'
                  f'\nОписание кнопок:\n'
                  f'<u><b>Show duty admin</b></u> -- показать дежурных админов.\n'
                  f'<u><b>Open release board</b></u> -- открыть релизную доску Admsys.\n'
                  f'<u><b>Open documentation</b></u> -- открыть Wiki с документацией по боту.\n'
                  f'<u><b>Open logs page</b></u> -- открыть Kibana с логами бота.\n'
                  f'<u><b>Open admin menu</b></u> -- админское меню, доступно только администраторам.\n'
                  f'<u><b>Return task to the queue</b></u> -- вернет список Jira-тасок, которые можно вернуть в начало релизной очереди.\n'
                  f'<u><b>Subscribe to events</b></u> -- подписаться на все уведомления от бота.\n'
                  f'Там же можно и отписаться от уведомлений.\n'
                  f'<b>Важно:</b> на персональные уведомления (о своих релизах) подписывться не нужно -- они работают по умолчанию.\n'
                  f'<u><b>Get minimum information from release board</b></u> -- покажет статистику о текущем состоянии релизной доски.\n'
                  f'<u><b>Get extended information from release board</b></u> -- то же, но в расширенном варианте.\n')
    try:
        await message.answer(text=msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)
    except Exception as exc:
        logger.exception('Help sending error %s %s ', msg, str(exc))

@initializeBot.dp.message_handler(filters.restricted, commands=['start'])
async def start(message: types.Message):
    """
        Start function, handled by /start
        :param message: dict with information
        :type message: _ContextInstanceMixin__context_instance
    """
    try:
        logger.info('start function by %s', returnHelper.return_name(message))
        user_info = await db().search_users_by_account(message.from_user.username)
        if len(user_info)>0:
            for users in user_info:
                if users["tg_id"] != str(message.from_user.id):
                    await db().db_set_users(users['account_name'], full_name=None, tg_login=None, working_status=None, tg_id=str(message.from_user.id), notification=None, email=None)
                await message.reply(text=start_menu_message(message),
                                    reply_markup=keyboard.main_menu(),
                                    parse_mode=ParseMode.MARKDOWN_V2)
        else:
            not_familiar_msg = emojize(f'Здравствуй, {bold(message.from_user.full_name)}!\n'
                                       f'Я не нашел записи с твоим телеграмм-аккаунтом в своей базе. :confused:\n'
                                       f'Пожалуйста, обратись к системным администраторам группы admsys@\n'
                                       f'На всякий случай, подробнее обо мне можно прочесть здесь:\n'
                                       f'wiki.yamoney.ru/display/admins/CD_Bot.HowTo.User')
            await message.reply(text=not_familiar_msg)

    except Exception:
        logger.exception('start')
        not_familiar_msg = emojize(f'Здравствуй, {bold(message.from_user.full_name)}!\n'
                                   f'В ходе знакомства с тобой произошла ошибка. :confused:\n'
                                   f'Пожалуйста, обратись к системным администраторам группы admsys@')
        await message.reply(text=not_familiar_msg)

def start_menu_message(message) -> str:
    """
        Start menu message
        :return: str
    """
    return emojize(f'Hello, {bold(message.from_user.full_name)}! :raised_hand:\n'
                   f'Send /help if you want to read description of commands.\n'
                   f'Here :point_down: you can see the available buttons.\n')


def main_menu_message() -> str:
    """
        Main menu message
        :return: str
    """
    msg = emojize('Отправьте /help, чтобы узнать, что я умею.\n'
                  'Ниже :point_down: меню, но это далеко не всё.')
    return msg

@initializeBot.dp.message_handler(filters.restricted, commands=['write_my_chat_id'])
async def write_chat_id(message: types.Message):
    """
        {@tg_username: tg_chat_id}
        Using for private notifications
    """
    logger.info('write chat id started for : %s %s %s', message.from_user.username, message.from_user.id, message.chat.id)
    try:
        user_info = await db().search_users_by_account(str(message.from_user.username))
        if len(user_info) > 0:
            logger.info('write my chat id found user info %s', user_info)
            message.from_user.username: message.chat.id
            await db().db_set_users(user_info[0]['account_name'], full_name=None, tg_login=None, working_status=None, tg_id=str(message.chat.id), email=None)
            logger.info('wirhte my chat id done for %s %s', str(message.from_user.id), str(message.chat.id))
    except Exception:
        logger.exception('write chat id exception')

# /duty command from chatbot
@initializeBot.dp.message_handler(filters.restricted, commands=['duty'])
async def duty_admin(message: types.Message):
    """
        Информация о дежурных на дату (N, по умолчанию N = 0, т.е. на сегодня)
        Берется из xerxes.duty_list (таблица заполняется модулем Assistant, раз в час на основании календаря AdminsOnDuty)
    """
    try:
        logger.info('def duties admin started: %s', returnHelper.return_name(message))
        message.bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.typing)
        cli_args = message.text.split()
        # если в /duty передан аргумент в виде кол-ва дней отступа, либо /duty без аргументов
        after_days = int(cli_args[1]) if (len(cli_args) == 2 and int(cli_args[1]) > 0) else 0
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
        await message.answer(msg, reply_markup=to_main_menu(), parse_mode=ParseMode.MARKDOWN_V2)

        message.bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.typing)
    except Exception as e:
        logger.exception('error in duty admin %s', str(e))

# /timetable command from chatbot
@initializeBot.dp.message_handler(filters.restricted, commands=['timetable'])
async def timetable_personal(message: types.Message):
    """
    """
    try:
        logger.info('timetable personal: %s', message.from_user.username)

        start_date = datetime.today()
        end_date = datetime.today() + timedelta(1)
        user_from_db = await db().get_users('tg_id', query.message.chat.id)

        session = await get_session()
        async with session.get(config.api_get_timetable, headers=data) as resp:
            await resp.json()
        logger.info('get timetable personal from api: %s %s', resp.status, resp.json())

        await message.answer(resp.json(), reply_markup=to_main_menu(), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.exception('error in duty admin %s', str(e))

###############################################
async def create_duty_message(duty_date) -> str:
    dutymen_array = await db().get_duty(duty_date)
    if len(dutymen_array) > 0:
        msg = f"<b>Дежурят на {duty_date.strftime('%Y-%m-%d')}:</b>\n"
        for d in dutymen_array:
            d['tg_login'] = '@' + d['tg_login'] if len(d['tg_login']) > 0 else ''
            msg += f"\n· {d['full_text']} <b>{d['tg_login']}</b>"
        logger.debug('I find duty admin for date %s %s', duty_date.strftime('%Y-%m-%d %H %M'), msg)
    else:
        msg = f"Никого не нашлось в базе бота, посмотрите в календарь AdminsOnDuty \n"
    return msg


async def create_duty_message_personal(duty_date, tg_login) -> str:
    dutymen_array = await db().get_duty_personal(duty_date, tg_login)
    if len(dutymen_array) > 0:
        msg = f"Дежурства начиная с *{duty_date.strftime('%Y-%m-%d')}* для @{tg_login}:\n"

        for d in dutymen_array:
            msg += f"\n· {d['area']} - *{d['duty_date']}*"
        logger.info('I find duty admin for date %s %s', duty_date.strftime('%Y-%m-%d %H %M'), msg)
    else:
        msg = f"Никого не нашлось в базе бота, посмотрите в календарь AdminsOnDuty \n"
    return msg


def get_duty_date(date):
    # Если запрошены дежурные до 10 утра, то это "вчерашние дежурные"
    # Это особенность дежурств в Департаменте
    if int(datetime.today().strftime("%H")) < int(10):
        return date - timedelta(1)
    else:
        return date
   

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='get_ext_inf_board'), filters.restricted)
async def get_ext_inf_board_button(query: types.CallbackQuery, callback_data: str) -> str:
    """
        Get full information from Admsys release board
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    del callback_data
    try:
        logger.info('get_ext_inf_board_button started from: %s',
                    returnHelper.return_name(query))
        final_msg = ''
        await returnHelper.return_one_second(query)

        async def find_issue_and_add(jira_filter, header_tg_user) -> str:
            """
                Create msg with Jira task based on incoming filter
                :return: string with issues or empty str
            """
            issues = JiraConnection().jira_search(jira_filter)
            if len(issues) > 0:
                list_of_issues = []
                for issue in issues:
                    list_of_issues.append('%s: [%s](%s/browse/%s)' %
                                          (issue.key, issue.fields.summary,
                                           config.jira_host, issue.key))
                header_tg_user += '\n'.join(list_of_issues)
            else:
                header_tg_user = ''
            return header_tg_user

        test_dict = {config.search_issues_wait: '*Релизы в ожидании:*\n',
                     config.search_issues_work: '\n*Релизы в работе:*\n',
                     config.search_issues_work: '\n*Релизы в работе:*\n'
                     }
        for config_request, title in test_dict.items():
            if str_of_issues := await find_issue_and_add(config_request, title):
                final_msg += str_of_issues

        if len(final_msg) > 0:
            text = final_msg
        else:
            text = 'Я не смог найти тасок на релизной доске'
            logger.error('get_ext_inf_board_button, can\'t find issues in Jira')
        await query.message.answer(text=text, reply_markup=to_main_menu(),
                                   parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception('get_ext_inf_board')


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
                :return: msg for tg
            """
            issues_releases_progress = JiraConnection().jira_search(config.search_issues_work)

            issues_admsys = JiraConnection().jira_search(
                'project = ADMSYS AND issuetype = "Release (conf)" AND '
                'status IN (Open, "Waiting release") ORDER BY Rank ASC'
            )
            msg = f'\n - Releases in the progress: *{len(issues_releases_progress)}*'
            msg += f'\n - In AdmSYS queue: *{len(issues_admsys)}*'
            return msg

        information_from_jira = await count_issues()
        await query.message.answer(text=information_from_jira, reply_markup=to_main_menu(),
                                   parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception('get_min_inf_board_button')

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
            msg += f'<strong>Приветствую!</strong>\n' \
                  f'Сейчас <strong>{datetime.today().strftime("%H:%M")}</strong> утра.\n' \
                  f'Посмотреть, кто сегодня дежурит после 10:00 можно командой ' \
                  f'<strong>/duty 1</strong>.\n\n'

        msg += await create_duty_message(get_duty_date(datetime.today()))
        msg += '\n\nЕсли вы хотите узнать дежурных через N дней, отправьте команду /duty N\n\n'
        await query.message.answer(text=msg, reply_markup=to_main_menu(), parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('duty_button')


def to_main_menu() -> types.InlineKeyboardMarkup:
    """
        Return to main menu button
        :return: InlineKeyboardMarkup object
    """
    keyboard_main_menu = [[types.InlineKeyboardButton('Main menu',
                                                      callback_data=keyboard.posts_cb.new(action='main', issue='1'))]]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_main_menu)


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='main'), filters.restricted)
async def main_menu(query: types.CallbackQuery, callback_data: str):
    """
        Main menu
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    del callback_data
    try:
        logger.info('main_menu started')
        await query.message.answer(text=main_menu_message(),
                                   reply_markup=keyboard.main_menu(),
                                   parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception('main_menu_message')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='admin_menu'), filters.restricted, filters.admin)
async def admin_menu(query: types.CallbackQuery, callback_data: str):
    """
        Open admin menu
        :param query:
        :param callback_data
    """
    del callback_data
    try:
        logger.info('admin menu opened by %s', returnHelper.return_name(query))
        msg = f'Hi, admin!\nCurrent work mode: *{keyboard.current_mode()}*'
        await query.message.reply(text=msg, reply_markup=keyboard.admin_menu(),
                                  parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception('admin_menu')


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='restart'), filters.restricted, filters.admin)
async def restart(query: types.CallbackQuery, callback_data: str):
    """
        Restart pod with bot
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
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
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    del callback_data
    logger.warning('%s stopped bot', returnHelper.return_name(query))
    db().set_parameters('run_mode', 'off')
    await query.answer('Bot was stopped, Bye!')


@initializeBot.dp.message_handler(filters.restricted, filters.admin, commands=['lock', 'unlock'])
async def lock_app_release(message: types.Message):
    """
        Turn off bot
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    logger.info('lock app release started by %s %s', returnHelper.return_name(message), message.get_full_command())
    incoming = message.text.split()
    if len(incoming) == 2:
        if message.get_full_command()[0].find('lock') == 1:
            locked_app = {"lock": incoming[1], "unlock": ""}
        elif message.get_full_command()[0].find('unlock') == 1:
            locked_app = {"lock": "", "unlock": incoming[1]}

        logger.info('lock app release sent %s', locked_app)
        try:
            session = await get_session()
            async with session.post(config.api_lock_unlock, headers=locked_app) as resp:
                await resp.json()
                logger.info('lock send locked app to api, status is: %s', resp.status)
            get_app =  db().get_application_metainfo(incoming[1])
            logger.info('lock app release %s ', get_app)
            msg = f'lock app release {get_app}'
            await message.answer(text=msg)
        except Exception as exc:
            logger.exception('lock_unlock_task')
            return web.json_response({'status': 'error', 'message': str(exc)})

##############################################################################################
#              Кнопки админского меню
##############################################################################################

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='turn_on'), filters.restricted, filters.admin)
async def start_bot(query: types.CallbackQuery, callback_data: str):
    """
        Turn on bot
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    del callback_data
    logger.warning('%s started bot', returnHelper.return_name(query))
    db().set_parameters('run_mode', 'on')
    await query.answer('Bot was started, Go!')


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
    await query.answer('Ok, I won\'t touch new releases by myself.')

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='admin_menu'), filters.restricted, filters.admin)
async def admin_menu(query: types.CallbackQuery, callback_data: str):
    """
        Open admin menu
        :param query:
        :param callback_data
    """
    del callback_data
    try:
        logger.info('admin menu opened by %s', returnHelper.return_name(query))
        msg = f'Привет! \nМой текущий рабочий режим: *{keyboard.current_mode()}*'
        await query.message.reply(text=msg, reply_markup=keyboard.admin_menu(),
                                  parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception('admin_menu')

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='release_app_list'), filters.restricted, filters.admin)
async def release_app_list(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    #issue_key = callback_data['issue_key']
    logger.info('-- RELEASE APP LIST menu opened by %s %s', returnHelper.return_name(query), callback_data)
    msg = f'Релизы, которые я могу выкатить (находятся в статусе Waiting на доске):'
    await query.message.reply(text=msg, reply_markup=keyboard.release_app_list(), parse_mode=ParseMode.MARKDOWN_V2)

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='release_app'), filters.restricted, filters.admin)
async def release_app(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    logger.info('-- RELEASE APP started by %s %s', returnHelper.return_name(query), callback_data)
    msg = f"Точно выкатываем {callback_data['issue']} ?"
    await query.message.reply(text=msg, reply_markup=keyboard.release_app_confirm(callback_data['issue']), parse_mode=ParseMode.MARKDOWN_V2)

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
    await query.message.reply(text=msg, reply_markup=keyboard.rollback_app_list(), parse_mode=ParseMode.MARKDOWN_V2)

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='rollback_app'), filters.restricted, filters.admin)
async def rollback_app(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    #issue_key = callback_data['issue_key']
    logger.info('-- ROLLBACK APP started by %s %s', returnHelper.return_name(query), callback_data)
    msg = f"Точно откатываем {callback_data['issue']} ?"
    await query.message.reply(text=msg, reply_markup=keyboard.rollback_app_confirm(callback_data['issue']), parse_mode=ParseMode.MARKDOWN_V2)

@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='rollback_app_confirm'), filters.restricted, filters.admin)
async def rollback_app_confirm(query: types.CallbackQuery, callback_data: str):
    """
        Скормить релиз боту
    """
    #issue_key = callback_data['issue_key']
    logger.info('-- ROLLBACK APP CONFIRM started by %s %s', returnHelper.return_name(query), callback_data)
    try:
        JiraConnection().transition_issue_with_resolution(callback_data['issue'], JiraTransitions.FULL_RESOLVED.value, {'id': '10300'})
        JiraConnection().add_comment(callback_data['issue'], f"Откатывает некий {returnHelper.return_name(query)}")
    except Exception as e:
        logger.error('Error in ROLLBACK APP CONFIRM %s', e)
    await query.answer(f"Откатываю релиз {callback_data['issue']}. Потому что я красавчик.")

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
                                      parse_mode=ParseMode.MARKDOWN_V2)
        else:
            msg = 'Now there is **nothing** to return to the queue'
            await query.message.reply(text=msg,
                                      reply_markup=to_main_menu(),
                                      parse_mode=ParseMode.MARKDOWN_V2)
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

        msg = f'Вернул в очередь **{jira_issue_id}**. Попробую выкатить позже.'
        # Передвинем таску в начало доски и снимем её с бота
        jira_object = JiraConnection()
        jira_object.assign_issue(jira_issue_id, None)
        jira_object.transition_issue(jira_issue_id, JiraTransitions.FULL_WAIT.value)
        jira_object.add_comment(jira_issue_id, "Задача была возвращена в очередь одним из согласующих через телеграм.")

        await query.message.reply(text=msg, parse_mode=ParseMode.MARKDOWN_V2)
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
        msg = 'Вы можете подписаться на уведомления обо всех релизах.' \
              'Уведомления о ваших релизах будут работать в любом случае, от них отписаться нельзя.'
        await query.message.reply(text=msg, reply_markup=keyboard.subscribe_menu(),
                                  parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception("subscribe")


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='subscribe_all'), filters.restricted)
async def subscribe_all(query: types.CallbackQuery, callback_data: str):
    """
        Push 1 to some db table, you will subscribed
        :param callback_data: {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    try:
        del callback_data
        logger.info('Subscribe a %s chat %s ', query.message.chat.type, query.message.chat)
        if (query.message.chat.type == 'private'):
            user_from_db = await db().get_users('tg_id', query.message.chat.id)
            await db().db_set_users(user_from_db[0]['account_name'], full_name=None, tg_login=None, working_status=None, tg_id=None, notification='all', email=None)
        elif (query.message.chat.type == 'group'):
            await db().set_chats(query.message.chat.id, title=query.message.chat.title, started_by=query.message.from_user.username, notification='all')
        else:
            logger.info('Subscribe got something undefined %s', query.message.chat.id)
        msg = 'Вы подписаны на сообщения обо всех релизах.'
        await query.message.reply(text=msg, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception("subscribe_all")


@initializeBot.dp.callback_query_handler(keyboard.posts_cb.filter(action='unsubscribe_all'), filters.restricted)
async def unsubscribe_all(query: types.CallbackQuery, callback_data: str):
    """
    Отписать пользователя от всех уведомлений.
    {"action": value, "issue": value} (based on keyboard.posts_cb.filter)
    """
    try:
        del callback_data
        logger.info('-- UNSUBSCRIBE ALL %s chat %s ', query.message.chat.type, query.message.chat)
        if (query.message.chat.type == 'private'):
            user_from_db = await db().get_users('tg_id', query.message.chat.id)
            await db().db_set_users(user_from_db[0]['account_name'], full_name=None, tg_login=None, working_status=None, tg_id=None, notification='none', email=None)
        elif (query.message.chat.type == 'group'):
            await db().set_chats(query.message.chat.id, title=query.message.chat.title, started_by=query.message.from_user.username, notification='none')
        else:
            logger.info('Subscribe got something undefined %s', query.message.chat.id)
        msg = 'Вы отписались от сообщений о релизах.'
        await query.message.reply(text=msg, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.exception("Error in UNSUBSCRIBE ALL %s", e)


@initializeBot.dp.message_handler(filters.restricted, filters.admin, commands=['where_app'])
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
                    msg += f'\n Account name: <strong>{user["account_name"]}</strong>'
                    msg += f'\n Full name: <strong>{user["full_name"]}</strong>'
                    msg += f'\n Email: <strong>{user["email"]}</strong>'
                    msg += f'\n Telegram login: <strong>@{user["tg_login"]}</strong>'
                    msg += f'\n Telegram ID: <strong>{user["tg_id"]}</strong>'
                    msg += f'\n Is employee: <strong>{user["working_status"]}</strong>'
                    msg += f'\n Notification: <strong>{user["notification"]}</strong>\n'
            else:
                msg = 'Пользователей в моей базе не найдено'
        except Exception as e:
            logger.exception('Error GET USER INFO %s', e)
    else:
        msg = 'Пожалуйста, попробуйте еще раз: /who username'
    await message.answer(text=msg, parse_mode=ParseMode.HTML)

async def send_message_to_approvers(issue_key: str, message: str):
    """
       (issue_key='ADMSYS-10000', message='Алярма')
       Отправить сообщение согласующим. Согласующие - те, кто указаны в релизной таске, в виде рабочих аккаунтов.
       Функции нужно знать номер релиза и сообщение, дальше она сделает все сама. 
    """
    try:
        list_chat_id_recipients = jiratools.jira_get_approvers_list(issue_key)
        logger.info('-- SEND MESSAGE TO APPROVERS %s %s %s', issue_key, list_chat_id_recipients, message)
        send_message_to_users(list_chat_id_recipients, message)
    except Exception as e:
        logger.exception('Exception in SEND MESSAGE TO APPROVERS %s', e)

async def send_message_to_users(request):
    """
    # Внешняя ручка рассылки
    {'accounts': [list of account_names], 'jira_tasks': [list of tasks_id], 'text': str}
    """
    data_json = await request.json()
    logger.info('-- SEND MESSAGE TO USERS %s %s', data_json, type(data_json))
    disable_notification = False
    if 'accounts' in data_json:
        try:
            set_of_chat_id = []
            for acc in data_json['accounts']:
                user_from_db = await db().get_users('account_name', acc)
                if len(user_from_db) > 0:
                    if user_from_db[0]['tg_id'] != None:
                        set_of_chat_id.append(user_from_db[0]['tg_id'])
            if 'disable_notification' in data_json:
                disable_notification = True
            logger.info('sending message %s for %s', data_json['text'], set_of_chat_id)
            for chat_id in set_of_chat_id:
                try:
                    await bot.send_message(chat_id=chat_id, text=data_json['text'], disable_notification=disable_notification, parse_mode=ParseMode.MARKDOWN_V2)
                except BotBlocked:
                    logger.info('YM release bot was blocked by %s', chat_id)
                except ChatNotFound:
                    logger.error('Chat not found with: %s', chat_id)
        except Exception as e:
            logger.exception('Error send message to users %s', str(e))

    if 'jira_tasks' in data_json:
        for task in data_json['jira_tasks']:
            try:
                JiraConnection().add_comment(JiraConnection().jira_issue(task), data_json['text'])
            except Exception as e:
                logger.exception('Error send message to users when commenting jira task %s', str(e))

    return web.json_response()


async def inform_duty(request):
    """
    Внешняя ручка для информирования дежурных
    {'areas': ['ADMSYS(портал)', ...], 'message': str}
    areas - задаются в календаре AdminsOnDuty, перед именем дежурного
    """
    data_json = await request.json()
    logger.info('-- INFORM DUTY %s %s', data_json, type(data_json))
    if 'areas' in data_json:
        try:
            for area in data_json['areas']:
                await inform_today_duty(area, data_json['message'])
        except Exception as e:
            logger.exception('Error inform duty %s', e)
    return web.json_response()


async def inform_subscribers(request):
    """
    Внешняя ручка для информирования подписанных на информинги =)
    {'notification': 'all', 'message': str}
    notification можно найти в таблице Xerxes.Users в соответствующем поле
    """
    data_json = await request.json()
    logger.info('-- INFORM SUBSCRIBERS %s %s', data_json, type(data_json))
    if 'notification' in data_json:
        try:
            subscribers = await db().get_subscribers_to_something('all')
            for chat_id in subscribers:
                await bot.send_message(chat_id=chat_id, text=data_json['text'], disable_notification=True, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.exception('Error inform subscribers %s', e)
    return web.json_response()


async def inform_today_duty(area, msg):
    """
    Функция отправки сообщения сегодняшнему дежурному
    """
    dutymen_array = await db().get_duty_in_area(get_duty_date(datetime.today()), area)
    logger.info('-- INFORM TODAY DUTY %s %s', dutymen_array, msg)
    if len(dutymen_array) > 0:
        for d in dutymen_array:
            try:
                dutymen = await db().get_users('account_name', d['account_name'])
                logger.info('informing duty %s %s %s', dutymen[0]['tg_id'], dutymen[0]['tg_login'], msg)
                await bot.send_message(chat_id=279933948, text=msg, parse_mode=ParseMode.MARKDOWN_V2)
                await bot.send_message(chat_id=dutymen[0]['tg_id'], text=msg, parse_mode=ParseMode.MARKDOWN_V2)
            except BotBlocked:
                logger.info('YM release bot was blocked by %s', d['tg_login'])
            except ChatNotFound:
                logger.error('Chat not found with: %s', d['tg_login'])
            except Exception as e:
                logger.exception('Error in INFORM TODAY DUTY %s', e)  


@initializeBot.dp.message_handler()
async def unknown_message(message: types.Message):
    """
    """
    logger.info('-- UNKNOWN MESSAGE start')
    is_restricted = await filters.restricted(message)
    if is_restricted:
        msg = emojize(f'{bold(message.from_user.full_name)},\n'
                      f'Я не знаю, как ответить на {message.text} :astonished:\n'
                      'Список того, что я умею - /help')
        await message.reply(msg, parse_mode=ParseMode.MARKDOWN_V2)


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
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, port=8080)
    loop.run_until_complete(site.start())

if __name__ == '__main__':

    keyboard.posts_cb = filters.callback_filter()
    # Disable insecure SSL Warnings
    warnings.filterwarnings('ignore')

    logger = logging.setup()
    start_webserver()
    executor.start_polling(initializeBot.dp, on_startup=on_startup, on_shutdown=on_shutdown)