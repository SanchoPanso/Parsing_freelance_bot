from telegram_bot import bot, dp, executor
from telegram_bot import start, check_on, check_off, check
from aiogram import Bot
from aiogram.types import BotCommand
import asyncio


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начало работы"),
        BotCommand(command="/check_on", description="check_on"),
        BotCommand(command="/check_off", description="check_off"),
    ]
    await bot.set_my_commands(commands)


async def main():
    dp.register_message_handler(start, commands='start')
    dp.register_message_handler(check_on, commands='check_on')
    dp.register_message_handler(check_off, commands='check_off')
    await set_commands(bot=bot)

    loop = asyncio.get_event_loop()
    loop.create_task(check())

    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
