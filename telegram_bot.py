from aiogram import Bot, Dispatcher, executor, types
import asyncio
from config import paths, token
from config import parsing_delay, waiting_delay
from json_io import get_data_from_file, write_data_into_file
from parsing_data import check_news
import pickle


def checking_is_active(chat_info: dict):
    """
    This function checks if at least one client turn on checking then the program needs to parse,
    that means the function return True
    """
    for key in chat_info.keys():
        if chat_info[key]['checking_is_active'] is True:
            return True
    return False


# chat_id_list = []   # [360558957]
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


async def check():
    while True:
        if checking_is_active(chat_info):
            print("парсинг начат")
            news_list = await check_news()
            print("парсинг закончен")
            # print(f"Найденных записей: {len(news_list)}")
            if len(news_list) > 0:
                for chat_id in chat_info.keys():
                    for new in news_list:
                        message_text = f"<a href = \'{new['url']}\'>{new['title']}</a>\n" \
                                       f"{new['description']}\n" \
                                       f"{new['publishing_time']}"
                        await bot.send_message(chat_id, message_text)
            await asyncio.sleep(parsing_delay)
        else:
            print("проверка неактивна")
            await asyncio.sleep(waiting_delay)

