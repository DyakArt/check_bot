# обработчики событий, которые относятся к общению бота с пользователем в личке

import os
from aiogram import F, types, Router
# для обработки HTML
from aiogram.enums import ParseMode
# импортируем систему фильтрации сообщений и для работы с командами
from aiogram.filters import CommandStart, Command, or_f, StateFilter
# импортируем библиотеки для работы со стояниями
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
# импортируем классы для форматирования текста
from aiogram.utils.formatting import as_list, as_marked_section, Bold
import aiohttp  # Асинхронная библиотека для HTTP-запросов

# наши импорты
# импортируем фильтр для определения личка, группа, супергруппа
from filters.chat_types import ChatTypeFilter
# импортируем ответные клавиатуры
from kbds.reply import get_keyboard
# импортируем методы для лички
from actions.private import status_monitor
# импортируем глобальные переменные
from singleton import global_vars




# создаем отдельный роутер для сообщений лички
user_private_router = Router()
# подключаем фильтр для определения, где будет работать роутер (в личке, в группе, супергруппе)
user_private_router.message.filter(ChatTypeFilter(['private']))

# Словарь для клавиатур
KEYBOARDS = {
    "user": get_keyboard("Проверить онлайн", placeholder="Выберите действие", sizes=(1,)),
    "social_media": get_keyboard("VK", placeholder="Выберите соцсеть", sizes=(1,)),
    "subscribe": get_keyboard("Подписаться", "Отписаться", "Отменить", placeholder="Выберите действие",
                              sizes=(1, 1, 1)),
    "back": get_keyboard("Назад", "Отменить", placeholder="Выберите действие", sizes=(1, 1)),
    "cancel": get_keyboard("Отменить", placeholder="Выберите действие", sizes=(1,))
}


# Вспомогательная функция для отправки ответов с клавиатурой
async def send_message_with_keyboard(message: types.Message, text: str, keyboard_type: str) -> None:
    await message.answer(text, reply_markup=KEYBOARDS[keyboard_type])


# Состояния для проверки онлайна в ВКонтакте
class CheckVKOnline(StatesGroup):
    """Шаги (состояния, через которые будет проходить пользователь для получения последнего входа в ВК)"""
    # Ожидание ID пользователя ВКонтакте
    vk_user_id = State()
    # Ожидание выбора: подписываться на отслеживание онлайна пользователя или нет
    waiting_for_subscription_choice = State()


# Обработчик для команды /start
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await send_message_with_keyboard(
        message,
        "Привет, я чек бот!",
        "user"
    )


# Код ниже для машины состояний (FSM)


# обработчик для отмены всех состояний
# добавляем StateFilter('*'), где '*' - любое состояние пользователя
@user_private_router.message(StateFilter('*'), Command("отменить"))
@user_private_router.message(StateFilter('*'), F.text.lower() == "отменить")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    # Получаем текущее состояние
    current_state = await state.get_state()

    # Если у пользователя нет состояния, то выходим из обработчика
    if current_state:
        # Очищаем все состояния пользователя
        await state.clear()

    # Отправляем сообщение об отмене и возвращаем начальную клавиатуру
    await send_message_with_keyboard(message, "Действия отменены", "user")


# обработка команды "Проверить онлайн"
@user_private_router.message(or_f(Command("check_online"), F.text.lower() == "проверить онлайн"))
async def choose_social_media(message: types.Message):
    await send_message_with_keyboard(
        message,
        "Выберите соцсеть, для которой вы хотите проверить онлайн-статус.",
        "social_media"
    )


# обработка выбора ВК
@user_private_router.message(F.text == "VK")
async def start_vk_check(message: types.Message, state: FSMContext):
    # текст для ответа в виде маркированного списка, сначала идёт заголовок
    text = as_marked_section(
        Bold('Пожалуйста, отправьте id или username пользователя VK, которого Вы хотите проверить.'),
        'Пример id: 1',
        'Пример username: durov',
        marker='✅ '
    ).as_html()
    await send_message_with_keyboard(message, text, "cancel")
    await state.set_state(CheckVKOnline.vk_user_id)


# Вспомогательная функция для обработки подписок
async def handle_subscription(user_id: int, vk_user_id: str, subscribe: bool) -> str:
    subscribers = global_vars.subscribers_vk
    if subscribe:
        if user_id not in subscribers:
            subscribers[user_id] = []
        if vk_user_id not in subscribers[user_id]:
            subscribers[user_id].append(vk_user_id)
            global_vars.online_status_subscribers_vk.setdefault(vk_user_id, False)
            return f"Вы подписались на уведомления о заходе пользователя {vk_user_id} в сеть."
        return f"Вы уже подписаны на пользователя {vk_user_id}."
    else:
        if user_id in subscribers and vk_user_id in subscribers[user_id]:
            subscribers[user_id].remove(vk_user_id)
            if not subscribers[user_id]:
                del subscribers[user_id]
            return f"Вы отписались от уведомлений для данного пользователя {vk_user_id}."
        return f"Вы не подписаны на уведомления для этого пользователя {vk_user_id}."


# Обработка введенного id/username для ВКонтакте
@user_private_router.message(CheckVKOnline.vk_user_id, F.text)
async def process_vk_user_id(message: types.Message, state: FSMContext):
    session = global_vars.session  # Извлекаем session
    vk_user_id = message.text.strip()
    if session is None:
        print("Ошибка: session не инициализирован")
        return

    # Вызываем функцию для получения времени последнего входа
    last_seen_data = await status_monitor.check_online_vk(vk_user_id, session)

    if last_seen_data:
        last_seen_time = last_seen_data["last_seen_time"].strftime("%d-%m-%Y %H:%M:%S")
        platform_name = last_seen_data["platform"]
        response_text = (
            f"Последний раз в сети: {last_seen_time}, с устройства: {platform_name}.\n\n"
            "Вы хотите подписаться/отписаться на уведомления об онлайн статусе этого пользователя?"
        )
    else:
        response_text = "Информация о последнем посещении отсутствует или пользователь не найден."

    await state.update_data(vk_user_id=vk_user_id)
    await send_message_with_keyboard(message, response_text, "subscribe")
    await state.set_state(CheckVKOnline.waiting_for_subscription_choice)


# Обработка команды подписки на уведомления
@user_private_router.message(CheckVKOnline.waiting_for_subscription_choice, F.text == "Подписаться")
async def subscribe_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    response_text = await handle_subscription(message.from_user.id, data["vk_user_id"], subscribe=True)
    await send_message_with_keyboard(message, response_text, "user")
    await state.clear()


# Обработка команды отписки от уведомлений
@user_private_router.message(CheckVKOnline.waiting_for_subscription_choice, F.text == "Отписаться")
async def unsubscribe_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    response_text = await handle_subscription(message.from_user.id, data["vk_user_id"], subscribe=False)
    await send_message_with_keyboard(message, response_text, "user")
    await state.clear()
