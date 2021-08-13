from aiogram import Bot, Dispatcher, executor, types
import asyncio
from config import paths, token
from config import parsing_delay, waiting_delay, ddos_delay
from json_io import get_data_from_file, write_data_into_file
from parsing_data import check_news
import random

random.seed()
chat_info_file_path = paths['chat_id_list_file_path']
chat_info = get_data_from_file(chat_info_file_path)


bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


async def start(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in chat_info.keys():
        chat_info[str(chat_id)] = {'checking_is_active': False}
        write_data_into_file(chat_info, chat_info_file_path)
    await message.answer("Начало работы")


async def check_on(message: types.Message):
    global chat_info
    chat_id = message.chat.id
    chat_info[str(chat_id)] = {'checking_is_active': True}
    write_data_into_file(chat_info, chat_info_file_path)
    await message.answer("Проверка включена")


async def check_off(message: types.Message):
    global chat_info
    chat_id = message.chat.id
    chat_info[str(chat_id)] = {'checking_is_active': False}
    write_data_into_file(chat_info, chat_info_file_path)
    await message.answer("Проверка выключена")


async def check_info(message: types.Message):
    chat_id = message.chat.id
    await message.answer(str(chat_info[str(chat_id)]['checking_is_active']))


def checking_is_active(chat_info: dict):
    """
    This function checks if at least one client turn on checking then the program needs to parse,
    that means the function return True
    """
    for key in chat_info.keys():
        if chat_info[key]['checking_is_active'] is True:
            return True
    return False


async def check():
    while True:
        if checking_is_active(chat_info):
            # print("Парсинг начат")
            news_list, result = await check_news()
            if result == 1:
                print("Засыпаем до лучших времен")
                await asyncio.sleep(ddos_delay*(1 + 0.7 * random.random()))
                print("Просыпаемся")
            # print("Парсинг закончен")
            # print(f"Найденных записей: {len(news_list)}")
            if len(news_list) > 0:
                for chat_id in chat_info.keys():
                    for new in news_list:
                        message_text = f"<a href = \'{new['url']}\'>{new['title']}</a>\n" \
                                       f"{new['description']}\n" \
                                       f"{new['publishing_time']}"
                        await bot.send_message(chat_id, message_text)
            await asyncio.sleep(parsing_delay * (1 + 0.5 * random.random()))
        else:
            # print("проверка неактивна")
            await asyncio.sleep(waiting_delay)

