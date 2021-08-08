from aiogram import Bot, Dispatcher, executor, types
import asyncio
from config import token
from parsing_data import check_news

chat_id_list = [360558957]

bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    await message.answer("Начало работы")


async def check():
    while True:
        news_list = await check_news()    # доработать
        if len(news_list) > 0:
            for chat_id in chat_id_list:
                for new in news_list:
                    await bot.send_message(chat_id, new)
        else:
            print("пока глухо")
        await asyncio.sleep(5)

loop = asyncio.get_event_loop()
loop.create_task(check())
