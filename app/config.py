#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from playhouse.pool import PostgresqlDatabase, PooledPostgresqlDatabase
from enum import Enum

bot_token = os.environ.get('telegram_token').rstrip()

#PG configuration
postgres = PooledPostgresqlDatabase(
    'release_bot',
    user=os.environ.get('postgres_user').rstrip(),
    password=os.environ.get('postgres_pass').rstrip(),
    host='master.db-postgres-cluster-14.service.consul.yooteam.ru',
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
api_take_duty = f'{bot_api_url}/api/take_duty'

staff_url = 'https://staff.yooteam.ru'
wiki_url = 'https://wiki.yooteam.ru'

assistant_wiki_url = wiki_url + "/display/admins/ReleaseBot.Assistant#ReleaseBot.Assistant-%D0%94%D0%B5%D0%B6%D1%83%D1%80%D1%81%D1%82%D0%B2%D0%B0"

jira_host = 'https://jira.yooteam.ru'
jira_user = os.environ.get('jira_user')
jira_pass = os.environ.get('jira_pass')
jira_options = {'server': jira_host, 'verify': False}

lk_host = 'https://lk.yooteam.ru'
tt_api_url = f'{lk_host}/1c82_lk/hs/teamtransition/v1/members'

waiting_assignee_releases = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                     'status = "TO DO" ORDER BY Rank ASC'

search_issues_wait = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                     'status IN (Open, "Waiting release", "TO DO") ORDER BY Rank ASC'

issues_waiting = 'project in (ADMSYS, DEPLOY) AND issuetype = "Release (conf)" AND ' \
                 'status IN ("Waiting release") ORDER BY Rank ASC'

issues_open = 'project in (DEPLOY) AND issuetype = "Release (conf)" AND ' \
                 'status IN (Open) ORDER BY Rank ASC'

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

class DaysOfWeek(Enum):
    Monday = 'Понедельник'
    Tuesday = 'Вторник'
    Wednesday = 'Среда'
    Thursday = 'Четверг'
    Friday = 'Пятница'
    Saturday = 'Суббота'
    Sunday = 'Воскресенье'

bplatform_specs_delivery = 'https://bitbucket.yooteam.ru/pages/PRODUCT-SPECS/backend-platform/master/browse/index.html#platform-delivery'