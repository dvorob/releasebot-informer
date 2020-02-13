#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Input/output for mysql
"""
from datetime import datetime
from app.utils import logging
import app.config as config
from playhouse.pool import PooledMySQLDatabase
from peewee import *

logger = logging.setup()

__all__ = ['MysqlPool']

db = PooledMySQLDatabase(
    config.db_name,
    host=config.db_host,
    user=config.db_user,
    passwd=config.db_pass,
    max_connections=8,
    stale_timeout=300)


class BaseModel(Model):
    class Meta:
        database = db


class Chat(BaseModel):
    """
        Create mysql table Chat
        id - tg chat_id
        type - group/private
        username - tg_username
        lastname - tg_lastname
        started - time
        last - time
        ym -
        rl - подписка на все сообщения бота
        digest
    """
    id = CharField()
    type = CharField()
    username = CharField()
    lastname = CharField()
    started = DateTimeField(default=datetime.now)
    last = DateTimeField(default=datetime.now)
    ym = BooleanField(default=False)
    rl = BooleanField(default=False)
    digest = BooleanField(default=False)

    class Meta:
        indexes = (
            (('id', 'type'), True)
        )


class Option(BaseModel):
    name = CharField(unique=True)
    value = CharField()


class MysqlPool:
    """

    """
    def __init__(self):
        self.db = PooledMySQLDatabase(
            config.db_name,
            host=config.db_host,
            user=config.db_user,
            passwd=config.db_pass,
            max_connections=8,
            stale_timeout=300)

    def db_subscribe(self, chat_id, chat_type, subscription):
        """
            Subscribe/unsubscribe employee to all bot notifications
            :param chat_id: tg_chat_id
            :param chat_type: private/group
            :param subscription: 1 - subscribe, 0 - unsubscribe
        """
        try:
            self.db.connect()
            db_chat = Chat.get(id=chat_id, type=chat_type)
            db_chat.rl = subscription
            db_chat.save()
        except Exception:
            logger.exception("MysqlPool, db_subscribe")
        finally:
            self.db.close()

    def db_get_option(self, name):
        """
            Get value from db key
            :param name:
            :return:
        """
        logger.debug('db_get_option started')
        try:
            self.db.connect()
            db_option, _ = Option.get_or_create(name=name)
            db_option.save()
            return db_option.value
        except Exception:
            logger.exception('db_get_option')
        finally:
            self.db.close()

    def db_set_option(self, name, value):
        """
            Set value to db
            :param name:
            :param value:
        """
        try:
            self.db.connect()
            db_option, _ = Option.get_or_create(name=name)
            db_option.value = value
            db_option.save()
            if value:
                logger.debug('saved %s to %s', value, name)
        except Exception:
            logger.exception('db_set_option')
        finally:
            self.db.close()

    def db_get_rl(self) -> list:
        """
            Get list of employee who subscribed to events
            :return: list of tg_chat_id
        """
        logger.debug('db_get_rl started')
        try:
            self.db.connect()
            db_chat = Chat.select(Chat.id).where(Chat.rl == '1')
            result = []

            for line in db_chat:
                result.append(line.id)
            logger.info('db_get_rl, result: %s', result)
            return result
        except Exception:
            logger.exception('db_get_rl')
        finally:
            self.db.close()
