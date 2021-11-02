#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from playhouse.pool import PostgresqlDatabase, PooledPostgresqlDatabase

bot_token = os.environ.get('telegram_token').rstrip()

#PG configuration
postgres = PooledPostgresqlDatabase(
    'release_bot',
    user=os.environ.get('postgres_user').rstrip(),
    password=os.environ.get('postgres_pass').rstrip(),
    host='iva-pgtools.yamoney.ru',
    port=7432,
    max_connections=32,
    stale_timeout=300)

couch_db = {
    'host': 'ugr-couchdb1.yamoney.ru',
    'port': '5984',
    'db_name': 'lxc_collector',
    'user': os.environ.get('couch_db_user').rstrip(),
    'passwd': os.environ.get('couch_db_pass').rstrip()
}

bot_api_url = 'http://releasebot-api.intools.yooteam.ru'
api_lock_unlock = f'{bot_api_url}/api/tasks/lock_unlock'
api_get_timetable = f'{bot_api_url}/exchange/get_timetable'

staff_url = 'https://staff.yooteam.ru'

jira_host = 'https://jira.yooteam.ru'
jira_user = os.environ.get('jira_user')
jira_pass = os.environ.get('jira_pass')
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
