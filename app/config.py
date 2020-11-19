#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getenv
from playhouse.pool import PooledMySQLDatabase

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
              'grachev_telegram_id': 170541899,
              'gromov_telegram_id': 390182439,
              'avdonin_telegram_id': 145902753
              }

mysql = PooledMySQLDatabase(
    'xerxes',
    host='mysql.xerxes.svc.ugr-base1.kube.yamoney.ru',
    user=getenv('secret_mysql_user'),
    passwd=getenv('secret_mysql_pass'),
    max_connections=8,
    stale_timeout=300)

couch_db = {
    'host': 'ugr-couchdb1.yamoney.ru',
    'port': '5984',
    'db_name': 'lxc_collector',
    'user': 'admin',
    'passwd': '2G1FgGEuJtFmZxQWh3aN'
}

jenkins = 'http://releasebot-leeroy:8080'

api = 'http://releasebot-api/api-v1'
api_chat_id = f'{api}/chat-id'
api_aerospike_read = f'{api}/aerospike/read'
api_aerospike_write = f'{api}/aerospike/write'
api_get_user_info = f'{api}/get_user_info'
api_sign_up = f'{api}/sign_up'
api_lock_unlock = f'{api}/tasks/lock_unlock'

jira_host = 'https://jira.yamoney.ru'
jira_user = getenv('secret_jira_user')
jira_pass = getenv('secret_jira_pass')
jira_options = {'server': jira_host, 'verify': False}

waiting_assignee_releases = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                     'status = "TO DO" ORDER BY Rank ASC'

search_issues_wait = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                     'status IN (Open, "Waiting release", "TO DO") ORDER BY Rank ASC'

issues_waiting = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                 'status IN ("Waiting release") ORDER BY Rank ASC'

issues_confirm_full_resolved = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                               'status IN (CONFIRM, "FULL DEPLOY", Resolved) ORDER BY Rank ASC'

search_issues_work = 'project = ADMSYS AND issuetype = "Release (conf)" AND status IN ' \
                     '("PARTIAL DEPLOY", CONFIRM, "FULL DEPLOY") ORDER BY Rank ASC'

search_issues_completed = 'project = ADMSYS AND issuetype = "Release (conf)" ' \
                          'AND status = Resolved ORDER BY Rank ASC'

issues_waiting_confirm = 'project = ADMSYS AND issuetype = "Release (conf)" AND ' \
                 'status IN ("Open", "На согласовании", "Waiting release", "TO DO") ' \
                 'ORDER BY Rank ASC'

issues_not_closed_resolved = 'project = ADMSYS AND issuetype = "Release (conf)" ' \
                           'AND status NOT IN (Closed, Resolved) ORDER BY Rank ASC'
