from aiogram import Bot
from aiogram.types import BotCommand
import asyncio
from telegram_bot import bot, dp
from telegram_bot import start, check_on, check_off, check_info, check


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начало работы"),
        BotCommand(command="/check_on", description="Включение проверки новых записей"),
        BotCommand(command="/check_off", description="Выключение проверки новых записей"),
        BotCommand(command="/check_info", description="Включена ли проверка?"),
    ]
    await bot.set_my_commands(commands)


async def main():

    dp.register_message_handler(start, commands='start')
    dp.register_message_handler(check_on, commands='check_on')
    dp.register_message_handler(check_off, commands='check_off')
    dp.register_message_handler(check_info, commands='check_info')
    await set_commands(bot=bot)

    loop = asyncio.get_event_loop()
    loop.create_task(check())

    await dp.start_polling()


if __name__ == '__main__':
    print('Ready')
    asyncio.run(main())
