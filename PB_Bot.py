from typing import List, Dict
import requests
import re
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

class Test(StatesGroup):
    S1 = State()
    S2 = State()
    S3 = State()


userlist = {}

loop = asyncio.get_event_loop()

bot = Bot(token='TOKEN') #change token
dp = Dispatcher(bot, storage=MemoryStorage())

button_en = KeyboardButton('English 🇬🇧')
button_cz = KeyboardButton('Czech 🇨🇿')
button_ru = KeyboardButton('Русский 🇷🇺')
greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
greet_kb.add(button_en, button_ru, button_cz)

start = 'Choose a language!' + '\n' + 'Vyberte si jazyk!' + '\n' + 'Выбери язык!'
ru_commands = {'hi':'Привет, я буду присылать тебе обновления с poznámkových bloků',
               'uco':'Для начала введи свой učo', 'password':'Теперь введи свой пароль. '
                'Да, я понимаю, что вводить пароль '
                'в телеграм-боте не хочется, но иначе пока никак, правда😔',
                'information':'Информация на данный момент:',
               'next':'В дальнейшем я буду автоматически '
                                               'присылать тебе обновления, не благодари😉'}

cz_commands = {'hi':'Ahoj, budu posílat vám aktualizace z poznávacích bloků',
               'uco':'Nejprve zadejte své učo', 'password':'Nyní zadejte své heslo. '
                'Ano, chápu, že nechcete zadat heslo do telegramového robota, '
                'ale neexistuje žádný jiný způsob, omlouvám se😔',
                'information':'Informace v tuto chvíli',
               'next':'V budoucnu vám automaticky pošlu aktualizace, neděkujte mi😉'}

en_commands = {'hi':'Hi, I will send you Information from notebooks',
               'uco':'First of all, enter your učo', 'password':'Now enter your password. '
                'Yes, I understand that you do not want to enter a password in a telegram bot, '
                'but there is no other way, sorry😔',
                'information':'The information on this moment:',
               'next':'In the future, I will automatically '
                                               "send you updates, don't thank me😉"}



class User:
    def __init__(self,
                 login: str,
                 password: str,
                 update: str,
                 language: dict) -> None:
        self.login = login
        self.password = password
        self.update = update
        self.language = language




@dp.message_handler(commands='start')
async def process_start_command(message: types.Message):
    await message.answer(start, reply_markup=greet_kb)
    await Test.S1.set()


@dp.message_handler(state=Test.S1)
async def lang(message: types.Message, state: FSMContext):
    global language
    language = ""
    if message.text == button_ru.text:
        language = ru_commands
    if message.text == button_en.text:
        language = en_commands
    if message.text == button_cz.text:
        language = cz_commands
    if language:
        await message.answer(language['hi'])
        await message.answer(language['uco'])
        await Test.S2.set()
    else:
        await message.answer('try again')
        await message.answer('press /start')
        await state.reset_state()



@dp.message_handler(state=Test.S2)
async def lang(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('try again')
        await message.answer('press /start')
        await state.reset_state()
    else:
        global uco
        uco = message.text
        await message.answer(language['password'])
        await Test.S3.set()




@dp.message_handler(state=Test.S3)
async def lang(message: types.Message, state: FSMContext):
    password = message.text
    x = open_web(uco, password, "")

    if not x:
        await message.answer('try again')
        await message.answer('press /start')
        await state.reset_state()
    else:
        new_user(message.from_user.id, uco, password, x[0], language)
        await message.answer(language['information'])
        await message.answer(x[1])
        await message.answer(language['next'])
        await state.reset_state()


def new_user(id, login, parol, actual_info, language):
    userlist[id] = User(login, parol, actual_info, language)


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
    if not name.isdigit():
        return None

    url = "https://is.muni.cz/auth/student/poznamkove_bloky_nahled?obdobi=8063;studium=992339"
    page = requests.get(url, auth=(name, parol))
    if page.ok is False:
        return None

    x = page.text.split("\n")
    is_cz = False
    dl_checker = False
    dl = creator(x, "<dl")
    h3 = creator(x, "<h3")
    actualita = dl[0].split('dd>')[1].split("</")[0]
    if 'Poslední změna:' in dl[0]:
        is_cz = True

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
                if is_cz:
                    x = i.split('změněno')[1].split("</")
                    changing = "změněno" + x[0] + '\n' + x[1].split('<pre>')[1]
                else:
                    x = i.split('last modified')[1].split("</")
                    changing = "last modified" + x[0] + '\n' + x[1].split('<pre>')[1]
                course = h3[dl.index(every)+4].split(">")[1].split("</h")[0]
                exam = i.split('>')[1].split("</dt")[0]
                new_info = course + "\n" + exam + "\n" + changing
                breaker = True
                break
            count += 1
        if breaker:
            break
    return time, new_info



async def sheduled(wait):
    while True:
        await asyncio.sleep(wait)
        if userlist:
            keys = list(userlist.keys())
            for every in keys:
                login = userlist[every].login
                password = userlist[every].password
                update = userlist[every].update
                language = userlist[every].language
                x = open_web(uco, password, update)
                if x:
                    await bot.send_message(language['next'])
                    await bot.send_message(every, x[1])
                    update_info(every, x[0])



if __name__ == '__main__':
    loop.create_task(sheduled(300))
    executor.start_polling(dp, skip_updates=True)
