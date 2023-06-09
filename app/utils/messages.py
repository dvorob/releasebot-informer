#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Коллекция сообщений
"""
help_common = f'Привет, <b>%s</b>! :raised_hand:\n' \
    f'\nЧтобы начать со мной взаимодействовать, нужно быть сотрудником компании.\n' \
    f'Если ты с нами, скорее всего, мы уже знакомы. Проверить это можно, спросив меня:\n' \
    f'<b>/who мой_никнейм</b> (вместо мой_никней можно указать логин в ТГ, корпоративную учетку или имя (полное) с фамилией).\n' \
    f'Если в ответе ты видишь корректный логин, всё Ок.\n' \
    f'Если Telegram ID не заполнен, нажми <u><b>/start</b></u> .\n' \
    f'Во всех остальных случаях обратись к администраторам группы Admsys.\n' \
    f'\n:point_right: Вот список всего, что я умею:\n' \
    f'<u>/duty </u><b>N</b> -- покажет дежурных через N дней; N задавать необязательно, по умолчанию отобразятся деурные на сегодня.\n' \
    f'<u>/who </u><b>username</b> -- найдет инфо о пользователе; работает с ТГ-логином, аккаунтом или почтой.\n' \
    f'<u>/meet (/timetable) </u><b>N</b> -- расписание вашего календаря через N дней; N задавать необязательно,' \
    f'по умолчанию показывает расписание на сегодня. Как включить читайте здесь - ' \
    f'https://wiki.yooteam.ru/display/admins/ReleaseBot.ReleaseMaster#ReleaseBot.ReleaseMaster.\n' \
    f'<u>/app </u><b>app_name</b> -- инфа по параметрам выкладки приложения из БД бота. Если инфы нет - бот ничего не покатит.\n' \
    f'<u>/team </u><b>КОМАНДА</b> -- состав команды разработчиков; вытягивается из TeamTransition.\n' \
    f'\n:point_right: Описание кнопок:\n' \
    f'<u><b>Дежурные</b></u> -- показать дежурных админов.\n' \
    f'<u><b>Релизная доска</b></u> -- открыть релизную доску Admsys.\n' \
    f'<u><b>Документация</b></u> -- открыть Wiki с документацией по боту.\n' \
    f'<u><b>Логи бота</b></u> -- открыть Kibana с логами бота.\n' \
    f'<u><b>Админское меню</b></u> -- админское меню, доступно только администраторам.\n' \
    f'<u><b>Вернуть релиз в очередь</b></u> -- вернет список Jira-тасок, которые можно вернуть в начало релизной очереди.\n' \
    f'<u><b>Подписки и уведомления</b></u> -- подписаться на все уведомления от бота.\n' \
    f'Там же можно и отписаться от уведомлений.\n' \
    f'<b>Важно:</b> на персональные уведомления (о своих релизах) подписывться не нужно -- они работают по умолчанию.\n' \
    f'<u><b>Краткая инфа с релизной доски</b></u> -- покажет статистику о текущем состоянии релизной доски.\n' \
    f'<u><b>Расширенная инфа с релизной доски</b></u> -- то же, но в расширенном варианте.\n'

help_admin = f'\n:raised_hand: <u>Админские команы</u>:' \
    f'\n<u>/where_app </u><b>app_name</b> -- найти расположение приложения. Можно передать shiro, ' \
    f'iva-back-shiro1 и комбинации через пробел.' \
    f'\n<u>/app </u><b>app_name</b> -- инфа по приложению из БД бота (то, что он получает из metaconfig.yaml). ' \
    f'Если инфы нет - бот ничего не покатит.' \
    f'\n<u>/lock </u><b>app_name</b> -- /lock shiro залочит выкладки приложений. ' \
    f'Меняет значение bot_enabled = false (оно же есть в metaconfig.yaml, но истина - в БД).' \
    f'\n<u>/unlock </u><b>app_name</b> -- /unlock shiro, соответственно, запустит.' \
    f'\n<u>/show_locks</u> -- вернёт список заблокированных для выкладки приложений.'

main_menu = f'Отправьте /help, чтобы узнать, что я умею.\n' \
     f'Ниже :point_down: меню, но это далеко не всё.'

spam = f'Привет! :raised_hand:\n' \
    f'Я переехал на свою внутреннюю базу данных пользователей.\n' \
    f'Все телеграм-логины и id (есть и такая сущность), которые мне были известны, тоже переехали в неё.\n' \
    f'Если вы получили это сообщение -- у вас всё в порядке и уведомляния работают.\n' \
    f'Если кому-то из ваших коллег не приходят уведомления, отправьте им эту инструкцию:\n' \
    f'--------------------------\n' \
    f'1. Спросите у меня <b>/who "nickname" </b>,\n' \
    f'(вместо "nickname" можно подставить тг-логин, AD-логин или корпоративную почту).\n' \
    f'Если я вас узнаю, я верну сообщение с заполненными параметрами, среди которых должны быть заполнены:\n' \
    f'<b>Telegram Login</b> и <b>Telegram ID </b>:\n' \
    f'2. Если что-то среди этих параметров не заполнено, нажмите <b>/start</b> и затем спросите <b>/who ...</b> еще раз.\n' \
    f'3. Если это не помогло, зайдите, пожалуйста, в Диму Воробьёва -- @dvorob .\n' \
    f'--------------------------\n' \
    f'Хорошего дня!\n'

timetable_error = 'Доброго дня, {}. Спешу сообщить вам, что что-то пошло не так.\nВероятно, вы не выдали доступ до своего календаря. ' \
    'Подробнее читайте <a href="https://wiki.yooteam.ru/display/admins/ReleaseBot.ReleaseMaster#ReleaseBot.ReleaseMaster">здесь</a>'

rl_board_empty = 'Я не смог найти тасок на релизной доске'

duty_morning_hello = '<strong>Приветствую!</strong>\n' \
    f'Сейчас <strong>%s</strong> утра.\n' \
    f'Посмотреть, кто сегодня дежурит после 10:00 можно командой ' \
    f'<strong>/duty 1</strong>.\n\n'


quotes = ['Когда не знаешь, что делать, делай что должно и будь что будет. (с) Сенека',
    'Без товарища никакое счастье не радует. (с) Сенека',
    'Мы на многое не отваживаемся не потому, что оно трудно; оно трудно именно потому, что мы на него не отваживаемся. (с) Сенека',
    'Величие некоторых дел состоит не столько в размерах, сколько в своевременности их. (с) Сенека',
    'Вечного нет ничего, да и долговечно тоже немногое. (с) Сенека',
    'Кто не знает, в какую гавань плыть, для того нет попутного ветра. (с) Сенека',
    'Цезарю многое непозволительно именно потому, что ему дозволено всё. (с) Сенека',
    'Необходимое всегда легко приобрести. И только для избытков приходиться трудиться в поте лица. (с) Сенека',
    'Всюду, где можно жить, можно жить хорошо. (с) Марк Аврелий',
    'Несправедливость не всегда связана с каким-нибудь действием: часто она состоит именно в бездействии. (с) Марк Аврелий',
    'Наша жизнь есть то, что мы думаем о ней. (с) Марк Аврелий',
    'Жить каждый день так, как если бы он был последним, никогда не суетиться, никогда не быть равнодушным, никогда не принимать театральные позы - вот совершенство характера. Наша жизнь - это то, во что её превращают наши мысли. (с) Марк Аврелий',
    'Кто не знает, что такое мир, не знает, где он сам… (с) Марк Аврелий',
    'Если вас раздражает некий предмет, то виноват в этом не он сам, а ваше суждение о нём. И в ваших силах изменить это суждение. (с) Марк Аврелий',
    'Если бы ты видел, из какого источника текут людские суждения и интересы, то перестал бы добиваться одобрения и похвалы людей. (с) Марк Аврелий',
    'Пусть дела твои будут такими, какими бы ты хотел их вспомнить на склоне жизни. (с) Марк Аврелий',
    'Надо покорять умом то, что нельзя одолеть силой. (с) Марк Аврелий',
    'Всё настоящее - мгновение вечности. (с) Марк Аврелий',
    'Во-первых, не делай ничего без причины и цели. Во-вторых, не делай ничего, что бы не клонилось на пользу обществу. (с) Марк Аврелий',
    'Ни один человек не счастлив, пока он не считает себя счастливым. (с) Марк Аврелий',
    'Свободный ум требует оснований, другие же — только веры. (c) Ницше',
    'Быть великим — значит давать направление. (c) Ницше',
    'Нужно носить в себе ещё хаос, чтобы быть в состоянии родить танцующую звезду. (c) Ницше',
    'Я ненавижу людей, не умеющих прощать. (c) Ницше',
    'Стремление к величию выдаёт с головой: кто обладает величием, тот стремится к доброте. (c) Ницше',
    'Кто сражается с чудовищами, тому следует остерегаться, чтобы самому при этом не стать чудовищем. И если ты долго смотришь в бездну, то бездна тоже смотрит в тебя. (c) Ницше',
    'Я не доверяю всем систематикам и сторонюсь их. Воля к системе есть недостаток честности. (c) Ницше',
    'Без музыки жизнь была бы заблуждением. (c) Ницше',
    'Весь мир верит в это; но чему только не верит весь мир! (c) Ницше']

bot_was_stopped_manually = ":warning: Релизный поезд остановлен в ручном режиме; остановил %s.\n" \
    "Пожалуйста, воздержитесь от вопросов о том, зачем это сделано, если можете позволить себе подождать" \
    " - администраторы не делают этого без причины. Релизный поезд будет запущен, как только это станет возможным. " \
    "Если ваша задача критической срочности, обратитесь к дежурному от Мониторинга, возможно на инфраструктуре заведен Инцидент. " \
    "Если его ещё нет, и проблема длится более 1 часа, попросите Мониторинг завести задачу и взять её на контроль."

bot_was_started_manually = ":railway_car: Релизный поезд запущен; запустил %s. \nРелизы катятся в штатном режиме. Спасибо, что продолжаете пользоваться нашими услугами."

tg_release_in_status_open = '\n :yellow_circle: Есть релиз в статусе Open. Релизный бот не работает с этим статусом. ' \
                            'Вероятно, релиз ожидает <a href="%s">завершения INT/LOAD-приёмок</a>:\n '

tg_look_for_details_on_board = '\n Детали можно найти на <a href="%s/secure/RapidBoard.jspa?rapidView=1557">релизной доске</a>'

tg_rl_in_progress = '\n :yellow_circle: <a href="%s/browse/%s">%s</a> Компонент в процессе выкладки на доске'

tg_rl_queue_is_free = '\n :green_circle: Релизная очередь приложения свободна'  