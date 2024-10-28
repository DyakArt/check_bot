# точка входа
import os
import asyncio
from aiogram import Bot, Dispatcher, types
# импортируем класс для форматирования текста
from aiogram.enums import ParseMode
# импортируем класс для настроек бота
from aiogram.client.default import DefaultBotProperties

# библиотеки для автоматического нахождения нашего файла dotenv и его загрузки
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

# наши импорты
# импортируем наш роутер для обработки событий в личке
from handlers.user_private import user_private_router

# импортируем наши команды для бота (private - для личных сообщений)
from common.bot_cmds_list import private

# указываем какие именно изменения отслеживаем у сервера telegram
ALLOWED_UPDATES = ['message, edited_message']

# инициализируем класс бота, передаем токен
bot = Bot(token=os.getenv('TOKEN_TG'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# создаем класс диспетчера, который отвечает за фильтрацию разных сообщений (сообщения от сервера telegram)
dp = Dispatcher()

# подключаем наши роутеры (работают в том же порядке)
dp.include_routers(user_private_router)


async def main():
    """Метод запуска бота"""

    # отвечаем только, когда бот онлайн
    await bot.delete_webhook(drop_pending_updates=True)
    # удалить все наши команды для лички
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    # отправляем все наши команды, которые будут у бота (только в личке)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    # слушаем сервер telegram и постоянно спрашиваем его про наличие каких-то изменений
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


# запускаем нашу функцию main
asyncio.run(main())
