# обработчики событий, которые относятся к общению бота с пользователем в личке
from aiogram import F, types, Router
# для обработки HTML
from aiogram.enums import ParseMode
# импортируем систему фильтрации сообщений и для работы с командами
from aiogram.filters import CommandStart, Command, or_f, StateFilter
# импортируем наш фильтр для определения личка, группа, супергруппа
from filters.chat_types import ChatTypeFilter
# импортируем ответные клавиатуры
from kbds.reply import get_keyboard
# импортируем классы для форматирования текста
from aiogram.utils.formatting import as_list, as_marked_section, Bold
# импортируем наши методы для лички
from actions import private_actions
# импортируем библиотеки для работы со стояниями
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# создаем отдельный роутер для сообщений лички
user_private_router = Router()
# подключаем фильтр для определения, где будет работать роутер (в личке, в группе, супергруппе)
user_private_router.message.filter(ChatTypeFilter(['private']))

# формируем клавиатуру для пользователя
USER_KB = get_keyboard(
    "Проверить онлайн",
    placeholder="Выберите действие",
    sizes=(1,)
)

# формируем клавиатуру для выбора соцсети
SOCIAL_MEDIA_KB = get_keyboard(
    "VK",
    "Telegram",
    placeholder="Выберите соцсеть",
    sizes=(1, 1)
)

# формируем клавиатуру для отмены и шага назад
BACK_KB = get_keyboard(
    "Назад",
    "Отменить",
    placeholder="Выберите действие",
    sizes=(1,)
)

# формируем клавиатуру только для отмены
CANCELED_KB = get_keyboard(
    "Отменить",
    placeholder="Выберите действие",
    sizes=(1,)
)


# обрабатываем команду /start
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    # отправляем стартовую клавиатуру пользователю
    await message.answer('Привет, я чек бот!',
                         reply_markup=get_keyboard(
                             'Проверить онлайн',
                             placeholder='Что Вас интересует?',
                             sizes=(2, 2)
                         ),
                         )


# Код ниже для машины состояний (FSM)
# Состояния для проверки онлайна в ВКонтакте
class CheckVKOnline(StatesGroup):
    """Шаги (состояния, через которые будет проходить пользователь для получения последнего входа в ВК)"""
    # Ожидание ID пользователя ВКонтакте
    vk_user_id = State()


class CheckTelegramOnline(StatesGroup):
    # Ожидание ID пользователя Telegram
    telegram_user_id = State()


# обработчик для шага назад
# @user_private_router.message(StateFilter('*'), Command("назад"))
# @user_private_router.message(StateFilter('*'), F.text.casefold() == "назад")
# async def cancel_handler(message: types.Message, state: FSMContext) -> None:
#     # получаем текущее состояние
#     current_state = await state.get_state()
#     # если у пользователя состояние ввода названия товара
#     if current_state == CheckVKOnline.vk_user_id:
#         await message.answer(
#             'Предыдущего шага нет, введите id пользователя ВК или напишите "отмена" для выхода к клавиатуре')
#         # выходим из обработчика
#         return
#
#     # создаем переменную для предыдущего состояния
#     previous = None
#     # проходимся по всем нашим состояниям в AddProduct
#     for step in CheckVKOnline.__all_states__:
#         # если полученное состояние = текущему состоянию
#         if step.state == current_state:
#             # устанавливаем значение предыдущего состояния
#             await state.set_state(previous)
#             await message.answer(f'Ок, Вы вернулись к предыдущему шагу.\n{AddProduct.texts[previous.state]}')
#             return
#         # будет обновляться, пока не попадёт в условие, а когда попадет, то станет известно предыдущее состояние
#         # например, состояние description не прошёл в условие, но следующее price - прошло, значит
#         # предыдущее это состояние description
#         previous = step

# обработка команды "Проверить онлайн"
@user_private_router.message(or_f(Command("check_online"), F.text.lower() == "проверить онлайн"))
async def choose_social_media(message: types.Message):
    await message.answer(
        "Выберите соцсеть, для которой вы хотите проверить онлайн-статус.",
        reply_markup=SOCIAL_MEDIA_KB
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
    )
    # as_html() - обрабатываем наш ответ, как html текст
    await message.answer(text.as_html(), reply_markup=CANCELED_KB)
    # становимся в состояние ожидания (id пользователя vk)
    await state.set_state(CheckVKOnline.vk_user_id)


# обработка выбора Telegram
@user_private_router.message(F.text == "Telegram")
async def start_telegram_check(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, отправьте ID или username пользователя Telegram, которого Вы хотите проверить.",
        reply_markup=CANCELED_KB
    )
    await state.set_state(CheckTelegramOnline.telegram_user_id)


# обработчик для отмены всех состояний
# добавляем StateFilter('*'), где '*' - любое состояние пользователя
@user_private_router.message(StateFilter('*'), Command("отменить"))
@user_private_router.message(StateFilter('*'), F.text.lower() == "отменить")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    # Получаем текущее состояние
    current_state = await state.get_state()

    # Добавляем отладку
    # print("Cancel command received. Current state:", current_state)

    # Если у пользователя нет состояния, то выходим из обработчика
    if current_state is None:
        # print("Нет активных состояний. Выход из обработчика отмены.")
        return

    # Очищаем все состояния пользователя
    await state.clear()

    # Отправляем сообщение об отмене и возвращаем начальную клавиатуру
    await message.answer("Действия отменены", reply_markup=USER_KB)
    # print("State cleared and user notified.")


# Обработка введенного id/username для ВКонтакте
@user_private_router.message(CheckVKOnline.vk_user_id, F.text)
async def process_vk_user_id(message: types.Message, state: FSMContext):
    # Преобразуем введенный текст в целое число (ID пользователя ВКонтакте)
    vk_user_id = message.text.strip()

    # Вызываем функцию для получения времени последнего входа
    last_seen_vk = private_actions.get_last_seen_vk(vk_user_id)

    # Отправляем ответ пользователю
    response_text = f"{last_seen_vk}"
    await message.answer(response_text, reply_markup=USER_KB)

    # Сбрасываем состояние после выполнения команды
    await state.clear()


# обработка введенного id/username для Telegram
@user_private_router.message(CheckTelegramOnline.telegram_user_id, F.text)
async def process_telegram_user_id(message: types.Message, state: FSMContext):
    telegram_user_id = message.text.strip()

    # Пример ответа (можно добавить реальную проверку статуса Telegram)
    await message.answer(f"Telegram: последний вход для пользователя {telegram_user_id} - Неизвестно",
                         reply_markup=USER_KB)

    await state.clear()
