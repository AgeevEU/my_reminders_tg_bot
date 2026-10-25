import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import router
from database import init_db
from scheduler import start_scheduler


async def main():
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    start_scheduler(bot)

    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
