#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Telegram bot for employee of Yandex.Money
"""
import app.config as config
import json
import requests
import sys
import warnings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Dispatcher
from aiogram import executor, types
from aiogram.types import ParseMode, ChatActions, Update, ContentType
from aiogram.utils.markdown import bold
from aiogram.utils.emoji import emojize
from aiohttp import web
from app.exchanges.duty import ExchangeConnect
from app.jiraissues.base import JiraIssues
from app.keyboard import base as keyboard
from app.utils import ioAerospike as Spike
from app.utils import logging, returnHelper, initializeBot, staff
from app.utils import customFilters as Filters
from app.utils.ioMysql import MysqlPool as mysql
from app.update_of_releases.base import start_update_releases, todo_tasks
from datetime import timedelta, datetime
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

dp, bot = initializeBot.initialization()
posts_cb = Filters.callback_filter()


@dp.errors_handler()
async def errors_handler(update: Update, exception: Exception):
    """
        Errors handler
        :param update:
        :param exception:
        :return:
    """
    try:
        raise exception
    except Exception as e:
        logger.exception("Cause exception {e} in update {update}", e=e, update=update)
    return True


async def help_description(message: types.Message):
    """
        Will show description all commands, handled by /help
        :param message: _ContextInstanceMixin__context_instance
    """
    logger.info('help function by %s', returnHelper.return_name(message))
    msg = emojize(f'Hello, <b>{message.from_user.full_name}</b> :raised_hand:!\n'
                  f'Here :point_down: you can read description of all my commands.\n'
                  f'\nDescription of commands via <strong>/</strong>\n'
                  f'/start: Start working with bot\n'
                  f'/duty N: Will show duty admins after N days\n'
                  f'/who <strong>username</strong>: Will find information about user; works with tg_login or AD_accountname '
                  f'this employee on staff.yandex-team.ru\n'
                  f'/write_my_chat_id: Will write your telegram chat_id to bot database '
                  f'(using for private notifications). Should be used only '
                  f'in case of problems with private notifications. '
                  f'By default, you don\'t need it.\n'
                  f'\nDescription of buttons:\n'
                  f'<u><b>Show duty admin</b></u>: Will show now duty admins\n'
                  f'<u><b>Open release board</b></u>: Will open Admsys release board\n'
                  f'<u><b>Open documentation</b></u>: Will open Wiki page with documentation '
                  f'of bot\n'
                  f'<u><b>Open logs page</b></u>: Will open Kibana page with bot logs\n'
                  f'<u><b>Open admin menu</b></u>: Extended commands, only for some sysops\n'
                  f'<u><b>Return task to the queue</b></u>: Will show you which Jira task '
                  f'can be returned to the queue now\n'
                  f'<u><b>Subscribe to events</b></u>: Here you can subscribe to all'
                  f' notifications about all releases from bot or unsubscribe at all.\n'
                  f'<u><b>Get minimum information from release board</b></u>: Will show '
                  f'some like this:\n'
                  f'<code>- Releases in the progress: 1\n'
                  f'- In AdmSYS queue: 5\n</code>'
                  f'<u><b>Get extended information from release board</b></u>: Will show '
                  f'previous message in extended mode, example:\n')
    await message.reply(text=msg, reply_markup=to_main_menu(),
                        parse_mode=ParseMode.HTML)


async def start(message: types.Message):
    """
        Start function, handled by /start
        :param message: dict with information
        :type message: _ContextInstanceMixin__context_instance
    """
    try:
        logger.info('start function by %s', returnHelper.return_name(message))
        tg_username = f'@{message.from_user.username}'
        if Spike.read(item=tg_username, aerospike_set='informer'):
            # user already exist in aerospike, we don't need some additional actions
            await message.reply(text=start_menu_message(message),
                                reply_markup=keyboard.main_menu(),
                                parse_mode=ParseMode.MARKDOWN)
        else:
            not_familiar_msg = emojize(f'Hello, {bold(message.from_user.full_name)}! '
                                       f':raised_hand:\n'
                                       f'It\'s look like we are not familiar with you yet '
                                       f':confused:\n'
                                       f'Give me :hourglass_flowing_sand: for gathering all '
                                       f'needed information '
                                       f'for further succeeding work.\n'
                                       f'Here is my '
                                       f'[documentation](https://wiki.yamoney.ru/x/03AAD), '
                                       f'please read.')
            await message.reply(text=not_familiar_msg, parse_mode=ParseMode.MARKDOWN)
            # user doesn't exist in aerospike, we need to get information about him for further work
            # Write {@username: chat_id} to @username item in informer set
            # It's necessary for private notifications
            bins = {tg_username: message.chat.id}
            Spike.write(item=tg_username, bins=bins, aerospike_set='informer')

            msg = f'I\'ve received request from {message.from_user.full_name} ' \
                  f'tg_chat_id: {message.chat.id}'

            info_from_staff_str, info_from_staff_json = \
                staff.find_data_by_tg_username(message.from_user.username)
            logger.info('info_from_staff_str: %s\n info_from_staff_json: %s',
                        info_from_staff_str, info_from_staff_json)
            if len(info_from_staff_json) != 0:
                for info in info_from_staff_json:
                    mail_str = ''.join(info['emails'])
                    tg_user_str = ''.join(info['telegrams'])
                # Add record to aerospike, for further private notifications
                Spike.write(item=mail_str, aerospike_set='staff',
                            bins={tg_user_str: '1'})
                logger.info('I\'ve recorded to aerospike_set "staff" item: %s '
                            'with value: {%s: str(1)}',
                            mail_str, tg_user_str)
                logger.debug('info_from_staff: %s', info_from_staff_str)
                for record in info_from_staff_str:
                    msg += f'\n{record}'
                hello_msg = 'Thanks for waiting, let\'s go!\n'
                await message.answer(text=hello_msg + main_menu_message(),
                                     reply_markup=keyboard.main_menu(),
                                     parse_mode=ParseMode.MARKDOWN)

                for admin in config.bot_master.values():
                    await message.bot.send_message(chat_id=admin, text=msg,
                                                   parse_mode=ParseMode.HTML)
            else:
                main_msg = ''.join(info_from_staff_str)
                logger.warning('Error occur when try find info for @%s on a staff',
                               message.from_user.username)
                emojize_msg = emojize('Nothing found on the staff :white_frowning_face:\n ')
                await message.answer(text=main_msg + emojize_msg,
                                     parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception('start')


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
    msg = emojize('Send /help if you want to read description all of my commands.\n'
                  'Here :point_down: you can see what I can')
    return msg


async def write_my_chat_id(message: types.Message):
    """
        Will write to aerospike set 'informer' to item @tg_username
        {@tg_username: tg_chat_id}
        Using for private notifications
    """
    try:
        logger.info('write_my_chat_id started from: %s', returnHelper.return_name(message))
        logger.info('write_my_chat_id: %s %s %s', message.from_user.username, message.from_user.id, message.chat.id)
        headers = {'tg_login': str(message.from_user.username), 'tg_user_id': str(message.from_user.id), 'tg_chat_id': str(message.chat.id)}
        req_tg = requests.post(config.api_sign_up, headers=headers)
        logger.info('write_my_chat_id response %s', req_tg)
        bins = {'@' + message.from_user.username: message.chat.id}
        Spike.write(item='@' + message.from_user.username,
                    bins=bins, aerospike_set='informer')
        msg = emojize('Ok, done. :ok_hand:')
    except Exception:
        logger.exception('exception in write_my_chat_id')

async def duty_admin(message: types.Message):
    """
        Info about current or future duty admin
        Description:
        /duty N - go to exchange, receives info about duty admin after N days.
        /duty - go to aerospike for info (it does by assistant at 10 a.m.)
        If current time between 00.00 and 10.00, got to the exchange
        and will write explanatory message.
        :param message:
    """
    try:
        logger.info('duty_admin started: %s', returnHelper.return_name(message))
        message.bot.send_chat_action(chat_id=message.chat.id,
                                     action=ChatActions.typing)
        cli_args = message.text.split()
        logger.debug('duty, in_text = %s', cli_args)
        # если в /duty передан аргумент в виде кол-ва дней отступа, либо /duty без аргументов но вызван до 10 часов утра
        if (len(cli_args) == 2 and int(cli_args[1]) > 0):
            now = ExchangeConnect().timezone()
            dict_duty_adm = Spike.read(item='duty', aerospike_set='duty_admin')
            if len(cli_args) == 1:
                msg = returnHelper.return_early_duty_msg(datetime.today().strftime("%H:%M"))
                cal_start = now + timedelta(minutes=0)
                cal_end = now + timedelta(minutes=1)
            else:
                msg = 'Дежурят через <strong>%s</strong> дней:\n\n' % cli_args[1]
                delta = int(cli_args[1]) * 24 * 60
                logger.debug('len ==2, delta = %s', delta)
                cal_start = now + timedelta(minutes=delta)
                cal_end = now + timedelta(minutes=delta + 1)
            msg += ExchangeConnect().find_duty_exchange(cal_start, cal_end)
        else:
            dict_duty_adm = Spike.read(item='duty', aerospike_set='duty_admin')
            today = datetime.today().strftime("%Y-%m-%d")
            # Если запрошены дежурные до 10 утра, то это "вчерашние дежурные"
            if int(datetime.today().strftime("%H")) < int(10):
                today = (datetime.today() - timedelta(1)).strftime("%Y-%m-%d")
            else:
                today = datetime.today().strftime("%Y-%m-%d")
            logger.debug('dict_duty_adm = %s', dict_duty_adm)

            if today in dict_duty_adm.keys():
                msg = dict_duty_adm[today]
                logger.info('I find duty_admin for date %s %s', today, msg)
            else:
                logger.error('Today is %s and i did\'t find info in aerospike '
                             'look at assistant pod logs', today)
        await message.answer(msg, reply_markup=to_main_menu(),
                             parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('h_duty-tg_send')


def duty_admin_now() -> str:
    """
        Information about current duty administrators
        :return: msg with today duty admin
    """
    try:
        logger.info('duty_admin_now started')
        dict_duty_adm = Spike.read(item='duty', aerospike_set='duty_admin')
        today = datetime.today().strftime("%Y-%m-%d")

        logger.debug('dict_duty_adm, today = %s\n%s', dict_duty_adm, today)

        if today in dict_duty_adm.keys():
            msg = dict_duty_adm[today]
            logger.info('I find info about duty_admin in aerospike, without '
                        'using exchange!')
        else:
            msg = 'Error'
            logger.error('Today is %s and i did\'t find info in aerospike '
                         'look at assistant pod logs', today)
        return msg
    except Exception:
        logger.exception(duty_admin_now)


@dp.callback_query_handler(posts_cb.filter(action='get_ext_inf_board'), Filters.restricted)
async def get_ext_inf_board_button(query: types.CallbackQuery, callback_data: str) -> str:
    """
        Get full information from Admsys release board
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
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
            issues = JiraIssues().jira_search(jira_filter)
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
                                   parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception('get_ext_inf_board')


@dp.callback_query_handler(posts_cb.filter(action='get_min_inf_board'), Filters.restricted)
async def get_min_inf_board_button(query: types.CallbackQuery, callback_data: str) -> str:
    """
        Create msg with releases in the progress and in the Admsys queue
    """
    del callback_data
    try:
        logger.info('get_min_inf started from: %s', returnHelper.return_name(query))
        await returnHelper.return_one_second(query)

        async def count_issues() -> str:
            """
                Request to Jira and format msg
                :return: msg for tg
            """
            issues_releases_progress = JiraIssues().jira_search(config.search_issues_work)

            issues_admsys = JiraIssues().jira_search(
                'project = ADMSYS AND issuetype = "Release (conf)" AND '
                'status IN (Open, "Waiting release") ORDER BY Rank ASC'
            )
            msg = f'\n - Releases in the progress: *{len(issues_releases_progress)}*'
            msg += f'\n - In AdmSYS queue: *{len(issues_admsys)}*'
            return msg

        information_from_jira = await count_issues()
        await query.message.answer(text=information_from_jira, reply_markup=to_main_menu(),
                                   parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception('get_min_inf_board_button')

@dp.callback_query_handler(posts_cb.filter(action='duty_button'), Filters.restricted)
async def duty_button(query: types.CallbackQuery, callback_data: str):
    """
        Button with duty admin now
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    del callback_data
    try:
        logger.info('duty_button started from: %s', returnHelper.return_name(query))
        logger.debug('duty, query: %s', query)
        extra_msg = '\n\nЕсли вы хотите узнать дежурных через N дней,\n' \
                    'отправьте команду /duty N'
        msg = returnHelper.return_early_duty_msg(datetime.today().strftime("%H:%M")) \
            if int(datetime.today().strftime("%H")) < int(10) \
            else duty_admin_now() + extra_msg
        await query.message.answer(text=msg, reply_markup=to_main_menu(),
                                   parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception('duty_button')


def to_main_menu() -> types.InlineKeyboardMarkup:
    """
        Return to main menu button
        :return: InlineKeyboardMarkup object
    """
    keyboard_main_menu = [[types.InlineKeyboardButton('Main menu',
                                                      callback_data=posts_cb.new(action='main',
                                                                                 issue='1'))]]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_main_menu)


@dp.callback_query_handler(posts_cb.filter(action='main'), Filters.restricted)
async def main_menu(query: types.CallbackQuery, callback_data: str):
    """
        Main menu
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    del callback_data
    try:
        logger.info('main_menu started')
        await query.message.answer(text=main_menu_message(),
                                   reply_markup=keyboard.main_menu(),
                                   parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception('main_menu_message')


@dp.callback_query_handler(posts_cb.filter(action='admin_menu'),
                           Filters.restricted, Filters.admin)
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
                                  parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception('admin_menu')


@dp.callback_query_handler(posts_cb.filter(action='restart'),
                           Filters.restricted, Filters.admin)
async def restart(query: types.CallbackQuery, callback_data: str):
    """
        Restart pod with bot
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    try:
        del callback_data
        await returnHelper.return_one_second(query)
        dp.stop_polling()
        logger.warning('Bot was restarted... by %s', returnHelper.return_name(query))
        sys.exit(1)
    except Exception:
        logger.exception('restart')

@dp.callback_query_handler(posts_cb.filter(action='turn_off'),
                           Filters.restricted, Filters.admin)
async def stop_bot(query: types.CallbackQuery, callback_data: str):
    """
        Turn off bot
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    del callback_data
    logger.warning('%s stopped bot', returnHelper.return_name(query))
    bins = {'run': 0}
    Spike.write(item='deploy', bins=bins, aerospike_set='remaster')
    await query.answer('Bot was stopped, Bye!')


@dp.callback_query_handler(posts_cb.filter(action='turn_on'),
                           Filters.restricted, Filters.admin)
async def start_bot(query: types.CallbackQuery, callback_data: str):
    """
        Turn on bot
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    del callback_data
    logger.warning('%s started bot', returnHelper.return_name(query))
    bins = {'run': 2}
    Spike.write(item='deploy', bins=bins, aerospike_set='remaster')
    await query.answer('Bot was started, Go!')


@dp.callback_query_handler(posts_cb.filter(action='dont_touch'),
                           Filters.restricted, Filters.admin)
async def dont_touch_releases(query: types.CallbackQuery, callback_data: str):
    """
        Don't touch releases on Jira board
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    del callback_data
    logger.warning('%s pressed button Don\'t touch new release',
                   returnHelper.return_name(query))
    bins = {'run': 1}
    Spike.write(item='deploy', bins=bins, aerospike_set='remaster')
    await query.answer('Ok, I won\'t touch new releases by myself.')


@dp.callback_query_handler(posts_cb.filter(action='return_queue'),
                           Filters.restricted)
async def return_to_queue(query: types.CallbackQuery, callback_data: str):
    """
        Create menu with Jira task which can be returned or will write msg
        "Now there is nothing to return to the queue"
    """
    del callback_data
    try:
        await returnHelper.return_one_second(query)
        if waiting_assignee_issues := JiraIssues().jira_search(config.waiting_assignee_releases):
            msg = 'This is Jira task, which may be returned to the queue'
            markup = keyboard.return_queue_menu(waiting_assignee_issues)
            await query.message.reply(text=msg,
                                      reply_markup=markup,
                                      parse_mode=ParseMode.MARKDOWN)
        else:
            msg = 'Now there is **nothing** to return to the queue'
            await query.message.reply(text=msg,
                                      reply_markup=to_main_menu(),
                                      parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception('return_to_queue')


@dp.callback_query_handler(posts_cb.filter(action='return_release'),
                           Filters.restricted)
async def process_return_queue_callback(query: types.CallbackQuery, callback_data: str):
    """
        Based on callback_data["issue"] (received from keyboard.return_queue_menu)
        will know a = [tg chat_id] of assignee this Jira task. If employee clicking the button
        with this Jira task inside a:
        will stop the Jenkins job, del assignee from task, return to the queue, write msg.
        Else, will write "You are not in assignee list"
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    try:
        await returnHelper.return_one_second(query)
        jira_issue_id = callback_data['issue']
        # Get chat_id of recipients this jira task
        request_api_v1 = requests.get(f'{config.api_chat_id}/{jira_issue_id}')
        chat_id_recipients = request_api_v1.json()
        logger.info('chat_id_recipients: %s', chat_id_recipients)

        if str(query.message.chat.id) in chat_id_recipients:
            msg = f'Returned back to the queue  **{jira_issue_id}**, ' \
                  'come back when you are ready.'
            # delete assignee from task
            jira_object = JiraIssues()
            jira_object.assign_issue(jira_issue_id, None)
            # 321 - transition identifier from looking_for_assignee
            # to waiting_release_master
            jira_object.transition_issue(jira_issue_id, '321')
            jira_object.add_comment(jira_issue_id, "Задача была возвращена "
                                                   "в очередь одним из согласующих "
                                                   "через телеграм.")
            msg_who_returned = f'{returnHelper.return_name(query)} ' \
                               f'returned {jira_issue_id} ' \
                               f'to the queue a second ago'
            logger.info(msg_who_returned)

            # jenkins stop task
            all_return_queue_task = Spike.read(item='return_to_queue',
                                               aerospike_set='jenkins_args')
            jenkins_args_for_stop = all_return_queue_task[jira_issue_id]
            logger.info('jenkins_args_for_stop: %s', all_return_queue_task[jira_issue_id])
            url_jenkins_stop_job = f'{config.jenkins}/stop/job'
            r = requests.post(url_jenkins_stop_job, json=jenkins_args_for_stop)
            logger.info('jenkins remote response: %s', r.json())
        else:
            msg = 'You are not in assignee list.\n'
            err_msg = f'{returnHelper.return_name(query)} + ' \
                      f'tried return to queue {jira_issue_id} ' \
                      f'but smth went wrong'
            logger.error(err_msg)
        await query.message.reply(text=msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception('process_return_queue_callback')

@dp.callback_query_handler(posts_cb.filter(action='subscribe'),
                           Filters.restricted)
async def subscribe_events(query: types.CallbackQuery, callback_data: str):
    """
        Subscribe to events

        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    del callback_data
    try:
        logger.info('subscribe_events opened by %s', returnHelper.return_name(query))
        msg = 'Here you can `subscribe to all` notification about all releases from bot' \
              ' or `unsubscribe at all` - in this case, you will receive ' \
              'notifications *only related to you.*'
        await query.message.reply(text=msg, reply_markup=keyboard.subscribe_menu(),
                                  parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception("subscribe")

@dp.callback_query_handler(posts_cb.filter(action='subscribe_all'),
                           Filters.restricted)
async def subscribe_all(query: types.CallbackQuery, callback_data: str):
    """
        Push 1 to some db table, you will subscribed
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    try:
        del callback_data
        mysql().db_subscribe(query.message.chat.id, query.message.chat.type, 1)
        logger.info('%s have subscribed to the releases', returnHelper.return_name(query))
        msg = 'You have subscribed to the releases.'
        await query.message.reply(text=msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception("subscribe_all")


@dp.callback_query_handler(posts_cb.filter(action='unsubscribe_all'),
                           Filters.restricted)
async def unsubscribe_all(query: types.CallbackQuery, callback_data: str):
    """
        Push 0 to some db table, you will unsubscribed
        :param query:
        :param callback_data: {"action": value, "issue": value} (based on posts_cb.filter)
    """
    try:
        del callback_data
        mysql().db_subscribe(query.message.chat.id, query.message.chat.type, 0)
        logger.info('%s have unsubscribed to the releases', returnHelper.return_name(query))
        msg = 'You have unsubscribed to the releases.'
        await query.message.reply(text=msg, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception("unsubscribe_all")


# Ручки поиска по БД. Светят наружу в API
# Выдать информацию по пользователю из таблицы xerxes.users
async def get_user_info(message: types.Message):
    logger.info('get_user_info started by %s', returnHelper.return_name(message))
    incoming = message.text.split()
    if len(incoming) == 2:
        try:
            user_info = await get_username_from_db(incoming[1])
            logger.info('get user info found %s', user_info)
            if len(user_info) > 0:
                msg = 'Found the User:'
                msg += f'\n Account name: <strong>{user_info[0]["account_name"]}</strong>'
                msg += f'\n Full name: <strong>{user_info[0]["full_name"]}</strong>'
                msg += f'\n Email: <strong>{user_info[0]["email"]}</strong>'
                msg += f'\n Telegram login: <strong>{user_info[0]["tg_login"]}</strong>'
                msg += f'\n Telegram ID: <strong>{user_info[0]["tg_id"]}</strong>'
                msg += f'\n Working status: <strong>{user_info[0]["working_status"]}</strong>'
                msg += f'\n Notification: <strong>{user_info[0]["notification"]}</strong>'
            else:
               msg = 'Didn\'t find any users'
        except Exception:
            logger.exception('exception in get user info')
    else:
        msg = 'Please, try again, example: /who username'
    await message.answer(text=msg, parse_mode=ParseMode.HTML)

# Вытащить пользователя из БД. Задается юзернейм, поиск ведется по полям account_name и tg_name
async def get_username_from_db(username):
    # Получили username, который может быть логином в AD или в ТГ. Проверим по обоим полям, запишем непустые объекты в массив 
    # Вернем первого члена массива (если в БД всплывут дубли, например, где у одного tg_login = account_name другого, надо что-то придумать)
    logger.info('Mysql: trying to get users from Users table')
    users_array = []
    user_from_db = mysql().db_get_users('account_name', username)
    users_array.append(user_from_db) if len(user_from_db) > 0 else logger.info('Nothing found in Users for %s as account_name', username)

    user_from_db = mysql().db_get_users('tg_login', username)
    users_array.append(user_from_db) if len(user_from_db) > 0 else logger.info('Nothing found in Users for %s as tg_login', username)
    if len(users_array) > 0:
        users_array = users_array[0]
    else:
        users_array = []
    return(users_array)

async def send_to_users(request):
    """
        {'chat_id': [list of chat_id], 'text': msg}
    """
    try:
        data_json = await json.loads(request.text())
        logger.info('send to user caught message : %s', data_json)
        parse_mode_in_json = data_json.get('type', None)
        parse_mode = telegram.ParseMode.MARKDOWN if not parse_mode_in_json else telegram.ParseMode.HTML
        set_of_chat_id = set(data_json.get('chat_id'))
        for chat_id in set_of_chat_id:
            try:
                bot.send_message(chat_id=chat_id, text=data_json['text'],
                                 parse_mode=parse_mode)
            except telegram.error.Unauthorized:
                blocked_by_whom = find_username_by_chat_id(chat_id)
                logger.error('Bot was blocked by: %s', blocked_by_whom)
                bot.send_message(chat_id=279933948,
                                 text=f'*Xerxes was blocked by {blocked_by_whom}*',
                                 parse_mode=telegram.ParseMode.MARKDOWN)

        return web.json_response()
    except Exception:
        logger.exception('tg_send')

async def unknown_message(message: types.Message):
    """
        If a employee tries to send smth, that unregistered in dispatcher, answer him.
        :param message:
    """
    msg = emojize(f'{bold(message.from_user.full_name)}, are you sure?\n'
                  f'I don\'t know what to do with {message.text} :astonished:\n'
                  'Try send /help')
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)


def setup_handlers(disp: Dispatcher):
    """
        Setup handlers for bot
        :param disp:
    """
    disp.register_message_handler(start, Filters.restricted, commands='start')
    disp.register_message_handler(help_description, Filters.restricted, commands='help')
    disp.register_message_handler(duty_admin, Filters.restricted, commands='duty')
    disp.register_message_handler(get_user_info, Filters.restricted, commands='who')
    disp.register_message_handler(write_my_chat_id, Filters.restricted, commands='write_my_chat_id')
    disp.register_message_handler(unknown_message, Filters.restricted, content_types=ContentType.ANY)


async def on_startup(dispatcher):
    """
        Start up function
        :param dispatcher:
    """
    try:
        logger.info('Startup bot, hello!')
        setup_handlers(dispatcher)
        scheduler = AsyncIOScheduler(timezone=config.tz_name)
        scheduler.add_job(start_update_releases, 'cron', day='*',
                          hour='*', minute='*', second='30')
        scheduler.add_job(todo_tasks, 'cron', day='*',
                          hour='*', minute='*', second='20')
        scheduler.start()
    except Exception:
        logger.exception('on_startup')
        scheduler.shutdown()


async def on_shutdown(dispatcher):
    """
        Shutdown Bot
        :param dispatcher:
    """
    del dispatcher
    logger.info('Shutdown')

if __name__ == '__main__':

    # Disable insecure SSL Warnings
    warnings.filterwarnings('ignore')
    logger = logging.setup()

    BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)

    app = web.Application()

    app.add_routes([
        web.post('/send', send_to_users)
    ])

    web.run_app(app, port=8080)