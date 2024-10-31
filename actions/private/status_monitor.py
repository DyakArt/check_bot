import aiohttp  # Асинхронная библиотека для HTTP-запросов
from datetime import datetime
import asyncio

# наши импорты
# импортируем метод проверки, когда пользователь был онлайн
from actions.vk_api import check_online_vk
# импортируем глобальные переменные
from singleton import global_vars


async def monitoring_vk_user(bot):
    """Асинхронный метод отслеживающий онлайн пользователя ВК"""
    while True:
        current_time = datetime.now().strftime('%d-%m-%Y %H:%M')
        for user_id, vk_user_ids in global_vars.subscribers_vk.items():
            for vk_user_id in vk_user_ids:
                user_info = await check_online_vk(vk_user_id, global_vars.session)
                # если нет пользователя, переходим к следующему
                if not user_info:
                    continue

                is_online = user_info["online"] == 1
                platform = user_info["platform"]
                last_seen_time = user_info["last_seen_time"]

                # Проверка на вход в сеть
                if is_online and not global_vars.online_status_subscribers_vk.get(vk_user_id, False):
                    # Пользователь зашел в сеть
                    global_vars.online_status_subscribers_vk[vk_user_id] = True
                    await bot.send_message(
                        user_id,
                        f"Пользователь {vk_user_id} зашел в сеть. Время: {current_time}\nС устройства: {platform}"
                    )

                # Проверка на выход из сети
                elif not is_online and global_vars.online_status_subscribers_vk.get(vk_user_id, False):
                    # Пользователь вышел из сети
                    global_vars.online_status_subscribers_vk[vk_user_id] = False
                    await bot.send_message(
                        user_id,
                        f"Пользователь {vk_user_id} вышел из сети. Время выхода: {last_seen_time.strftime('%d-%m-%Y %H:%M')}"
                    )

                # Небольшая задержка между запросами для каждого подписчика
                await asyncio.sleep(0.5)

        # проверяем онлайн статус каждые 10 секунд
        await asyncio.sleep(10)
