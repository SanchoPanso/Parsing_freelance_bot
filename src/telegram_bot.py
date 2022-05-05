from aiogram import Bot, Dispatcher, executor, types
import asyncio
from src.config import paths
from src.config import parsing_delay, waiting_delay, ddos_delay
from src.config import fl_ru_host, fl_ru_projects_url
from src.json_io import get_data_from_file, write_data_into_file
from src.parsing_data import check_news
from src.parsers.parsing_fl import FLParser, ParsingResult
from os import getenv
import random
import logging
import sys
from memory_profiler import memory_usage

logger = logging.getLogger("App.TelegramBot")

fl_parser = FLParser(fl_ru_projects_url, paths['project_data_file_path'])

random.seed()
chat_info_file_path = paths['chat_id_list_file_path']
chat_info = dict()  # get_data_from_file(chat_info_file_path)

token = getenv("BOT_TOKEN")
if not token:
    sys.exit("Error: no token provided")

bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


async def start(message: types.Message):
    chat_id = message.chat.id
    logger.info(f"Command '/start' started in chat id {chat_id}")
    if chat_id not in chat_info.keys():
        chat_info[str(chat_id)] = {'checking_is_active': False}
        # write_data_into_file(chat_info, chat_info_file_path)
    await message.answer("Начало работы")


async def check_on(message: types.Message):
    global chat_info
    chat_id = message.chat.id
    logger.info(f"Command '/check on' started in chat id {chat_id}")
    chat_info[str(chat_id)] = {'checking_is_active': True}
    # write_data_into_file(chat_info, chat_info_file_path)
    await message.answer("Проверка включена")


async def check_off(message: types.Message):
    global chat_info
    chat_id = message.chat.id
    logger.info(f"Command '/check off' started in chat id {chat_id}")
    chat_info[str(chat_id)] = {'checking_is_active': False}
    # write_data_into_file(chat_info, chat_info_file_path)
    await message.answer("Проверка выключена")


async def check_info(message: types.Message):
    chat_id = message.chat.id
    logger.info(f"Command '/check info' started in chat id {chat_id}")
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
            logger.info("Checking is active, parsing started")
            news_list, result = await fl_parser.check_news()
            if result == ParsingResult.BLOCKED_BY_GUARD:
                logger.info("Request blocked. Go asleep")
                for chat_id in chat_info.keys():
                    await bot.send_message(chat_id, "Сработала защита ddos-guard. Засыпаем до лучших времен")

                await asyncio.sleep(ddos_delay*(1 + 0.7 * random.random()))

                logger.info("Awake after blocking")
                for chat_id in chat_info.keys():
                    await bot.send_message(chat_id, "Просыпаемся")

            elif result == ParsingResult.SUCCESSFUL:
                logger.info(f"Parsing successfully ended. Sending is starting")
                logger.info(f"Number of the foung news: {len(news_list)}")

                if len(news_list) > 0:
                    for chat_id in chat_info.keys():
                        if chat_info[chat_id]['checking_is_active'] is True:
                            for new in news_list:
                                message_text = new
                                await bot.send_message(chat_id, message_text)

                logger.info(f"Sending ended")
                await asyncio.sleep(parsing_delay * (1 + 0.5 * random.random()))
        else:
            logger.info("Checking is not active")
            await asyncio.sleep(waiting_delay)

