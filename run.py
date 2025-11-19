import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from dotenv import load_dotenv
from app.handlers import router
from app.background_tasks import setup_scheduler


async def main():
    load_dotenv()
    bot = Bot(
        token=os.getenv('TG_TOKEN'),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp['bot'] = bot
    
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)
    
    dp.include_router(router)
    await dp.start_polling(bot)


async def startup(dispatcher: Dispatcher):
    print('Bot started.')
    bot = dispatcher['bot']
    setup_scheduler(bot)

async def shutdown(dispatcher: Dispatcher):
    print('Bot stopped.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Бот остановлен!')