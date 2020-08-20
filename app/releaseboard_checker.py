#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realize jira methods
"""
import re
import requests
from aiogram.types import ParseMode
from aiogram.utils.exceptions import ChatNotFound, BotBlocked
from app import config
from app.utils.ioMysql import MysqlPool as mysql
from app.jiratools import JiraTools
from app.utils import logging, initializeBot
from app.utils import aero
from app.utils.initializeBot import dp, bot

logger = logging.setup()

async def todo_tasks():
    """
        Function for notification in case changing releases status.
        Looks at all waiting assignee tasks.
    """
    logger.debug('todo_tasks started')
    try:
        db_result_todo = mysql().db_get_option('rl_todo')
        todo_db = db_result_todo.split() if isinstance(db_result_todo, str) else []
        logger.info('DB Releases (in mysql): %s', todo_db)

        issues_todo = JiraTools().jira_search(config.waiting_assignee_releases)
        logger.info('Jira releases in todo: %s', issues_todo)

        todo_id = []
        for issue in issues_todo:
            logger.info('Working with issue: %s', issue)
            todo_id.append(issue.id)

            if issue.id not in todo_db:
                for chatId_subscribed in mysql().db_get_rl():
                    msg_in_queue = f'[{issue.fields.summary}]' \
                                   f'(https://jira.yamoney.ru/browse/{issue.key}) ' \
                                   f'ищет согласующих.'
                    await bot.send_message(chat_id=chatId_subscribed,
                                           text=msg_in_queue + how_many_is_working(),
                                           parse_mode=ParseMode.MARKDOWN)

                # Personal notification
                logger.info('Trying to personal notification for issue: %s', issue.key)
                try:
                    request_chatid_api_v1 = requests.get(f'{config.api_chat_id}/{issue.key}')
                    recipient_chat_id = list(request_chatid_api_v1.json())
                except Exception:
                    logger.exception('Personal Jesus fail')
                logger.info('recipient_chatid: %s', request_chatid_api_v1.json())

                jira_link = 'https://jira.yamoney.ru/browse/'
                text_waiting = f'[{issue.fields.summary}]({jira_link}{issue.key}) ' \
                               f'с нетерпением ждет твоего согласования.\n' \
                               'Если вы не можете катить релиз сейчас, ' \
                               'воспользуйтесь кнопкой `Return task to the queue`'
                # Especially for case, when someone block or not added to bot..
                for chat_id in set(recipient_chat_id):
                    try:
                        await bot.send_message(chat_id=chat_id, text=text_waiting,
                                               parse_mode=ParseMode.MARKDOWN)
                    except BotBlocked:
                        logger.info('YM release bot was blocked by %s', chat_id)
                        await bot.send_message(chat_id=279933948, text=f'*YMReleaseBot '
                                                                       f'was blocked by {chat_id}*')
                    except ChatNotFound:
                        logger.error('Chat not found with: %s', chat_id)
                        await bot.send_message(chat_id=279933948, text=f'*YMReleaseBot '
                                                                       f'chat not found {chat_id}*')

                logger.info('%s - sent notification looking forward (via api-v1) to: %s',
                            issue.key, set(recipient_chat_id))
            
            # Save data to db
            mysql().db_set_option('rl_todo', ' '.join(todo_id))

    except Exception:
        logger.exception('todo_task')


def how_many_is_working() -> str:
    """
        Count how many releases is working now and how many in total
        :return: msg
    """
    issues_releases = JiraTools().jira_search(config.issues_not_closed_resolved)
    issues_working_now = JiraTools().jira_search(config.search_issues_work)
    return f'\n> в работе: {len(issues_working_now)} из {len(issues_releases)}'


async def start_update_releases():
    """
        Function for notification in case changing releases status.
        Informs about all entered the queue tasks and
    """
    logger.debug('start_update_releases started')

    def helper_func(option_name, jira_filter, action_of_task):
        """

            :param option_name:
            :param jira_filter
            :param action_of_task
            :return:
        """
        msg_sending = ''
        try:
            logger.debug('helper is start_update_releases for %s started', option_name)
            db_result = mysql().db_get_option(option_name)
            logger.debug('db_result_waiting %s', db_result)
            list_tasks_in_db = db_result.split() if isinstance(db_result, str) else []
            jira_tasks = JiraTools().jira_search(jira_filter)
            logger.debug('Jira issues in helper_func %s', jira_tasks)
            return_list_id = []

            for issues in jira_tasks:
                if issues.id not in list_tasks_in_db:
                    msg_sending = f'[{issues.fields.summary}]' \
                                  f'(https://jira.yamoney.ru/browse/{issues.key}) ' \
                                  f'{action_of_task}.'

                return_list_id.append(issues.id)

            logger.debug('List of jira id to DB %s', return_list_id)
            # Save data to db
            mysql().db_set_option(option_name, ' '.join(return_list_id))
            if len(msg_sending) == 0:
                msg_sending = 'No message'
            return return_list_id, list_tasks_in_db, msg_sending
        except Exception:
            logger.exception('helper_func start_update_releases')

    try:
        waiting_id, waiting_db, msg_queed = helper_func(
            'rl_waiting', config.issues_waiting, 'поступила в очередь'
        )
        if msg_queed != 'No message':
            # await send_msg_all_subscribed(msg_queed)
            for chat_id in mysql().db_get_rl():
                await bot.send_message(chat_id=chat_id, text=msg_queed + how_many_is_working(),
                                       parse_mode=ParseMode.MARKDOWN)

        now_id, now_db, msg_in_work = helper_func(
            'rl_now', config.search_issues_work, 'в работе!'
        )
        if msg_in_work != 'No message':
            for chat_id in mysql().db_get_rl():
                await bot.send_message(chat_id=chat_id, text=msg_in_work + how_many_is_working(),
                                       parse_mode=ParseMode.MARKDOWN)

        ###
        # List of new completed tasks
        for issue in now_db:
            if issue not in now_id:
                j_issue = JiraTools().jira_issue(int(issue))
                logger.debug('j_releases, j_issue: %s', j_issue)
                msg_done_new_task = f'[{j_issue.fields.summary}]' \
                                    f'(https://jira.yamoney.ru/browse/{j_issue.key}) ' \
                                    f'выполнена! ({j_issue.fields.resolution})'
                for chat_id in mysql().db_get_rl():
                    await bot.send_message(chat_id=chat_id,
                                           text=msg_done_new_task + how_many_is_working(),
                                           parse_mode=ParseMode.MARKDOWN)
                # 'Выполнена! kiosk+1.223.0, ADMSYS-34586'
                logger.info('Выполнена! %s, %s, %s', j_issue.fields.summary,
                            j_issue.key, j_issue.fields.resolution)

                # After completing each task, write dict
                # { 'releases': {'deposit': ['1.1.1', '1.1.2'], 'shiro': ['2.2.1', '2.2.2'] }} to
                # aerospike(item='auto_rollback', set='rollback')
                logger.info('fields.resolution: %s', str(j_issue.fields.resolution))
                if str(j_issue.fields.resolution) == 'Выполнен':
                    # To the aerospike we write only successfully
                    # completed tasks
                    collect_success_releases(j_issue.fields.summary)
                    # Send notification about the successful
                    # completion of the task without the participation of people
                    config_deploy = aero.read(item='deploy', aerospike_set='remaster')
                    name_version_task = app_version(j_issue.fields.summary)
                    if name_version_task['name'] in config_deploy['not_agreement']:
                        telegram_msg = f'*{j_issue.fields.summary}* ' \
                                       f'[{j_issue.key}]' \
                                       f'(https://jira.yamoney.ru/browse/{j_issue.key}) ' \
                                       'успешно выкатилась без участия человека.'
                        request_chat_id_api_v1 = requests.get(f'{config.api_chat_id}/{j_issue.key}')
                        list_chat_id_recipients = list(request_chat_id_api_v1.json())
                        for chat_id in list_chat_id_recipients:
                            await bot.send_message(chat_id=chat_id, text=telegram_msg,
                                                   parse_mode=ParseMode.MARKDOWN)
                        logger.info('Sent notification successfully completion %s to %s',
                                    j_issue.key, list_chat_id_recipients)
                else:
                    logger.info('Why not collect_success_releases? %s', j_issue.fields.resolution)

        ###
        # List of tasks completed quickly
        for issue in waiting_db:
            if issue not in waiting_id:
                if issue not in now_id:
                    j_issue = JiraTools().jira_issue(int(issue))
                    for chat_id in mysql().db_get_rl():
                        msg_done = f'[{j_issue.fields.summary}]' \
                                   f'(https://jira.yamoney.ru/browse/{j_issue.key}) ' \
                                   f'выполнена! ({j_issue.fields.resolution})'
                        await bot.send_message(chat_id=chat_id,
                                               text=msg_done + how_many_is_working(),
                                               parse_mode=ParseMode.MARKDOWN)
                    logger.info('resolution is %s', j_issue.fields.resolution)
                    if str(j_issue.fields.resolution) == 'Выполнен':
                        # To the aerospike we write only successfully
                        # completed tasks
                        collect_success_releases(j_issue.fields.summary)
    except BotBlocked:
        logger.info('YM release bot was blocked by %s', chat_id)
    except ChatNotFound:
        logger.error('Chat not found with: %s', chat_id)
        await bot.send_message(chat_id=279933948, text=f'*YMReleaseBot was blocked by {chat_id}*')
    except Exception:
        logger.exception('start_update_releases')


def app_version(issue_name) -> dict:
    """
        Get name, version from Jira task name
        :param issue_name: Jira task name
        :type issue_name: str
        :return: name, version of Jira task
        :rtype: dict {'name': 'currency-storage', 'version': '1.3.1'}
    """
    app = re.match('^([0-9a-z-]+)[+=]([0-9a-z-.]+)$', issue_name.strip())

    output = {'name': app[1], 'version': app[2]} if app else {'name': issue_name, 'version': False}

    return output


def collect_success_releases(issue_name):
    """
        Set to aerospike succeed releases for possible rollback
        :param issue_name - name of Jira task
        :type issue_name currency-storage+1.3.1
        :return:
    """
    logger.info('collect_success_releases started')
    try:
        # get name and version of release
        release_name_version = app_version(issue_name)
        if release_name_version['version'] is False:
            logger.info('I can\'t get version from this release: %s', issue_name)
        else:
            components_releases_success = aero.read(item='auto_rollback',
                                                     aerospike_set='rollback')

            if len(components_releases_success) == 0:
                # create structure of key
                components_releases_success = {
                    'releases':
                        {release_name_version['name']: [release_name_version['version']]}
                }
            else:
                # if with release name already exist
                if components_releases_success['releases'].get(release_name_version['name']):
                    components_releases_success['releases'][release_name_version['name']].append(
                        release_name_version['version'])
                else:
                    new_component = {
                        release_name_version['name']: [release_name_version['version']]
                    }
                    components_releases_success['releases'].update(new_component)
            logger.info('collect_success_releases, response: %s',
                        aero.write(item='auto_rollback',
                                    bins=components_releases_success,
                                    aerospike_set='rollback'))
    except Exception:
        logger.exception('collect_success_releases')


def request_telegram_send(telegram_message: dict) -> bool:
    """
        Send message to telegram channel
        :param: telegram_message - dict with list of chat_id, msg and optional field type
        :return: bool value depends on api response
    """
    try:
        logger.info('request_telegram_send started')
        req_tg = requests.post(config.api_tg_send, json=telegram_message)
        if req_tg.ok:
            logger.info('Successfully sent message to tg for %s via api',
                        telegram_message['chat_id'])
            feedback = True
        else:
            logger.error('Error in request_telegram_send for %s', telegram_message['chat_id'])
            feedback = False
        return feedback
    except Exception:
        logger.exception('request_telegram_send')
