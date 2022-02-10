#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Работа с БД в PostgreSQL
"""
# External
import json
from datetime import datetime
from peewee import *
# Internal
import config
import re
from utils import logging

logger = logging.setup()

__all__ = ['PostgresPool']

class BaseModel(Model):
    class Meta:
        database = config.postgres

class App_List(BaseModel):
    id = IntegerField(primary_key=True)
    app_name = CharField(unique=True)
    perimeter = CharField(default=None)
    release_mode = CharField(default=None)
    admins_team = CharField(default=None)
    queues = TextField(default=None)
    bot_enabled = BooleanField(default=None)
    dev_team = CharField(default=None)
    jira_com = CharField(default=None)
    locked_by = CharField(default=None)

class Option(BaseModel):
    name = CharField(unique=True)
    value = CharField()

class Users(BaseModel):
    id = IntegerField(primary_key=True)
    account_name = CharField(unique=True)
    full_name = CharField()
    tg_login = CharField()
    tg_id = CharField()
    working_status = CharField()
    email = CharField()
    notification = CharField(default='none')
    admin = IntegerField(default=0)
    date_update = DateField()
    staff_login = CharField()
    first_name = CharField()
    middle_name = CharField()
    ops = IntegerField(default=0)
    team_key = CharField(default=None)
    team_name = CharField(default=None)
    department = CharField(default=None)

class User_Subscriptions(BaseModel):
    id = IntegerField(primary_key=True)
    account_name = CharField()
    subscription = CharField()

class Duty_List(BaseModel):
    id = IntegerField()
    duty_date = DateField(index=True)
    area = CharField()
    full_name = CharField()
    account_name = CharField()
    full_text = CharField()
    tg_login = CharField()

class Parameters(BaseModel):
    id = IntegerField(index=True)
    name = CharField()
    value = CharField()
    description = CharField()

class Releases_List(BaseModel):
    id = IntegerField(primary_key=True)
    jira_task = CharField(unique=True)
    app_name = CharField(default=None)
    app_version = CharField(default=None)
    fullname = CharField(default=None)
    date_create = DateField(default=datetime.now)
    date_update = DateField(default=None)
    resolution = CharField(default=None)
    is_rollbacked = BooleanField(default=None)
    is_static_released = BooleanField(default=None)
    notifications_sent = TextField(default=None)

class PostgresPool:

    def __init__(self):
        self.db = config.postgres

    # ---------------------------------
    # ----- AppList -------------------

    def get_application_metainfo(self, app_name) -> list:
        # Сходить в AppList и получить конфигурацию деплоя конкретного приложения - очереди, режим выкладки и прочее
        logger.info('get application metainfo %s ', app_name)
        try:
            self.db.connect(reuse_if_open=True)
            result = {}
            db_query = App_List.select().where(App_List.app_name == app_name)
            for v in db_query:
                result = vars(v)['__data__']
            return result
        except Exception as e:
            logger.exception('exception in get application metainfo %s', e)
        finally:
            self.db.close()


    def get_many_applications_metainfo(self, apps_list) -> list:
        # Сходить в AppList и получить конфигурацию деплоя конкретного приложения - очереди, режим выкладки и прочее
        logger.info('get many applications metainfo %s ', apps_list)
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            db_query = App_List.select().where(App_List.app_name.in_(apps_list))
            for v in db_query:
                result.append(vars(v)['__data__'])
            return result
        except Exception as e:
            logger.exception('exception in get many applications metainfo %s', e)
        finally:
            self.db.close()


    def get_applications(self, field, value, operation) -> list:
        # сходить в таблицу AppList и найти записи по заданному полю с заданным значением. Вернет массив словарей.
        logger.info(f'get_applications {field} {value} {operation}')
        result = []
        try:
            self.db.connect(reuse_if_open=True)
            if operation == 'equal':
                db_apps = App_List.select().where(getattr(App_List, field) == value)
            elif operation == 'like':
                db_apps = App_List.select().where(getattr(App_List, field) % value)
            else:
                db_apps = []
            logger.info(db_apps)
            for v in db_apps:
                result.append((vars(v))['__data__'])
            return result
        except Exception as e:
            logger.exception(f'exception in get apps {str(e)}')
            return result
        finally:
            self.db.close()

    def get_all_applications(self) -> list:
        # сходить в таблицу AppList и найти все записи  
        logger.info(f'get all applications')
        result = []
        try:
            self.db.connect(reuse_if_open=True)
            db_apps = App_List.select()
            logger.info(db_apps)
            for v in db_apps:
                result.append((vars(v))['__data__'])
            return result
        except Exception:
            logger.exception(f'exception in get all applications {str(e)}')
            return result
        finally:
            self.db.close()

    # ---------------------------------
    # ----- Users   -------------------

    async def set_users(self, account_name, full_name, tg_login, working_status, tg_id, notification, email):
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
            logger.exception('exception in set_users')
        finally:
            self.db.close()


    async def get_users(self, field, value) -> list:
        # сходить в таблицу Users и найти записи по заданному полю с заданным значением. Вернет массив словарей.
        # например, найти Воробьева можно запросом get_users('account_name', 'ymvorobevda')
        # всех админов - запросом get_users('admin', 1)
        logger.info(f'get_users {field} = {value}')
        result = []
        try:
            self.db.connect(reuse_if_open=True)
            if field in ('tg_login', 'account_name'):
                db_users = Users.select().where(fn.Lower(getattr(Users, field)) == fn.Lower(value))
            else:
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
        # например, найти Воробьева можно запросом get_users('account_name', 'ymvorobevda')
        # всех админов - запросом get_users('admin', 1)
        users_array = []
        try:
            logger.info('Search users by fullname for %s', full_name)
            self.db.connect(reuse_if_open=True)
            if (type(full_name) == str):
                full_name = re.split(' ', value)

            full_name = [name.replace('ё', 'е') for name in full_name]

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
            db_users = await self.get_users('account_name', account_name)
            users_array.append(db_users) if len(db_users) > 0 else logger.info('Nothing found in Users for %s as account_name', account_name)

            db_users = await self.get_users('tg_login', account_name)
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
        except Exception as e:
            logger.exception('exception in db set users %s', str(e))
        finally:
            self.db.close()

    async def get_duty(self, duty_date) -> list:
        # Сходить в таблицу xerxes.duty_list за дежурными на заданную дату
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            db_query = Duty_List.select().where(Duty_List.duty_date == duty_date)
            for v in db_query:
                result.append((vars(v))['__data__'])
            logger.debug('get duty for %s %s', duty_date, result)
            return result
        except Exception as e:
            logger.exception('exception in db get duty %s', str(e))
        finally:
            self.db.close()


    async def get_duty_in_area(self, duty_date, area) -> list:
        # Сходить в таблицу xerxes.duty_list за дежурными на заданную дату и зону ответственности
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            db_query = Duty_List.select().where(Duty_List.duty_date == duty_date, Duty_List.area.startswith(area))
            for v in db_query:
                result.append((vars(v))['__data__'])
            logger.info('get duty in area for %s %s %s', duty_date, area, result)
            return result
        except Exception as e:
            logger.exception('exception in db get duty in area %s', str(e))
        finally:
            self.db.close()


    async def get_duty_personal(self, duty_date, tg_login) -> list:
        # Сходить в таблицу xerxes.duty_list за расписание дежурств конкретного администратора
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            logger.info('get duty personal for %s %s', duty_date, tg_login)
            db_query = (Duty_List
                        .select()
                        .where(Duty_List.duty_date >= duty_date, Duty_List.tg_login == tg_login)
                        .order_by(Duty_List.duty_date.asc()))
            for v in db_query:
                result.append((vars(v))['__data__'])
            logger.info('get duty for %s %s %s', duty_date, tg_login, result)
            return result
        except Exception as e:
            logger.exception('exception in db get duty personal tg_login %s', str(e))
        finally:
            self.db.close()

    def get_parameters(self, name) -> list:
        # Сходить в parameters
        logger.debug('get parameters %s ', name)
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            db_query = Parameters.select().where(Parameters.name == name)
            for v in db_query:
                result.append((vars(v))['__data__'])
            logger.debug('get parameters for %s %s', name, result)
            return result
        except Exception as e:
            logger.exception('exception in get parameters %s', e)
        finally:
            self.db.close()

    def set_parameters(self, name, value):
        # Записать в parameters
        logger.info('set parameters %s %s ', name, value)
        try:
            self.db.connect(reuse_if_open=True)
            db_rec, _ = Parameters.get_or_create(name=name)
            db_rec.value = value
            db_rec.save()
        except Exception as e:
            logger.exception('exception in set parameters %s', e)
        finally:
            self.db.close()

    async def delete_user_subscription(self, account_name, subscription):
        # Выставить в users_subscription подписку пользователя
        logger.debug('delete user subscription %s %s', account_name, subscription)
        try:
            self.db.connect(reuse_if_open=True)
            query = User_Subscriptions.delete().where(
                fn.Lower(User_Subscriptions.account_name) == fn.Lower(account_name), User_Subscriptions.subscription == subscription)
            query.execute()
        except Exception as e:
            logger.exception('exception in delete user subscription %s', e)
        finally:
            self.db.close()

    async def set_user_subscription(self, account_name, subscription):
        # Выставить в users_subscription подписку пользователя
        logger.debug('set user subscription %s ', account_name)
        try:
            self.db.connect(reuse_if_open=True)
            db_rec, _ = User_Subscriptions.get_or_create(account_name=fn.Lower(account_name), subscription=subscription)
            db_rec.save()
        except Exception as e:
            logger.exception('exception in set user subscription %s', e)
        finally:
            self.db.close()

    async def set_user_tg_id(self, tg_login, tg_id):
        # Выставить tg_id для данного чата (если отправленно из группового чата, выставит id чата, если найдет его)
        logger.info(f'set user tg_id {tg_login} {tg_id}')
        try:
            self.db.connect(reuse_if_open=True)
            result = (Users
                     .update(tg_id = tg_id)
                     .where(fn.Lower(Users.tg_login) == fn.Lower(tg_login)))
            result.execute()
        except Exception as e:
            logger.exception('exception in set user tg_id %s', e)
            return result
        finally:
            self.db.close()

    async def get_user_subscriptions(self, account_name) -> list:
        # Вернуть все подписки конкретного пользователя
        logger.debug('get user subscriptions %s ', account_name)
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            db_query = User_Subscriptions.select().where(fn.Lower(User_Subscriptions.account_name) == fn.Lower(account_name))
            for v in db_query:
                if ((vars(v))['__data__']):
                    result.append((vars(v))['__data__']['subscription'])
            logger.info('get user subscriptions for %s %s', account_name, result)
            return result
        except Exception as e:
            logger.exception('exception in get user subscriptions %s', e)
        finally:
            self.db.close()

    async def get_all_users_with_subscription(self, subscription) -> list:
        # Вернуть список пользователей (account_name) с конкретной подпиской
        logger.debug('get all users with subscription %s ', subscription)
        try:
            self.db.connect(reuse_if_open=True)
            result = []
            db_query = (Users.select()
                             .join(User_Subscriptions, on=(fn.Lower(User_Subscriptions.account_name) == fn.Lower(Users.account_name)))
                             .where(User_Subscriptions.subscription == subscription))
            for v in db_query:
                if ((vars(v))):
                    result.append((vars(v))['__data__'])
            return result
        except Exception as e:
            logger.exception('exception in get all users with subscription %s', e)
        finally:
            self.db.close()


    def get_last_success_app_version(self, app_name, offset):
        # Вернет версию компоненты, успешно выехавшую на бой, отступив на offset релизов. 
        # Последня - это offset=0, предпоследняя - offset=1. Для роллбека
        try:
            result = ''
            self.db.connect(reuse_if_open=True)
            db_result = (Releases_List
                        .select(Releases_List.app_version)
                        .where(Releases_List.app_name == app_name, Releases_List.resolution == 'Выполнен')
                        .order_by(Releases_List.id.desc())
                        .offset(offset)
                        .limit(1))
            for r in db_result:
                if r.app_version:
                    result = r.app_version
                else:
                    result = ''
            return result
        except Exception as e:
            logger.exception('exception in get last success app version %s', e)
            return result
        finally:
            self.db.close()


    def get_last_deploy_task_number(self, app_name):
        # Вернет номер последней таски из таблицы релизов
        try:
            result = ''
            self.db.connect(reuse_if_open=True)
            db_result = (Releases_List
                        .select(Releases_List.jira_task)
                        .where(Releases_List.app_name == app_name, Releases_List.resolution != 'None')
                        .order_by(Releases_List.id.desc())
                        .limit(1))
            for r in db_result:
                if r.jira_task:
                    result = r.jira_task
                else:
                    result = ''
            return result
        except Exception as e:
            logger.exception('exception in get last deploy task number %s', e)
            return result
        finally:
            self.db.close()


    def get_last_success_app_version(self, app_name, offset=0):
        # Вернет версию компоненты, успешно выехавшую на бой, отступив на offset релизов. 
        # Последня - это offset=0, предпоследняя - offset=1. Для роллбека
        try:
            result = ''
            self.db.connect(reuse_if_open=True)
            db_result = (Releases_List
                        .select(Releases_List.app_version)
                        .where(Releases_List.app_name == app_name, Releases_List.resolution == 'Выполнен')
                        .order_by(Releases_List.id.desc())
                        .offset(offset)
                        .limit(1))
            for r in db_result:
                if r.app_version:
                    result = r.app_version
                else:
                    result = ''
            return result
        except Exception as e:
            logger.exception('exception in get last success app version %s', e)
            return result
        finally:
            self.db.close()