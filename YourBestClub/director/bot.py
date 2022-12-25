import json
import os
import re
from datetime import datetime
from pathlib import Path
from time import time, sleep

import requests
from django.db.models import Sum
from django.shortcuts import redirect
from django.utils import timezone
from keyboa import Keyboa, Button
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo

from telebot import TeleBot
from django.conf import settings
from django.http import JsonResponse

from YourBestClub.settings import BASE_HOST, TELEGRAM_BOT_URI
from director.models import Club, Director, Trainer, Student, ClubGroup, Payment
from director.models import Lesson, Participant
# from finances.models import DirectorPay
from news.models import Post
from . import messages as mes
from .bot_utils import check_tg_id, find_user_data

bot = TeleBot(settings.TELEGRAM_BOT_API_KEY, parse_mode='HTML')
ENTER_CLUB_ID = {}

valid_FIO_pattern = re.compile(r"^[а-яА-ЯёЁa-zA-Z]+ [а-яА-ЯёЁa-zA-Z]+ ?[а-яА-ЯёЁa-zA-Z]+$")
valid_Phone_pattern = re.compile(r"^((\+7|7|8)+([0-9]){10})$")
valid_BD_pattern = re.compile(r"^(0?[1-9]|[12][0-9]|3[01]).(0?[1-9]|1[012]).((19|20)\d\d)+$")


def validate(name: str):
    return bool(valid_FIO_pattern.match(name))


def validate_phone(phone: str):
    return bool(valid_Phone_pattern.match(phone))


def validate_birthday(bd: str):
    return bool(valid_BD_pattern.match(bd))


# _____________________________________________________________________________________________


def main_menu(chat_id, user_type):
    menu = []
    text = ''
    if user_type == 'director':
        menu = [["🏫 Мои клубы", {"💸 Финансы": 'director_finance'}],
                [{"⚙️ Настройки": 'director_settings'}, {"💌 Новости": 'director_news'}]]
        text = '<b>Личный кабинет директора</b>'
    if user_type == 'trainer':
        menu = [["🏫 Мои группы", {"📋 Расписание": 'trainer_schedule'}],
                [{"⚙️ Настройки": 'trainer_settings'}, {"💌 Новости": 'trainer_news'}]]
        text = '<b>Личный кабинет преподавателя</b>'
    if user_type == 'student':
        menu = [[{"📋 Расписание": 'student_schedule'}, {"💸 Финансы": 'student_finance'}],
                [{"⚙️ Настройки": 'student_settings'}, {"💌 Новости": 'student_news'}]]
        text = '<b>Личный кабинет ученика</b>'

    keyboard = Keyboa(items=menu)
    msg = bot.send_message(chat_id, text, reply_markup=keyboard())


def send_private_message(chat_id, message):
    msg = bot.send_message(chat_id, message)
    with open(f'{chat_id}.txt', 'a', encoding='utf8') as f:
        f.write(f'{msg.message_id}\n')
    return True


def clear_chat(chat_id, msg_id):
    bot.delete_message(chat_id, msg_id)
    with open(f'{chat_id}.txt', 'r', encoding='utf8') as f:
        while True:
            line = f.readline()
            if not line:
                break
            bot.delete_message(chat_id, int(line.strip()))
    path = f'{chat_id}.txt'
    try:
        os.remove(path)
    except:
        print('Path is not a file')
    return True


def broadcast(recipients, mes_data):
    text = f"<b>{mes_data['subject']}</b>\n\n{mes_data['text']}"
    if mes_data['image'] is None:
        for recipient in recipients:
            bot.send_message(recipient, text)
    else:
        print(mes_data['image'])
        with open(mes_data['image'], 'rb') as image:
            photo = image.read()
            for recipient in recipients:
                bot.send_photo(recipient, photo, caption=text)


def lesson_remainder(recipients, lesson_data):
    menu = []
    text = f'Привет! ✨ Напоминаем: сегодня в {lesson_data["time"]} в группе {lesson_data["group"]} начнётся занятие!'
    menu.append([{'🚷 Пропустим': f'participant_status_false&{lesson_data["pk_participant"]}'}])
    keyboard = Keyboa(items=menu)
    for recipient in recipients:
        msg = bot.send_message(recipient, text, reply_markup=keyboard())
    return True


def lesson_individuals_remainder(recipients, lesson_data):
    menu = []
    text = f'Привет! ✨ Напоминаем: сегодня в {lesson_data["time"]} состоится индивидуальное занятие!'
    menu.append([{'🚷 Пропустим': f'participant_status_false&{lesson_data["pk_participant"]}'}])
    keyboard = Keyboa(items=menu)
    for recipient in recipients:
        msg = bot.send_message(recipient, text, reply_markup=keyboard())
    return True


def trainer_remainder(recipient, lesson_data):
    menu = []
    students = "\n".join(lesson_data["participants"])
    if lesson_data.get("group"):
        text = f'Привет! ✨ Напоминаем: сегодня в {lesson_data["time"]} состоится занятие у группы {lesson_data["group"]}! ' \
               f'Состав:\n\n{students}'
    else:
        text = f'🔔 <i>Cегодня в {lesson_data["time"]} состоится индивидуальное занятие для: \n\n{students}</i>'
    print(text, recipient)
    msg = bot.send_message(recipient, text)
    return True


# _____________________________________________________________________________________________


# @csrf_exempt
def get_update(request):
    if request.method == 'POST':
        with open('tg_log.txt', 'a', encoding='utf8') as f:
            f.write(f'TUT znaxchit POST\n{os.listdir(path=".")}')
        if request.headers.get('Content-Type') == 'application/json':
            with open('tg_log.txt', 'a', encoding='utf8') as f:
                f.write(f'TUT znachit application/json\n')
            upd = json.loads(request.read().decode('utf-8'))
            update = Update.de_json(upd)
            with open('tg_log.txt', 'a', encoding='utf8') as f:
                f.write(f'{update}\n')
            bot.process_new_updates([update])

        return JsonResponse({'ok': True, 'status': 200})
    else:
        return redirect('/login/')


# _______________________________________Зарегистрировался ТРЕНЕР _____________________________________


def trainer_registration(club, trainer):
    text = f"🔔 <i> В {club} зарегистрировался {trainer} в должности тренера! Необходимо проставить оплату и оклад.</i>"
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Заполнить данные',
                                  web_app=WebAppInfo(url=f'{BASE_HOST}/trainer/{trainer.pk}/edit/'))
    markup.add(button)
    bot.send_message(club.director.tgID, text, reply_markup=markup)


# _____________________________________________________________________________________________


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if check_tg_id(message.chat.id):
        menu = []
        send_login = False
        user_type_str, club_title, group_str = '', '', ''
        try:
            command_type = message.text.split(' ')[-1][0]
            user_pk = message.text.split(' ')[-1][1:-1]
            user_type = message.text.split(' ')[-1][-1]

            # ================================= ПРИКРЕПЛЕНИЕ TG_ID ====================================
            if command_type == 'c' and user_type == 'd':
                bot.delete_message(message.chat.id, message.message_id)
                director = Director.objects.get(pk=int(user_pk))
                user_type_str = 'директора'
                if not director.tgID:
                    director.tgID = message.chat.id
                    director.save()

                msg = bot.send_message(message.chat.id, mes.DIR_REG_OK.replace('#{type_u}', user_type_str))
                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton(text='Авторизация',
                                              web_app=WebAppInfo(url=f'{BASE_HOST}/login_tg/{msg.message_id}/'))
                markup.add(button)
                msg = bot.send_message(message.chat.id, '⚠️ Авторизуйтесь, для доступа ко всем функциям 👇🏻',
                                       reply_markup=markup)
                print(msg.message_id)
                with open(f'{message.chat.id}.txt', 'a', encoding='utf8') as f:
                    f.write(f'{msg.message_id}\n')

                return True

            if command_type == 'c' and user_type == 't':
                user_type_str = 'преподавателя'
                trainer = Trainer.objects.get(pk=int(user_pk))
                club_title = trainer.club.title
                if not trainer.tgID:
                    trainer.tgID = message.chat.id
                    trainer.save()

                text = mes.CREATE_USER.replace('#{type_u}', user_type_str).replace('#{club}', f' в {club_title}')
                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton(text='Создать логин и пароль', web_app=WebAppInfo(
                    url=settings.BASE_HOST + '/rtruftg/' + str(message.chat.id)))
                markup.add(button)
                msg = bot.send_message(message.chat.id, text, reply_markup=markup)
                with open(f'{message.chat.id}.txt', 'a', encoding='utf8') as f:
                    f.write(f'{msg.message_id}\n')
                return True

            if command_type == 'c' and user_type == 's':
                user_type_str = 'ученика'
                student = Student.objects.get(pk=int(user_pk))
                club_title = student.group.club.title
                if not student.tgID:
                    student.tgID = message.chat.id
                    student.save()
                text = mes.CREATE_USER.replace('#{type_u}', user_type_str).replace('#{club}', f' в {club_title}')
                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton(text='Создать логин и пароль', web_app=WebAppInfo(
                    url=settings.BASE_HOST + '/rtruftg/' + str(message.chat.id)))
                markup.add(button)
                msg = bot.send_message(message.chat.id, text, reply_markup=markup)
                with open(f'{message.chat.id}.txt', 'a', encoding='utf8') as f:
                    f.write(f'{msg.message_id}\n')
                return True
            # ==========================================================================================

            # ================================= РЕГИСТРАЦИЯ ====================================
            if command_type == 'r':
                url, text = '', ''
                club = Club.objects.get(pk=int(user_pk))
                if user_type == 't':
                    text = mes.INVITE.replace('#{type_u}', 'преподавателя').replace('#{club}', f'{club.title}')
                    url = settings.BASE_HOST + f'/club/{int(club.pk)}/add-trainer/{message.chat.id}/'
                if user_type == 's':
                    text = mes.INVITE.replace('#{type_u}', 'ученика').replace('#{club}', f'{club.title}')
                    url = settings.BASE_HOST + f'/club/{int(club.pk)}/group/0/add-student/{message.chat.id}/'

                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton(text='Зарегистрироваться', web_app=WebAppInfo(url=url))
                markup.add(button)
                msg = bot.send_message(message.chat.id, text, reply_markup=markup)
                return True

        except:
            return bot.send_message(message.chat.id, f'Работа с ботом невозможна без регистрации на сайте '
                                                     f'{BASE_HOST}\n\nЕсли регистрация пройдена — '
                                                     f'воспользуйтесь командой /menu')
    else:
        user_type, user_data = find_user_data(message.chat.id)
        if user_data and user_type:
            main_menu(message.chat.id, user_type)
        else:
            return bot.send_message(message.chat.id,
                                    f'Ваш Телеграм уже привязан к аккаунту. Закончите регистрацию на сайте {BASE_HOST}')


# **************************** Обработка нажатий на кнопки ********************************************
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call, **kwargs):
    print('call.data: ', call.data)
    menu = []

    # ================================= ОСНОВНОЕ МЕНЮ ЛК ====================================
    if call.data.startswith("mainmenu_"):
        user_type = call.data.split('_')[1]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        main_menu(call.message.chat.id, user_type)
        return True

    # ================================= ОТМЕНА ПОСЕЩЕНИИЯ ====================================
    if call.data.startswith("participant_status_false"):
        pk_participant = call.data.split('&')[1]
        participant = Participant.objects.get(pk=int(pk_participant))
        participant.status = False
        participant.save()
        msg = bot.send_message(call.message.chat.id,
                               f'✔️ Участие в занятии {timezone.datetime.strftime(participant.lesson.dt, "%d.%m.%Y %H:%M")} <b>отменено</b>!')
        return True

    # ================================= КНОПКИ ОСНОВНОГО МЕНЮ ДИРЕКТОРА ====================================
    if call.data == "🏫 Мои клубы":
        clubs = Director.objects.get(tgID=call.message.chat.id).club_set.all()
        if clubs:
            for club in clubs:
                menu.append({f'{club.title}, {club.city}': f'club_{club.pk}'})
            keyboard1 = Keyboa(items=menu, items_in_row=2).keyboard
            button_footer = [
                {'text': '➕ Добавить клуб', 'web_app': WebAppInfo(url=settings.BASE_HOST + '/club/add-club/')},
                {'◀️ Назад': 'mainmenu_director'}]
            keyboard2 = Keyboa(items=button_footer).keyboard
            keyboard = Keyboa.combine(keyboards=(keyboard1, keyboard2))
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text='Выберите клуб 👇🏻', reply_markup=keyboard)
        else:
            markup = InlineKeyboardMarkup()
            button = InlineKeyboardButton(text='➕ Добавить клуб',
                                          web_app=WebAppInfo(url=settings.BASE_HOST + '/club/add-club/'))
            button_back = InlineKeyboardButton(text='◀️ Назад', callback_data=f'mainmenu_director')
            markup.add(button).add(button_back)
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text='🏫 В этом разделе будут находиться все ваши клубы.\n\n'
                                             'Добавляйте и наслаждайтесь сервисом!',
                                        reply_markup=markup)
        return True

    # =================================  ДИРЕКТОР ФИНАНСЫ ====================================
    if call.data == 'director_finance':
        user = Director.objects.get(tgID=call.message.chat.id)
        balance = Payment.objects.filter(user__director=user, is_personal=False).aggregate(Sum('amount'))['amount__sum']
        balance = balance if balance is not None else 0
        menu = [
            [{'text': "💵 Вывести", 'web_app': WebAppInfo(url=f'{BASE_HOST}/withdrawal/')},
             {'text': '💸 Пополнить', 'web_app': WebAppInfo(url=f'{BASE_HOST}/refill/')}],
            [{'text': '➕ Добавить расходы', 'web_app': WebAppInfo(url=f'{BASE_HOST}/club/0/finances/add_personal_payment/')},
             {'◀️ Назад': 'mainmenu_director'}]
        ]
        keyboard = Keyboa(items=menu)
        incoming = \
            Payment.objects.filter(user__director=user, amount__gt=0, is_personal=False).aggregate(Sum('amount'))[
                'amount__sum']
        expenses = \
            Payment.objects.filter(user__director=user, amount__lt=0, is_personal=False).aggregate(Sum('amount'))[
                'amount__sum']
        personal = Payment.objects.filter(user__director=user, amount__lt=0, is_personal=True).aggregate(Sum('amount'))[
            'amount__sum']
        incoming = incoming if incoming is not None else 0
        expenses = expenses if expenses is not None else 0
        personal = personal if personal is not None else 0
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              text=f'<b>💸 Финансы</b>\n\n'
                                   f'💎 Баланс: <b>{balance}₽</b>\n\n'
                                   f'Общая статистика:\n<i>Доходы:</i> <b>{incoming}₽</b>, <i>Расходы:</i> <b>{expenses}₽</b>, '
                                   f'<i>Личные:</i> <b>{personal}₽</b>\n'
                                   f'--------------------\n'
                                   f'<b>Итого: {incoming + expenses + personal}₽</b>\n',
                              reply_markup=keyboard()
                              )
        return True
    # =================================  ДИРЕКТОР НАСТРОЙКИ ====================================
    if call.data == "director_settings":
        menu.append([{'◀️ Назад': 'mainmenu_director'}])
        keyboard = Keyboa(items=menu)
        msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                    text='🤷🏼‍♂️ Здесь должны быть какие-то настройки, но пока ничего нет потому что я еще не придумал какие...',
                                    reply_markup=keyboard())

    # =================================  ДИРЕКТОР НОВОСТИ ====================================
    if call.data == "director_news":
        menu.append([{'◀️ Назад': 'mainmenu_director'}])
        keyboard = Keyboa(items=menu)
        posts = Post.objects.all()
        text = ''
        if posts:
            for news in posts:
                text += f'<b>{news.title}</b>\n\n{news.content[:100]}...\n\n<a href={news.get_absolute_url()}>Подробнее...</a>'
        else:
            text += '🤷🏼‍♂️ Здесь должны быть новости... Но их пока нет!'
        msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                    text=text, reply_markup=keyboard())

    # **************************** Обработка нажатий на кнопки club_ ********************************************
    if call.data.startswith('club_'):
        menu = []
        if '&' not in call.data:
            club_data = call.data.split('_')
            club = Club.objects.filter(pk=int(club_data[1])).first()
            menu = [
                [{"👨🏼‍🏫 Сотрудники": f'club_{club.pk}&trainers'}, {"🗂 Группы": f'club_{club.pk}&groups'}],
                [{"👫 Ученики": f'club_{club.pk}&students'}, {"📆 Расписание": f'club_{club.pk}&schedule'}],
                [{"📊 Статистика": f'club_{club.pk}&statistic'}, {"💸 Финансы": f'club_{club.pk}&finances'}],
                [{'text': "✉️ Связь", 'web_app': WebAppInfo(url=f'{BASE_HOST}/club/{club.pk}/mailing/')},
                 {"🪄 Вклад в будущее": f'club_{club.pk}&donation'}],
                [{'text': '📝 Редактировать', 'web_app': WebAppInfo(url=f'{BASE_HOST}/club/{club.pk}/edit/')},
                 {'🎉 Мероприятия': f'club_{club.pk}&events'}],
                [{'◀️ Назад': 'mainmenu_director'}, ]
            ]
            keyboard = Keyboa(items=menu)
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=f'🏫 <b>{club.title}</b>, {club.city}.\n<i>{club.description}</i>',
                                        reply_markup=keyboard())

        else:
            club_data = call.data.split('_')
            pk_club = int(club_data[1].split('&')[0])
            club = Club.objects.filter(pk=pk_club).first()
            choice = club_data[1].split('&')[1]

            if choice == 'trainers':
                warning = ''
                trainers = Trainer.objects.filter(club=club)
                url = settings.BASE_HOST + f'/club/{int(club.pk)}/trainer-add/'
                link = requests.get(f'https://clck.ru/--?url={TELEGRAM_BOT_URI}r{club.pk}t').text
                if trainers:
                    for trainer in trainers:
                        if trainer.user is None:
                            warning = '⚠️ '
                        menu.append({
                            f'{warning}{trainer.surname} {trainer.name[0]}.{trainer.soname[0]}.': f'trainer_{trainer.pk}'})
                    keyboard1 = Keyboa(items=menu, items_in_row=2).keyboard
                    button_footer = [
                        {'text': '➕ Добавить тренера', 'web_app': WebAppInfo(url=url)},
                        {'◀️ Назад': f'club_{club.pk}'}]
                    keyboard2 = Keyboa(items=button_footer).keyboard
                    keyboard = Keyboa.combine(keyboards=(keyboard1, keyboard2))

                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text=f'👨🏼‍🏫 {club.title}, тренера:\n\n'
                                                     f'🤗 Пригласить 👉🏻 <code>{link}</code>',
                                                reply_markup=keyboard)
                else:
                    markup = InlineKeyboardMarkup()
                    button = InlineKeyboardButton(text='➕ Добавить тренера', web_app=WebAppInfo(url=url))
                    button_back = InlineKeyboardButton(text='◀️ Назад', callback_data=f'club_{club.pk}')
                    markup.add(button).add(button_back)
                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text=f'🤷🏼‍♂️ В этом клубе еще не добавлены тренера...\n\n'
                                                     f'Вы можете добавить тренера через личный кабинет на сайте, '
                                                     f'нажав на кнопку внизу 👇🏻 '
                                                     f'Или просто скопируйте ссылку и отправьте ее тренеру, '
                                                     f'чтобы он зарегистрировался в <b>{club.title}</b> сам.\n\n'
                                                     f'👉🏻 <code>{TELEGRAM_BOT_URI}r{club.pk}t</code>',
                                                reply_markup=markup)

            if choice == 'groups':
                groups = ClubGroup.objects.filter(club=club)
                url = settings.BASE_HOST + f'/club/{int(club.pk)}/group-add/'
                if groups:
                    for group in groups:
                        menu.append({f'{group.title}': f'group_{group.pk}'})
                    keyboard1 = Keyboa(items=menu, items_in_row=2).keyboard
                    button_footer = [
                        {'text': '➕ Добавить группу', 'web_app': WebAppInfo(url=url)},
                        {'◀️ Назад': f'club_{club.pk}'}]
                    keyboard2 = Keyboa(items=button_footer).keyboard
                    keyboard = Keyboa.combine(keyboards=(keyboard1, keyboard2))
                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text=f'🗂 {club.title}, группы:',
                                                reply_markup=keyboard)
                else:
                    markup = InlineKeyboardMarkup()
                    button = InlineKeyboardButton(text='➕ Добавить группу', web_app=WebAppInfo(url=url))
                    button_back = InlineKeyboardButton(text='◀️ Назад', callback_data=f'club_{club.pk}')
                    markup.add(button).add(button_back)
                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text='🤷🏼‍♂️ В этом клубе еще не добавлены группы...',
                                                reply_markup=markup)

            if choice == 'students':
                students = Student.objects.filter(group__in=ClubGroup.objects.filter(club=club), is_deleted=False)
                warning = ''
                if students:
                    for student in students:
                        if student.user is None:
                            warning = '⚠️ '
                        if student.is_active:
                            menu.append(
                                {
                                    f'{warning}{student.surname} {student.name[0]}.{student.soname[0]}.': f'student_{student.pk}'})
                        else:
                            menu.append(
                                {
                                    f'⛔️ {student.surname} {student.name[0]}.{student.soname[0]}.': f'student_{student.pk}'})
                    menu.append({'◀️ Назад': f'club_{club.pk}'})
                    keyboard = Keyboa(items=menu, items_in_row=3)
                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text=f'👫 {club.title}, ученики:',
                                                reply_markup=keyboard())
                else:
                    menu.append({'◀️ Назад': f'club_{club.pk}'})
                    keyboard = Keyboa(items=menu, items_in_row=2)
                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text='🤷🏼‍♂️ В этом клубе еще не добавлены ученики...\n\n'
                                                     'Для добавления учеников - перейдите в <b>необходимую группу</b>.',
                                                reply_markup=keyboard())

            if choice == 'schedule':
                text = ''
                groups = ClubGroup.objects.filter(club=club)
                lessons_individuals = Lesson.objects.filter(is_group=False)
                filtered_lessons_individuals = []
                for lesson in lessons_individuals:
                    for participant in lesson.participant_set.all():
                        if participant.student.group in groups:
                            if lesson not in filtered_lessons_individuals:
                                filtered_lessons_individuals.append(lesson)
                if groups:
                    for group in groups:
                        lessons_group = Lesson.objects.filter(group=group)
                        if lessons_group:
                            text += f'<b>{group.title}</b>, групповые занятия:\n'
                            for lesson in lessons_group:
                                trainers = lesson.trainer.all()
                                trainers_str = ''
                                for trainer in trainers:
                                    trainers_str += f'{trainer}, '
                                text += f'{timezone.datetime.strftime(lesson.dt, "%d.%m.%Y %H:%M")} - {trainers_str[:-2]}\n'
                            text += f'\n'
                        else:
                            text += f'<b>{group.title}</b>, групповых занятий нет!\n'
                else:
                    text = f'<b>⚠️ Нет ни одной группы!</b>\n'
                text += '\n'
                if filtered_lessons_individuals:
                    for lesson in filtered_lessons_individuals:
                        students = ''
                        print('lesson', lesson)
                        for participant in lesson.participant_set.all():
                            if participant.student.soname not in students:
                                students += f'{participant.student.surname} {participant.student.name[0]}. {participant.student.soname[0]}., '
                        trainers = ''
                        for trainer in lesson.trainer.all():
                            trainers += f'{trainer.surname} {trainer.name[0]}. {trainer.soname[0]}., '
                        text += f'{timezone.datetime.strftime(lesson.dt, "%d.%m.%Y %H:%M")} - {students[:-2]} ({trainers[:-2]})\n'
                else:
                    text += f'<b> Индивидуальных занятий нет! </b>\n'

                menu.append({'◀️ Назад': f'club_{club.pk}'})
                text += f'\n💡 <i>Чтобы добавить расписание — перейдите в необходимую группу.</i>'
                keyboard = Keyboa(items=menu, items_in_row=2)
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=f'📆 <b>{club.title}</b>, расписание:\n\n{text}',
                                            reply_markup=keyboard())

            if choice == 'statistic':
                text = f'Здесь предполагается какая-то краткая статистика. Это как раз на подумать, {call.message.chat.first_name}...'
                menu.append({'◀️ Назад': f'club_{club.pk}'})
                keyboard = Keyboa(items=menu, items_in_row=2)
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=f'📊 {club.title}, статистика:\n\n{text}',
                                            reply_markup=keyboard())

            if choice == 'finances':
                menu = [
                    [{'text': '➕ Добавить расходы',
                      'web_app': WebAppInfo(url=f'{BASE_HOST}/club/{club.pk}/finances/add_personal_payment/')},
                     {'◀️ Назад': f'club_{club.pk}'}]
                ]
                keyboard = Keyboa(items=menu)
                incoming = Payment.objects.filter(club=club, amount__gt=0, is_personal=False).aggregate(Sum('amount'))['amount__sum']
                expenses = Payment.objects.filter(club=club, amount__lt=0, is_personal=False).aggregate(Sum('amount'))['amount__sum']
                personal = Payment.objects.filter(club=club, amount__lt=0, is_personal=True).aggregate(Sum('amount'))['amount__sum']
                incoming = incoming if incoming is not None else 0
                expenses = expenses if expenses is not None else 0
                personal = personal if personal is not None else 0
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text=f'<b>💸 <b>{club.title}</b>, Финансы</b>\n\n'
                                           f'<i>Доходы:</i> <b>{incoming}₽</b>, <i>Расходы:</i> <b>{expenses}₽</b>, '
                                           f'<i>Личные:</i> <b>{personal}₽</b>\n'
                                           f'--------------------\n'
                                           f'<b>Итого: {incoming + expenses + personal}₽</b>\n',
                                      reply_markup=keyboard()
                                      )

            if choice == 'mailing':
                menu = [{'👨‍👦‍👦 Всем': f'mailing_club_{club.pk}'}, {'👨🏼‍🏫 Тренерам': f'mailing_trainers_{club.pk}'},
                        {'🗂 Группе': f'mailing_group_{club.pk}'}, {'👫 Ученикам': f'mailing_students_{club.pk}'},
                        {'◀️ Назад': f'club_{club.pk}'}]
                keyboard = Keyboa(items=menu, items_in_row=2)
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=f'💸 {club.title}, рассылка:',
                                            reply_markup=keyboard())

            if choice == 'donation':
                text = f'Здесь предполагается какие то МОЩНЫЕ ПРИЗЫВЫ для доната. Это как раз тоже на очень подумать, {call.message.chat.first_name}...'
                menu.append({'◀️ Назад': f'club_{club.pk}'})
                keyboard = Keyboa(items=menu, items_in_row=2)
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=f'💸 {club.title}, вклад в будущее:\n\n{text}',
                                            reply_markup=keyboard())

            if choice == 'events':
                text = f'Здесь предполагается какие то мероприятия. Надо доработать, {call.message.chat.first_name}...'
                menu.append({'◀️ Назад': f'club_{club.pk}'})
                keyboard = Keyboa(items=menu, items_in_row=2)
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=f'💸 {club.title}, мероприятия:\n\n{text}',
                                            reply_markup=keyboard())

    # **************************** Обработка нажатий на кнопки trainer_ ********************************************
    if call.data.startswith('trainer_'):
        menu = []
        if '&' in call.data:
            pass
        else:
            mes_data = call.data.split('_')
            trainer = Trainer.objects.filter(pk=int(mes_data[1])).first()
            lessons = Lesson.objects.filter(is_group=True, trainer=trainer)
            groups_text = "Нет групп  "
            groups = []
            if lessons:
                groups_text = ''
                for lesson in lessons:
                    if lesson.group not in groups:
                        groups.append(lesson.group)
                        groups_text += f'{lesson.group.title}, '
            club = trainer.club
            statistic = 'Здесь какая то статистика 1.\nЗдесь какая то статистика 2.\nЗдесь какая то статистика 3.'

            if trainer.user is not None:
                button_footer = [
                    {'text': '📝 Редактировать', 'web_app': WebAppInfo(url=f'{BASE_HOST}/trainer/{trainer.pk}/edit/')},
                    {'◀️ Назад': f'club_{club.pk}&trainers'}]
                keyboard2 = Keyboa(items=button_footer).keyboard
                keyboard = Keyboa.combine(keyboards=(keyboard2,))
                text = f'<b>👨🏼‍🏫 {trainer}</b>\n\n📞 <a href="tel:{trainer.phone}">{trainer.phone}</a>\n' \
                       f'🗂 {groups_text[:-2]}\n📊 Статистика:\n{statistic}'
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=text, reply_markup=keyboard)
                return True
            else:
                button_footer = [{'◀️ Назад': f'club_{club.pk}&trainers'}]
                keyboard2 = Keyboa(items=button_footer).keyboard
                keyboard = Keyboa.combine(keyboards=(keyboard2,))
                text = f'⚠️ Сотрудник не завершил регистрацию! Отправьте ему ссылку для создания логина и пароля:\n\n' \
                       f'👉🏻 <code>{requests.get(f"https://clck.ru/--?url={TELEGRAM_BOT_URI}c{trainer.pk}t").text}</code>'
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=text, reply_markup=keyboard)
                return True

    # **************************** Обработка нажатий на кнопки group_ ********************************************
    if call.data.startswith('group_'):
        if '&' not in call.data:
            menu = []
            mes_data = call.data.split('_')
            group = ClubGroup.objects.filter(pk=int(mes_data[1])).first()
            club = group.club
            schedule = Lesson.objects.filter(is_group=True, group=group).order_by('dt')
            schedule_text = '<b>Расписание отсутствует!</b>'
            if schedule:
                schedule_text, trainers_str = '', ''
                for lesson in schedule:
                    for trainer in lesson.trainer.all():
                        if str(trainer) not in trainers_str:
                            trainers_str += str(trainer) + ', '
                    schedule_text += f"{timezone.datetime.strftime(lesson.dt, ' %d.%m.%Y %H:%M')} — {trainers_str[:-2]}\n"
            text = f"👨🏼‍🏫 {club.title}, <b>{group.title}</b>:\n\n" \
                   f"{schedule_text}\n"
            lessons_individuals = Lesson.objects.filter(is_group=False).filter(
                participant__student__in=Student.objects.filter(group=group))
            if lessons_individuals:
                for lesson in lessons_individuals:
                    students = ''
                    for participant in lesson.participant_set.all():
                        if participant.student.soname not in students:
                            students += f'{participant.student.surname} {participant.student.name[0]}. {participant.student.soname[0]}., '
                    trainers = ''
                    for trainer in lesson.trainer.all():
                        trainers += f'{trainer.surname} {trainer.name[0]}. {trainer.soname[0]}., '
                    text += f'{timezone.datetime.strftime(lesson.dt, "%d.%m.%Y %H:%M")} - {students[:-2]} ({trainers[:-2]})\n'
            else:
                text += f'<b>Индивидуальных занятий нет! </b>\n'
            button_footer = [{'👫 Ученики': f'group_{group.pk}&students'},
                             {'📊 Статистика': f'group_{group.pk}&statistic'},
                             {'text': '➕ Добавить ученика',
                              'web_app': WebAppInfo(url=f'{BASE_HOST}/club/{club.pk}/group/{group.pk}/add-student/0/')},
                             {'text': '➕ Добавить занятие',
                              'web_app': WebAppInfo(url=f'{BASE_HOST}/club/{club.pk}/group/{group.pk}/add-lesson/')},
                             {'◀️ Назад': f'club_{club.pk}&groups'}]

            keyboard2 = Keyboa(items=button_footer, items_in_row=2).keyboard
            keyboard = Keyboa.combine(keyboards=(keyboard2,))
            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=text, reply_markup=keyboard)
        else:
            mes_data = call.data.split('_')
            pk_group = int(mes_data[1].split('&')[0])
            group = ClubGroup.objects.filter(pk=int(pk_group)).first()
            club = group.club
            choice = mes_data[1].split('&')[1]

            if choice == 'students':
                students = Student.objects.filter(group=group, is_deleted=False)
                warning = ''
                if students:
                    for student in students:
                        if student.user is None:
                            warning = '⚠️ '
                        if not student.is_active:
                            warning = '⛔️ '
                        menu.append(
                            {
                                f'{warning}{student.surname} {student.name[0]}.{student.soname[0]}.': f'student_{student.pk}'})
                    menu.append({'◀️ Назад': f'group_{group.pk}'})
                    keyboard = Keyboa(items=menu, items_in_row=3)
                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text=f'👫 {club.title}, <b>{group.title}</b>, ученики:',
                                                reply_markup=keyboard())
                else:
                    menu = [{'text': '➕ Добавить ученика',
                             'web_app': WebAppInfo(url=f'{BASE_HOST}/club/{club.pk}/group/{group.pk}/student-add/')},
                            {'◀️ Назад': f'group_{group.pk}'}]
                    keyboard = Keyboa(items=menu, items_in_row=1)
                    msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                                text='🤷🏼‍♂️ В эту группу еще не добавлены ученики...',
                                                reply_markup=keyboard())

            if choice == 'statistic':
                text = f'Здесь предполагается какая-то краткая статистика по группе. Это как раз на подумать, {call.message.chat.first_name}...'
                menu.append({'◀️ Назад': f'club_{club.pk}&groups'})
                keyboard = Keyboa(items=menu, items_in_row=2)
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=f'📊 {club.title}, <b>{group.title}</b>, статистика:\n\n{text}',
                                            reply_markup=keyboard())

    # **************************** Обработка нажатий на кнопки student_ ********************************************
    if call.data.startswith('student_'):
        if '&' not in call.data:
            menu = []
            mes_data = call.data.split('_')
            student = Student.objects.filter(pk=int(mes_data[1])).first()
            group = student.group
            club = group.club
            birthday = "Не указан"
            if student.birthday:
                birthday = datetime.strftime(student.birthday, "%d.%m.%Y")
            statistic = 'Здесь какая то статистика 1.\nЗдесь какая то статистика 2.\nЗдесь какая то статистика 3.'
            if student.user is not None:
                button_footer = [
                    {'text': '📝 Редактировать', 'web_app': WebAppInfo(url=f'{BASE_HOST}/student/{student.pk}/edit/')},
                    {'✉️ Сообщение': f'mailing_personal&student_{student.pk}'},
                    {'◀️ Назад': f'group_{group.pk}&students'}]
                keyboard2 = Keyboa(items=button_footer).keyboard
                keyboard = Keyboa.combine(keyboards=(keyboard2,))
                text = f'<b>👨🏼‍🏫 {student}</b>\n\n🎂 {birthday}\n👤 {student.agent_name}\n' \
                       f'📞 <a href="tel:{student.agent_phone}">{student.agent_phone}</a>\n' \
                       f'🗂 {group.title}\n📊 Статистика:\n{statistic}'
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=text, reply_markup=keyboard)
                return True
            else:
                button_footer = [{'◀️ Назад': f'group_{group.pk}&students'}]
                keyboard2 = Keyboa(items=button_footer).keyboard
                keyboard = Keyboa.combine(keyboards=(keyboard2,))
                text = f'⚠️ Ученик не завершил регистрацию! Отправьте ему ссылку для создания логина и пароля:\n\n' \
                       f'👉🏻 <code>{requests.get(f"https://clck.ru/--?url={TELEGRAM_BOT_URI}c{student.pk}s").text}</code>'
                msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                            text=text, reply_markup=keyboard)
                return True
        else:
            pass

    # **************************** Обработка нажатий на кнопки mailing_ ********************************************
    if call.data.startswith('mailing_personal'):
        menu = []
        mes_data = call.data.split('&')
        for_who = mes_data[1].split('_')[0]
        recipient = mes_data[1].split('_')[1]
        if for_who == 'director':
            recipient_data = Director.objects.filter(pk=int(recipient)).first()
            club = recipient_data.club
        if for_who == 'trainer':
            recipient_data = Trainer.objects.filter(pk=int(recipient)).first()
            club = recipient_data.club
        if for_who == 'student':
            recipient_data = Student.objects.filter(pk=int(recipient)).first()
            club = recipient_data.group.club

        link = f'{BASE_HOST}/personal-mailing/<int:user_type>/<int:pk_user>/'


# **************************** Обработка любых текстовых сообщений_ ********************************************
@bot.message_handler(func=lambda message: True)
def send(message, **kwargs):
    print(message.text)
    # msg = bot.send_message(message.chat.id, message.text)
    # bot.send_message(message.chat.id, f'{msg.message_id}')
    # sleep(5)
    # clear_chat(message.chat.id, msg.message_id)

# ********************** Обработка СПЕЦИАЛЬНОГО тестового сообщения *****************************************
