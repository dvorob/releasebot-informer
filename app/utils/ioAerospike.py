#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Input/output for aerospike
"""
import requests
from app.utils import logging
import app.config as config

logger = logging.setup()


def read(item, aerospike_set) -> dict:
    """
        Read from aerospike via api-v1
        :param: item - item in aerospike
        :param: aerospike_set - set in aerospike
        :return: 'Response' object - response from api-v1, a lot of methods
    """
    logger.debug('request_read_aerospike started: item=%s, set=%s', item, aerospike_set)
    headers = {'item': item, 'set': aerospike_set}
    all_return_queue_task = requests.get(config.api_aerospike_read, headers=headers)
    return all_return_queue_task.json()


def write(item, bins, aerospike_set):
    """
        Write to aerospike via api-v1
        :param: item - item in aerospike
        :param: aerospike_set - set in aerospike
        :return: 'Response' object - response from api-v1, a lot of methods
    """
    try:
        logger.debug('request_write_aerospike started: item=%s, set=%s, bins=%s',
                     item, aerospike_set, bins)
        headers = {'item': item, 'set': aerospike_set}
        all_return_queue_task = requests.post(config.api_aerospike_write,
                                              headers=headers, json=bins)
        return all_return_queue_task
    except Exception:
        logger.exception('request_write_aerospike')
