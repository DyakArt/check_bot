# методы для лички

import requests
import os
from datetime import datetime
# библиотеки для автоматического нахождения нашего файла dotenv и его загрузки
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def get_last_seen_vk(user_id):
    """Метод получения последнего входа в ВК"""
    access_token = os.getenv('TOKEN_VK')
    if not access_token:
        print("Ошибка: токен не найден. Убедитесь, что он указан.")
        return

    url = f"https://api.vk.com/method/users.get"
    params = {
        "user_ids": user_id,
        "fields": "last_seen",
        "access_token": access_token,
        "v": "5.131"
    }

    try:
        response = requests.get(url, params=params).json()
        if "response" in response and response['response']:
            user_info = response['response'][0]
            last_seen = user_info.get("last_seen", {})
            if last_seen:
                last_seen_time = last_seen['time']
                platform = last_seen['platform']

                last_seen_date = datetime.fromtimestamp(last_seen_time)
                platform_names = ["мобильная версия", "iPhone", "iPad", "Android", "Windows Phone", "Windows 10", "ПК"]
                platform_name = platform_names[platform - 1]

                return f"последний раз в сети: {last_seen_date}, с {platform_name}"
            else:
                return "информация о последнем посещении отсутствует."
        # Если данные не найдены, возвращаем сообщение "Пользователь не найден"
        else:
            return "пользователь с таким id/username не найден.\nПодсказка: введите корректный id/username.\n"
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
