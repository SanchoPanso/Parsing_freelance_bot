from aiogram import Bot, Dispatcher, executor, types
import asyncio
from config import paths, token
from parsing_data import check_news
import pickle

checking_is_active = False

chat_id_list = []   # [360558957]
chat_id_list_file_path = paths['chat_id_list_file_path']


bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


async def start(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in chat_id_list:
        chat_id_list.append(chat_id)
    await message.answer("Начало работы")


async def check_on(message: types.Message):
    global checking_is_active
    checking_is_active = True
    await message.answer("Проверка включена")


async def check_off(message: types.Message):
    global checking_is_active
    checking_is_active = False
    await message.answer("Проверка выключена")


async def check():
    while True:
        if checking_is_active:
            print("парсинг начат")
            news_list = await check_news()
            print("парсинг закончен")
            print(f"Найденных записей: {len(news_list)}")
            if len(news_list) > 0:
                for chat_id in chat_id_list:
                    for new in news_list:
                        message_text = f"<b>{new['title']}</b>\n{new['description']}"
                        await bot.send_message(chat_id, message_text)
            await asyncio.sleep(5 * 60)
        else:
            print("проверка неактивна")
            await asyncio.sleep(10)

