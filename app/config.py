#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getenv
from playhouse.pool import PostgresqlDatabase, PooledPostgresqlDatabase

bot_token = getenv('secret_telegram_token')

#PG configuration
postgres = PooledPostgresqlDatabase(
    'release_bot',
    user=getenv('secret_postgres_user').rstrip(),
    password=getenv('secret_postgres_pass').rstrip(),
    host='iva-pgtools2.yamoney.ru',
    port=7432,
    max_connections=32,
    stale_timeout=300)

couch_db = {
    'host': 'ugr-couchdb1.yamoney.ru',
    'port': '5984',
    'db_name': 'lxc_collector',
    'user': 'admin',
    'passwd': '2G1FgGEuJtFmZxQWh3aN'
}

api = 'http://releasebot-api'
api_lock_unlock = f'{api}/api-v1/tasks/lock_unlock'
api_get_timetable = f'{api}/exchange/get_timetable'

staff_url = 'https://staff.yooteam.ru'

jira_host = 'https://jira.yooteam.ru'
jira_user = getenv('secret_jira_user')
jira_pass = getenv('secret_jira_pass')
jira_options = {'server': jira_host, 'verify': False}

tt_api_url = f'{jira_host}/rest/teamtransitions/2.0/member/'

waiting_assignee_releases = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                     'status = "TO DO" ORDER BY Rank ASC'

search_issues_wait = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                     'status IN (Open, "Waiting release", "TO DO") ORDER BY Rank ASC'

issues_waiting = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                 'status IN ("Waiting release") ORDER BY Rank ASC'

issues_confirm_full_resolved = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                               '(status IN (CONFIRM, "FULL DEPLOY") OR (status in (Resolved) AND updated >= startOfDay())) ' \
                               'ORDER BY Rank ASC'

search_issues_work = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND status IN ' \
                     '("PARTIAL DEPLOY", CONFIRM, "FULL DEPLOY") ORDER BY Rank ASC'

search_issues_started = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND status IN ' \
                     '("TO DO", "PARTIAL DEPLOY", CONFIRM, "FULL DEPLOY") ORDER BY Rank ASC'

search_issues_completed = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" ' \
                          'AND status = Resolved ORDER BY Rank ASC'

issues_waiting_confirm = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                 'status IN ("Open", "На согласовании", "Waiting release", "TO DO") ' \
                 'ORDER BY Rank ASC'

issues_not_closed_resolved = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" ' \
                           'AND status NOT IN (Closed, Resolved) ORDER BY Rank ASC'
