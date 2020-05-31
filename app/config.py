#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getenv

bot_token = getenv('secret_telegram_token')
bot_master = {'vorobiev_telegram_id': 279933948,
              'reytsman_telegram_id': 254802165,
              'spiridonov_telegram_id': 104632759,
              'krepyshev_telegram_id': 132381920,
              'uchaev_telegram_id': 386533784,
              'podlipaev_telegram_id': 325499139,
              'kim_telegram_id': 930740404,
              'igoshin_telegram_id': 153780462,
              'batuto_telegram_id': 124171502,
              'titov_telegram_id': 81194573,
              'gromov_telegram_id': 390182439       
              }

tz_name = 'Europe/Moscow'

ex_host = 'mail-mx10.yamoney.ru'
ex_user = getenv('secret_exchange_user')
ex_pass = getenv('secret_exchange_pass')
ex_cal = 'adminsonduty@yamoney.ru'
ex_tz = 'Europe/Moscow'

db_host = 'mysql.xerxes.svc.ugr-base1.kube.yamoney.ru'
db_user = getenv('secret_mysql_user')
db_pass = getenv('secret_mysql_pass')
db_name = 'xerxes'

jenkins = 'http://xerxes-leeroy:8080'
api = 'http://xerxes-api-v1/api-v1'
api_chat_id = f'{api}/chat-id'
api_aerospike_read = f'{api}/aerospike/read'
api_aerospike_write = f'{api}/aerospike/write'
api_tg_send = f'{api}/tg_new/send'

jira_host = 'https://jira.yamoney.ru'
jira_user = getenv('secret_jira_user')
jira_pass = getenv('secret_jira_pass')

waiting_assignee_releases = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                     'status = "TO DO" ORDER BY Rank ASC'

search_issues_wait = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                     'status IN (Open, "Waiting release", "TO DO") ORDER BY Rank ASC'

search_issues_work = 'project = ADMSYS AND issuetype = "Release (conf)" AND status IN ' \
                     '("PARTIAL DEPLOY", CONFIRM, "FULL DEPLOY") ORDER BY Rank ASC'

search_issues_completed = 'project = ADMSYS AND issuetype = "Release (conf)" ' \
                          'AND status = Resolved ORDER BY Rank ASC'

issues_waiting = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                 'status IN ("Open", "На согласовании", "Waiting release", "TO DO") ' \
                 'ORDER BY Rank ASC'

issues_not_closed_resolved = 'project = ADMSYS AND issuetype = "Release (conf)" ' \
                           'AND status NOT IN (Closed, Resolved) ORDER BY Rank ASC'

staff_url = 'https://census.xerxes.svc.ugr-base1.kube.yamoney.ru:8444'
