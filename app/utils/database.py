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

class Chats(BaseModel):
    id = IntegerField()
    tg_id = CharField()
    title = CharField()
    started_by = CharField()
    date_start = DateTimeField(default=datetime.now)
    notification = CharField(default='none')
    description = CharField()

class Option(BaseModel):
    name = CharField(unique=True)
    value = CharField()

class Users(BaseModel):
    id = IntegerField()
    account_name = CharField(unique=True)
    full_name = CharField()
    tg_login = CharField()
    tg_id = CharField()
    working_status = CharField()
    email = CharField()
    notification = CharField(default='none')
    admin = IntegerField(default=0)
    date_update = DateTimeField()

class Duty_List(BaseModel):
    id = IntegerField()
    duty_date = DateField(index=True)
    area = CharField()
    full_name = CharField()
    account_name = CharField()
    full_text = CharField()

class MysqlPool:

    def __init__(self):
        self.db = config.mysql

    async def set_chats(self, tg_id, title, started_by, notification):
        """
        """
        logger.info('sret chat called for %s %s %s notification %s', tg_id, title, started_by, notification)
        try:
            self.db.connect(reuse_if_open=True)
            db_chat, _ = Chats.get_or_create(tg_id=tg_id)
            logger.info('a chat object is %s', db_chat)
            db_chat.title = title
            db_chat.started_by = started_by
            db_chat.notification = notification
            db_chat.save()
        except Exception:
            logger.exception("set chats error")
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
            self.db.connect(reuse_if_open=True)
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
            self.db.connect(reuse_if_open=True)
            db_option, _ = Option.get_or_create(name=name)
            db_option.value = value
            db_option.save()
            if value:
                logger.debug('saved %s to %s', value, name)
        except Exception as e:
            logger.exception('db set option %s', str(e))
        finally:
            self.db.close()

    async def get_subscribers_to_everything(self) -> list:
        """
            Get list of employee and Chats who subscribed to events
            :return: list of tg_chat_id
        """
        try:
            self.db.connect(reuse_if_open=True)
            db_chats = Chats.select(Chats.tg_id).where(Chats.notification == 'all', Chats.tg_id.is_null(False))
            db_users = Users.select(Users.tg_id).where(Users.notification == 'all', Users.tg_id.is_null(False))
            logger.info('db chats = %s   db users = %s', db_chats, db_users)
            result = []

            for line in db_chats:
                result.append(line.tg_id)
            for line in db_users:
                result.append(line.tg_id)
            logger.debug('get_subscribers_to_everything, result: %s', result)
            return result
        except Exception as e:
            logger.exception('get subscribers to everything error %s', str(e))
        finally:
            self.db.close()

    async def db_set_users(self, account_name, full_name, tg_login, working_status, tg_id, notification, email):
        # Записать пользователя в таблицу Users. Переберет параметры и запишет только те из них, что заданы. 
        # Иными словами, если вычитали пользователя из AD с полным набором полей, запись будет создана, поля заполнены.
        # Если передадим tg_id для существующего пользователя, заполнится только это поле
        logger.debug('db set users started for %s', account_name)
        try:
            self.db.connect(reuse_if_open=True)
            db_users, _ = Users.get_or_create(account_name=account_name)
            if full_name:
                db_users.full_name = full_name
            if tg_login:
                db_users.tg_login = tg_login
            if working_status:
                db_users.working_status = working_status
            if tg_id:
                db_users.tg_id = tg_id
            if notification:
                db_users.notification = notification
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
            self.db.connect(reuse_if_open=True)
            db_users = Users.select().where(getattr(Users, field) == value)
            for v in db_users:
                result.append((vars(v))['__data__'])
            return result
        except Exception:
            logger.exception('exception in db get users')
            return result
        finally:
            self.db.close()

    async def get_all_tg_id(self) -> list:
        # Отобрать всех пользователей, у которых заполнен tg_id - для массовых уведомлений
        logger.info('db get users with tg id')
        result = []
        try:
            self.db.connect(reuse_if_open=True)
            db_users = Users.select().where(Users.tg_id.is_null(False))
            for v in db_users:
                result.append((vars(v))['__data__'])
            logger.info(result)
            return result
        except Exception:
            logger.exception('exception in db get users with tg id')
            return result
        finally:
            self.db.close()

    async def search_users_by_fullname(self, full_name):
        # сходить в таблицу Users и найти записи по заданному полю с заданным значением. Вернет массив словарей.
        # например, найти Воробьева можно запросом db_get_users('account_name', 'ymvorobevda')
        # всех админов - запросом db_get_users('admin', 1)
        users_array = []
        try:
            logger.info('Search users by fullname for %s', full_name)
            self.db.connect(reuse_if_open=True)
            if (type(full_name) == str):
                full_name = re.split(' ', full_name)

            if len(full_name) > 1:
                db_users = Users.select().where(
                    (Users.full_name.startswith(full_name[0]) & Users.full_name.endswith(full_name[1])) |
                    (Users.full_name.startswith(full_name[1]) & Users.full_name.endswith(full_name[0])))
            elif len(full_name) == 1:
                db_users = Users.select().where(Users.full_name.endswith(full_name[0]))
            else:
                db_users = ['Nobody']
            for v in db_users:
                users_array.append((vars(v))['__data__'])
            return users_array
        except Exception:
            return users_array
        finally:
            self.db.close()

    # Вытащить пользователя из БД. Задается юзернейм, поиск ведется по полям account_name и tg_name. Обёртка вокруг db_get_user
    async def search_users_by_account(self, account_name):
        # Получили account_name, который может быть логином в AD или в ТГ. Проверим по обоим полям, запишем непустые объекты в массив 
        # Вернем первого члена массива (если в БД всплывут дубли, например, где у одного tg_login = account_name другого, надо что-то придумать)
        users_array = []
        try:
            logger.info('Search users by account for %s', account_name)
            db_users = await self.db_get_users('account_name', account_name)
            users_array.append(db_users) if len(db_users) > 0 else logger.info('Nothing found in Users for %s as account_name', account_name)

            db_users = await self.db_get_users('tg_login', account_name)
            users_array.append(db_users) if len(db_users) > 0 else logger.info('Nothing found in Users for %s as tg_login', account_name)
            if len(users_array) > 0:
                users_array = users_array[0]
            else:
                users_array = []
            return users_array
        except Exception as e:
            logger.exception('Exception in search users by account %s', str(e))
            return users_array

    async def db_set_duty(self, duty_date, message, duty_chat_list):
        # Записать дежурных на сегодня
        logger.debug('db set duty started for %s %s %s ', duty_date, message, duty_chat_list)
        try:
            self.db.connect(reuse_if_open=True)
            db_users, _ = Duty_List.get_or_create(duty_date=duty_date)
            db_users.message = message
            db_users.duty_chat_list = duty_chat_list
            db_users.save()
        except Exception:
            logger.exception('exception in db_get_users')
        finally:
            self.db.close()

    async def get_duty(self, duty_date) -> list:
        # Сходить в таблицу xerxes.duty_list за дежурными на заданную дату
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            db_query = (Duty_List
                        .select(Duty_List, Users.tg_id)
                        .join(Users, JOIN.LEFT_OUTER, on=(Duty_List.account_name == Users.account_name))
                        .where(Duty_List.duty_date == duty_date))
            for v in db_query:
                result.append((vars(v))['__data__'])
            logger.info('get duty for %s %s', duty_date, result)
            return result
        except Exception:
            logger.exception('exception in db get duty')
        finally:
            self.db.close()