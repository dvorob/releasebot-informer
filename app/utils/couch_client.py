#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Input/output for coucdb 
"""

import couchdb
import app.config as config
from app.utils import logging

couch_config = config.couch_db
logger = logging.setup()

couch_connect = couchdb.Server(f"http://{couch_config['user']}:{couch_config['passwd']}@{couch_config['host']}:{couch_config['port']}/")
try:
    couch_db = couch_connect[f"{couch_config['db_name']}"]
    logger.info(f"Success connect couchdb {couch_config['host']}")
except Exception as e:
    logger.exception(f'Failed connect couchdb. Error: {e}')
    logger.debug(f'Couchdb connect settings: {couch_connect}')

local_db_copy = {}

def copy_part_db(except_hv_name = []):
    search = {'selector': {"type": "hypervisor"}, "limit": 100 }
    for item in couch_db.find(search):
        if item['name'] not in except_hv_name:
            local_db_copy.update({item['name']: item })


async def search_lxc_for_app(app_name):
    app_name = app_name.replace('_', '-')
    copy_part_db()
    hv_name_list = []
    hv_name_map = {}
    for value in local_db_copy.values():
        for cnt in value['containers']['list']:
            if cnt.find(app_name) != -1:
                hv_name_list.append(value['name'])
                hv_name_map.update({cnt: value['name']})
                break
    if len(hv_name_list) == 0:
        return f"{app_name}: not fount"
    elif len(hv_name_list) > 1:
        limits = ''
        for item in hv_name_list[:-1]:
            limits += f'{item}, '
        limits += hv_name_list[-1]
    else:
        limits = hv_name_list[0]
    hv_name_map.update({'limits': limits })
    return hv_name_map