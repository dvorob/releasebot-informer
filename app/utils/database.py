#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Input/output for mysql
"""
from datetime import datetime
from app.utils import logging
import app.config as config
from peewee import *

logger = logging.setup()

__all__ = ['MysqlPool']

class BaseModel(Model):
    class Meta:
        database = config.mysql

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

class Users(BaseModel):
    id = IntegerField()
    account_name = CharField(unique=True)
    full_name = CharField()
    tg_login = CharField()
    working_status = CharField()
    notification = CharField(default='none')
    admin = IntegerField(default=0)
    tg_id = CharField()
    email = CharField()

class DutyList(BaseModel):
    duty_date = DateField(unique=True)
    message = CharField()
    duty_chat_list = CharField()

class MysqlPool:

    def __init__(self):
        self.db = config.mysql

    async def db_subscribe(self, chat_id, chat_type, subscription):
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

    async def db_get_option(self, name):
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

    async def db_set_option(self, name, value):
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

    async def db_get_rl(self) -> list:
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

    async def db_set_users(self, account_name, full_name, tg_login, working_status, tg_id, email):
        # Записать пользователя в таблицу Users. Переберет параметры и запишет только те из них, что заданы. 
        # Иными словами, если вычитали пользователя из AD с полным набором полей, запись будет создана, поля заполнены.
        # Если передадим tg_id для существующего пользователя, заполнится только это поле
        logger.debug('db set users started for %s %s %s %s %s ', account_name, full_name, tg_login, working_status, tg_id, email)
        try:
            self.db.connect()
            db_users, _ = Users.get_or_create(account_name=account_name)
            if full_name:
                db_users.full_name = full_name
            if tg_login:
                db_users.tg_login = tg_login
            if working_status:
                db_users.working_status = working_status
            if tg_id:
                db_users.tg_id = tg_id
            if email:
                db_users.email = email
            db_users.save()
        except Exception:
            logger.exception('exception in db_set_users')
        finally:
            self.db.close()

    async def db_get_users(self, field, value) -> list:
        # сходить в таблицу Users и найти записи по заданному полю с заданным значением. Вернет массив словарей.
        # например, найти Воробьева можно запросом db_get_users('account_name', 'ymvorobevda')
        # всех админов - запросом db_get_users('admin', 1)
        logger.info('db_get_users param1 param2 %s %s', field, value)
        result = []
        try:
            self.db.connect()
            db_users = Users.select().where(getattr(Users, field) == value)
            for v in db_users:
                result.append((vars(v))['__data__'])
            return result
        except Exception:
            logger.exception('exception in db get users')
            return result
        finally:
            self.db.close()

    # Вытащить пользователя из БД. Задается юзернейм, поиск ведется по полям account_name и tg_name. Обёртка вокруг db_get_user
    async def get_username_from_db(self, username):
        # Получили username, который может быть логином в AD или в ТГ. Проверим по обоим полям, запишем непустые объекты в массив 
        # Вернем первого члена массива (если в БД всплывут дубли, например, где у одного tg_login = account_name другого, надо что-то придумать)
        logger.info('Mysql: trying to get users from Users table')
        users_array = []
        user_from_db = await self.db_get_users('account_name', username)
        users_array.append(user_from_db) if len(user_from_db) > 0 else logger.info('Nothing found in Users for %s as account_name', username)

        user_from_db = await self.db_get_users('tg_login', username)
        users_array.append(user_from_db) if len(user_from_db) > 0 else logger.info('Nothing found in Users for %s as tg_login', username)
        if len(users_array) > 0:
            users_array = users_array[0]
        else:
            users_array = []
        return(users_array)

    async def db_set_duty(self, duty_date, message, duty_chat_list):
        # Записать дежурных на сегодня
        logger.debug('db set duty started for %s %s %s ', duty_date, message, duty_chat_list)
        try:
            self.db.connect()
            db_users, _ = DutyList.get_or_create(duty_date=duty_date)
            db_users.message = message
            db_users.duty_chat_list = duty_chat_list
            db_users.save()
        except Exception:
            logger.exception('exception in db_get_users')
        finally:
            self.db.close()

    async def db_get_duty(self, duty_date) -> list:
        # Сходить в таблицу xerxes.duty_list за дежурными на заданную дату
        try:
            self.db.connect()
            return DutyList.get(DutyList.duty_date == duty_date)
        except Exception:
            logger.exception('exception in db get duty')
        finally:
            self.db.close()