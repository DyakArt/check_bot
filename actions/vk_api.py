# взаимодействие с API ВК (сетевые запросы)

import aiohttp  # Асинхронная библиотека для HTTP-запросов
# чтобы код был более устойчивым к временным проблемам с сетью, установим тайм-ауты для запросов и используем
# повторные попытки
from aiohttp import ClientTimeout
import os
from datetime import datetime
# библиотеки для автоматического нахождения нашего файла dotenv и его загрузки
from dotenv import find_dotenv, load_dotenv
import asyncio
import logging

# Настраиваем логгер
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())

# название возможных платформ у пользователя
platform_names = os.getenv("PLATFORMS_NAMES").split(',')
# удаляем пробелы, если есть
platform_names = [platform.strip() for platform in platform_names]


async def get_request(session, method, user_id, fields: str, retries=3):
    """Асинхронный метод для отправки запросов в ВК"""

    url = f"https://api.vk.com/method/{method}"
    access_token = os.getenv('TOKEN_VK')
    params = {
        "user_ids": user_id,
        "fields": fields,
        "access_token": access_token,
        "v": "5.131"
    }
    timeout = ClientTimeout(total=10)  # устанавливаем 10 секунд на запрос
    # пытаемся отправить запрос
    for attempt in range(retries):
        try:
            async with session.get(url, params=params, timeout=timeout) as response:
                return await response.json()
        except asyncio.TimeoutError:
            logger.warning(f"Тайм-аут при запросе к {url}, попытка {attempt + 1} из {retries}")
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
    return None


async def check_online_vk(user_id, session):
    """Асинхронный метод получения времени последнего входа и статуса онлайн в ВК"""

    # передаем параметры для запроса
    response = await get_request(session, method='users.get', user_id=user_id, fields="last_seen, online")

    if not response or "response" not in response or not response['response']:
        print(f"Ошибка: не удалось получить данные для пользователя {user_id}")
        return None

    user_info = response['response'][0]
    last_seen = user_info.get("last_seen", {})
    online = user_info.get("online", 0)  # 1, если онлайн, 0 если оффлайн

    if last_seen and "platform" in last_seen:
        last_seen_time = datetime.fromtimestamp(last_seen['time'])
        platform = last_seen['platform']
        platform_name = platform_names[platform - 1] if 1 <= platform <= len(platform_names) else "Неизвестно"
        return {"last_seen_time": last_seen_time, "platform": platform_name, "online": online}
    return None
