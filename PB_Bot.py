import telebot
import time
from typing import List, Dict
import requests
import re


bot = telebot.TeleBot('TOKEN')

class User:
    def __init__(self,
                 login: str,
                 password: str,
                 update: str) -> None:
        self.login = login
        self.password = password
        self.update = update


userlist = {}


@bot.message_handler(content_types=['text'])
def checker(message):
    user_id = message.from_user.id
    if user_id in userlist.keys():
        actual_user = userlist[user_id]
        x = open_web(actual_user.login, actual_user.password, actual_user.update)
        if x:
            bot.send_message(user_id, 'Новая информация:')
            bot.send_message(user_id, x[1])
            update_info(user_id, x[0])
        else:
            pass
        time.sleep(100)
        message.text = '/start'
        checker(message)
    else:
        send_text(message)


def send_text(message):
    if message.text == '/start':
        bot.send_message(message.from_user.id, 'Привет, я буду присылать тебе обновления с poznámkových bloků')
        time.sleep(1)
        bot.send_message(message.from_user.id, 'Для начала введи свой učo')
        bot.register_next_step_handler(message, get_uco)
    elif message.text == 'zanogo':
        bot.send_message(message.from_user.id, 'Введи свой učo')
        bot.register_next_step_handler(message, get_uco)
    else:
        bot.send_message(message.from_user.id, 'Я не понимаю:( Попробуй ввести "/start"!')


def get_uco(message):
    uco = message.text
    time.sleep(1)
    bot.send_message(message.from_user.id, 'Теперь введи свой пароль. Да, я понимаю, что вводить пароль '
                                           'в телеграм-боте '
                                           'не хочется, но иначе пока никак, правда:(')
    bot.register_next_step_handler(message, get_password, uco)


def get_password(message, uco):
    password = message.text
    time.sleep(1)
    x = open_web(uco, password, "")
    if not x:
        bot.send_message(message.from_user.id, 'Вы ввели неправильный логин или пароль, попробуйте еще раз!')
        message.text = 'zanogo'
        send_text(message)
    else:
        new_user(message.from_user.id, uco, password, x[0])
        bot.send_message(message.from_user.id, 'Информация на данный момент:')
        bot.send_message(message.from_user.id, x[1])
        bot.send_message(message.from_user.id, 'В дальнейшем я буду автоматически '
                                               'присылать тебе обновления, не благодари;)')
        time.sleep(100)
        message.text = "/start"
        checker(message)


def new_user(id, login, parol, actual_info):
    userlist[id] = User(login, parol, actual_info)


def update_info(id, actual_info):
    userlist[id].update = actual_info


def creator(li, st):
    checker = False
    result = ['']
    for i in li:
        if not checker and st in i:
            checker = True
        if checker:
            result[len(result)-1] = result[len(result)-1] + i
            if "/" + st[1] + st[2] in i:
                result.append('')
                checker = False
    return result



def open_web(name, parol, actual):
    if re.search(r'[^a-zA-Z0-9]', parol) or not name.isdigit():
        return None

    url = "https://is.muni.cz/auth/student/poznamkove_bloky_nahled?obdobi=8063;studium=992339"
    page = requests.get(url, auth=(name, parol))
    if page.ok is False:
        return None

    x = page.text.split("\n")

    dl_checker = False
    dl = creator(x, "<dl")
    h3 = creator(x, "<h3")
    actualita = dl[0].split('dd>')[1].split("</")[0]

    time = actualita.split(",")[0]
    if time == actual:
        return None

    fixer = 0
    dt = ''
    new_info = ''
    breaker = False
    count = 0
    for every in dl:
        if time in every:
            if fixer == 1:
                dt = every.split("<dt")
            else:
                fixer += 1
        for i in dt:
            if time in i:
                course = h3[dl.index(every)+4].split(">")[1].split("</h")[0]
                exam = i.split('>')[1].split("</dt")[0]
                x = i.split('změněno')[1].split("</")
                changing = "změněno" + x[0] + '\n' + x[1].split('<pre>')[1]
                new_info = course + "\n" + exam + "\n" + changing
                breaker = True
                break
            count += 1
        if breaker:
            break
    return time, new_info



if __name__ == '__main__':
    bot.polling()
