import asyncio
import json
import os
from typing import Dict, List, Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния FSM
class QuestStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_task_answer = State()

# Файл для хранения данных
DATA_FILE = "quest_data.json"

# Структура данных для хранения ответов участников
participants_data = {}

# Счетчик нажатий для кнопки "Миссия невыполнима"
mission_impossible_clicks = {}

# Список участников с красивым оформлением
PARTICIPANTS = [
    "👸 Наталья",
    "🌟 Юлия Иванова", 
    "💫 Анастасия",
    "🌸 Анна",
    "✨ Юлия Кузнецова",
    "🌺 Ольга"
]

# Список участников без эмодзи для внутренней логики
PARTICIPANTS_CLEAN = [
    "Наталья",
    "Юлия Иванова", 
    "Анастасия",
    "Анна",
    "Юлия Кузнецова",
    "Ольга"
]

# Задания для каждого участника
TASKS = {
    "Наталья": [
        "Подойди к моему свекру и узнай как прошла его последняя рыбалка. Узнай место и улов😉",
        "Закажи у диджея подходящую песню и станцуй ламбаду с подругами. Не забудь запечатлеть это на камеру, а потом загрузи сюда!",
        "Обещай больше никогда не говорить, что меня купили у цыганей. Советую хорошо подумать и дать свой ответ.",
        "Тогда сделай фото с моей любимкой❤️ Я думаю, ты знаешь кто это?"
    ],
    "Юлия Иванова": [
        "Сделай фото с человеком пауком.",
        "Узнай у Раисы Хруленко кто ее любимый внук😚",
        "Скажи Алине Хруленко, что Дане очень нравится песня «Сыну, Сыну, он жених.» Предлложи ей заказать эту песню у диджея. Запиши на видео ваш разговор😜"
    ],
    "Анастасия": [
        "Попроси диджея включить песню «Царица». Перед тем, как он согласится (надо будет поуговаривать), объяви в микрофон, что сейчас будет играть твоя самая любимая песня. Не забудь запечатлеть на видео",
        "Иди к сестре невесты и попроси помощи в таком совместном фото. Результат скинь боту",
        "Предложи ведущему познакомиться и попроси его номер. Напиши мне его ответ"
    ],
    "Анна": [
        "Аня, ты уже получила свое первое задание. Покажешь, что получилось?",
        "Среди гостей есть тайный агент. Подойди к нему и скажи «Погода сегодня отличная для миссии.» Если он ответит тебе «Но дождь запланирован на вечер». Напиши его имя",
        "Сделай фото с папой жениха"
    ],
    "Юлия Кузнецова": [
        "Скажи молодым тост, в который незаметно включи любую фразу из нашего детства. Запиши на видео и скинь мне",
        "Сделай фото с мамой невесты❤️",
        "Мне всегда было интересно узнать историю любви Бабушки Люды и дедушки Славы. Можешь узнать для меня?"
    ],
    "Ольга": [
        "Узнай у жениха его любимое блюдо, а потом спроси у его бабушки рецепт",
        "Пожми любому мужчине руку и скажи «Поздравляю, Агент!» если он ответит «Миссия принята!» - ты выиграла, напиши его имя мне.",
        "Сделай селфи с молодоженами и загрузи его сюда"
    ]
}

# Правильные ответы для проверки
CORRECT_ANSWERS = {
    "Анна": {
        1: ["Бондаренко Андрей", "Бондик", "Андрей Дмитриевич"],
    },
    "Ольга": {
        1: ["Евгений Одинец", "Женя Одинец", "Женя", "Евгеша"],
    }
}

# Типы контента для каждого задания
TASK_CONTENT_TYPES = {
    "Наталья": ["text", "media", "text", "photo"],
    "Юлия Иванова": ["photo", "text", "video"],
    "Анастасия": ["video", "photo", "text"],
    "Анна": ["photo", "text", "photo"],
    "Юлия Кузнецова": ["video", "photo", "text"],
    "Ольга": ["text", "text", "photo"]
}

# Создаем папку для статических файлов
if not os.path.exists('static'):
    os.makedirs('static')

def load_data():
    """Загружает данные из JSON файла"""
    global participants_data, mission_impossible_clicks
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                participants_data = data.get('participants', {})
                mission_impossible_clicks = data.get('clicks', {})
                print(f"✅ Данные загружены: {len(participants_data)} участников")
        else:
            print("📁 Файл данных не найден, создаем новый")
            participants_data = {}
            mission_impossible_clicks = {}
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        participants_data = {}
        mission_impossible_clicks = {}

def save_data():
    """Сохраняет данные в JSON файл"""
    try:
        data = {
            'participants': participants_data,
            'clicks': mission_impossible_clicks
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Данные сохранены: {len(participants_data)} участников")
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")

# Загружаем данные при запуске
load_data()

def create_name_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с именами участников в несколько рядов"""
    builder = InlineKeyboardBuilder()
    
    # Разбиваем на ряды по 2 кнопки для лучшего отображения
    for i in range(0, len(PARTICIPANTS), 2):
        row = [PARTICIPANTS[i]]
        if i + 1 < len(PARTICIPANTS):
            row.append(PARTICIPANTS[i + 1])
        
        for j, name in enumerate(row):
            # Используем чистое имя для callback_data, но красивое для отображения
            clean_name = PARTICIPANTS_CLEAN[i + j]
            builder.add(InlineKeyboardButton(text=name, callback_data=f"name_{clean_name}"))
        builder.adjust(2)  # 2 кнопки в ряду
    
    return builder.as_markup()

def create_task_keyboard(task_index: int, participant: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для задания"""
    builder = InlineKeyboardBuilder()
    
    # Специальные кнопки для определенных заданий
    if participant == "Наталья" and task_index == 2:
        builder.add(InlineKeyboardButton(text="Миссия невыполнима", callback_data="mission_impossible"))
    
    # Кнопка для подсказки
    if participant == "Наталья" and task_index == 3:
        builder.add(InlineKeyboardButton(text="Подсказка💡", callback_data="hint_natalia"))
    
    # Кнопка для возврата к заданию
    if participant == "Юлия Иванова" and task_index == 0:
        builder.add(InlineKeyboardButton(text="Вернуться к заданию", callback_data="return_task"))
    
    return builder.as_markup()

def get_encouragement_message() -> str:
    """Возвращает случайное поощрительное сообщение"""
    messages = [
        "🎉 Отлично! Продолжай в том же духе!",
        "🌟 Превосходно! Ты справляешься на ура!",
        "💫 Молодец! Так держать!",
        "🌸 Замечательно! Ты настоящая звезда!",
        "✨ Браво! Следующее задание ждет тебя!",
        "🌺 Потрясающе! Ты невероятная!",
        "🎊 Фантастика! Продолжай удивлять!",
        "🏆 Великолепно! Ты на высоте!",
        "💎 Изумительно! Ты лучшая!",
        "🚀 Превосходно! Летим дальше!"
    ]
    import random
    return random.choice(messages)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда для просмотра справки"""
    help_text = """🤖 Доступные команды:

📋 Основные команды:
/start - Начать квест
/help - Показать эту справку

👑 Команды администратора:
/answers - Просмотр всех ответов участников
/status - Статус выполнения заданий участниками
/reset - Сброс всех данных участников
/clear_state - Сброс твоего состояния (если застрял в квесте)
/test_data - Создать тестовые данные для проверки
/save - Принудительно сохранить данные
/next_task - Принудительно переходить к следующему заданию
/reset_clicks - Сбросить счетчик нажатий кнопки "Миссия невыполнима"

💡 Если застрял в квесте, используй /clear_state для сброса состояния!
🔍 Если команда /answers не работает, используй /test_data для диагностики!
🚀 Если завис на задании, используй /next_task для принудительного перехода!
🔄 Если кнопка "Миссия невыполнима" глючит, используй /reset_clicks!"""
    
    await message.answer(help_text)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = """🎉 Добро пожаловать в Свадебный Бот! 🎉

Тебе предстоит пройти увлекательный квест, чтобы получить приз в конце!

Выбери свое имя из списка участников:"""
    
    await message.answer(welcome_text, reply_markup=create_name_keyboard())

@dp.callback_query(lambda c: c.data.startswith('name_'))
async def process_name_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора имени участника"""
    participant_name = callback.data.replace('name_', '')
    
    # Сохраняем выбранное имя в состоянии
    await state.update_data(participant=participant_name)
    
    # Инициализируем данные участника если их нет
    if participant_name not in participants_data:
        participants_data[participant_name] = {
            'current_task': 0,
            'completed_tasks': [],
            'answers': {}
        }
        # Сохраняем данные после изменения
        save_data()
    
    # Показываем первое задание
    await show_task(callback.message, participant_name, 0)
    await callback.answer()

async def show_task(message: types.Message, participant: str, task_index: int):
    """Показывает задание участнику"""
    if task_index >= len(TASKS[participant]):
        # Все задания выполнены
        await message.answer("🎉 Ты очень классно постаралась! Подожди остальных девочек или помоги им в выполнении заданий. А потом все вместе узнайте у координатора Виолетты куда же она дела подарки???")
        return
    
    task_text = TASKS[participant][task_index]
    keyboard = create_task_keyboard(task_index, participant)
    
    # Показываем задание
    await message.answer(f"📋 Задание {task_index + 1}:\n\n{task_text}", reply_markup=keyboard)
    
    # Если это Анастасия и второе задание, показываем пример фото
    if participant == "Анастасия" and task_index == 1:
        try:
            # Пытаемся отправить пример фото
            photo_path = "photo_2025-08-11_11-45-40.jpg"
            if os.path.exists(photo_path):
                await message.answer_photo(
                    types.FSInputFile(photo_path),
                    caption="📸 Вот пример такого фото!"
                )
            else:
                await message.answer("📸 Пример фото будет показан позже")
        except Exception as e:
            await message.answer("📸 Пример фото будет показан позже")
            print(f"Ошибка при отправке фото: {e}")

@dp.callback_query(lambda c: c.data == "mission_impossible")
async def mission_impossible_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Миссия невыполнима'"""
    data = await state.get_data()
    participant = data.get('participant')
    
    if participant and participant in participants_data:
        # Увеличиваем счетчик нажатий
        if participant not in mission_impossible_clicks:
            mission_impossible_clicks[participant] = 0
        
        mission_impossible_clicks[participant] += 1
        save_data()  # Сохраняем счетчик
        
        # Если нажали 2+ раза, показываем подсказку и завершаем задание
        if mission_impossible_clicks[participant] >= 2:
            # Автоматически завершаем задание
            current_task = participants_data[participant]['current_task']
            participants_data[participant]['completed_tasks'].append(current_task)
            participants_data[participant]['answers'][current_task] = "Задание пропущено (кнопка нажата 2+ раза)"
            participants_data[participant]['current_task'] += 1
            
            # Сбрасываем счетчик
            mission_impossible_clicks[participant] = 0
            save_data()
            
            await callback.message.answer("💡 Подсказка: Задание автоматически завершено! Переходим к следующему.")
            
            # Проверяем, не последнее ли это задание
            if participants_data[participant]['current_task'] >= len(TASKS[participant]):
                await callback.message.answer("🎉 Ты очень классно постаралась! Подожди остальных девочек или помоги им в выполнении заданий. А потом все вместе узнайте у координатора Виолетты куда же она дела подарки???")
            else:
                encouragement = get_encouragement_message()
                await callback.message.answer(f"{encouragement}\n\n📋 Следующее задание для тебя:")
                await show_task(callback.message, participant, participants_data[participant]['current_task'])
            return
        
        # Если нажали 1 раз, показываем сообщение
        await callback.message.answer(f"🤔 Да ладно тебе, Наталья! Попробуй еще раз!")
        return
    
    await callback.answer()

@dp.callback_query(lambda c: c.data == "hint_natalia")
async def hint_natalia_handler(callback: types.CallbackQuery):
    """Обработчик подсказки для Натальи"""
    await callback.message.answer("💡 Подсказка: Последнее время я ласково называю тебя ее именем😚")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "return_task")
async def return_task_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик возврата к заданию"""
    data = await state.get_data()
    participant = data.get('participant')
    
    if participant:
        await show_task(callback.message, participant, 0)
    
    await callback.answer()

def check_content_type(participant: str, task_index: int, content_type: str) -> bool:
    """Проверяет правильность типа контента для задания"""
    if participant in TASK_CONTENT_TYPES and task_index < len(TASK_CONTENT_TYPES[participant]):
        expected_type = TASK_CONTENT_TYPES[participant][task_index]
        
        # Отладочная информация
        print(f"🔍 Проверка типа контента: {participant}, задание {task_index + 1}")
        print(f"   Ожидается: {expected_type}, получено: {content_type}")
        
        if expected_type == "photo" and content_type == "photo":
            result = True
        elif expected_type == "video" and content_type == "video":
            result = True
        elif expected_type == "media" and content_type in ["photo", "video"]:
            result = True
        elif expected_type == "text" and content_type == "text":
            result = True
        else:
            result = False
        
        print(f"   Результат проверки: {result}")
        return result
    
    print(f"🔍 Проверка типа контента: {participant}, задание {task_index + 1} - тип не указан, принимаем любой")
    return True  # Если тип не указан, принимаем любой

@dp.message(F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    """Обработчик загруженных фотографий"""
    data = await state.get_data()
    participant = data.get('participant')
    
    if not participant:
        await message.answer("Сначала выбери свое имя!")
        return
    
    current_task = participants_data[participant]['current_task']
    
    # Проверяем, подходит ли фото для этого задания
    if not check_content_type(participant, current_task, "photo"):
        await message.answer("❌ Для этого задания нужен другой тип контента!")
        return
    
    # Сохраняем фото
    photo_info = await bot.get_file(message.photo[-1].file_id)
    photo_path = f"static/{participant}_photo_{current_task}.jpg"
    
    # Скачиваем фото
    await bot.download_file(photo_info.file_path, photo_path)
    
    # Сохраняем ответ
    participants_data[participant]['answers'][current_task] = photo_path
    participants_data[participant]['completed_tasks'].append(current_task)
    participants_data[participant]['current_task'] += 1
    
    # Сохраняем данные после изменения
    save_data()
    
    # Проверяем, не последнее ли это задание
    if participants_data[participant]['current_task'] >= len(TASKS[participant]):
        # Последнее задание выполнено - не показываем "следующее задание"
        await message.answer("🎉 Ты очень классно постаралась! Подожди остальных девочек или помоги им в выполнении заданий. А потом все вместе узнайте у координатора Виолетты куда же она дела подарки???")
    else:
        encouragement = get_encouragement_message()
        await message.answer(f"{encouragement}\n\n📋 Следующее задание для тебя:")
        await show_task(message, participant, participants_data[participant]['current_task'])

@dp.message(F.video)
async def handle_video(message: types.Message, state: FSMContext):
    """Обработчик загруженных видео"""
    data = await state.get_data()
    participant = data.get('participant')
    
    if not participant:
        await message.answer("Сначала выбери свое имя!")
        return
    
    current_task = participants_data[participant]['current_task']
    
    # Проверяем, подходит ли видео для этого задания
    if not check_content_type(participant, current_task, "video"):
        await message.answer("❌ Для этого задания нужен другой тип контента!")
        return
    
    # Сохраняем видео
    video_info = await bot.get_file(message.video.file_id)
    video_path = f"static/{participant}_video_{current_task}.mp4"
    
    # Скачиваем видео
    await bot.download_file(video_info.file_path, video_path)
    
    # Сохраняем ответ
    participants_data[participant]['answers'][current_task] = video_path
    participants_data[participant]['completed_tasks'].append(current_task)
    participants_data[participant]['current_task'] += 1
    
    # Сохраняем данные после изменения
    save_data()
    
    # Проверяем, не последнее ли это задание
    if participants_data[participant]['current_task'] >= len(TASKS[participant]):
        # Последнее задание выполнено - не показываем "следующее задание"
        await message.answer("🎉 Ты очень классно постаралась! Подожди остальных девочек или помоги им в выполнении заданий. А потом все вместе узнайте у координатора Виолетты куда же она дела подарки???")
    else:
        encouragement = get_encouragement_message()
        await message.answer(f"{encouragement}\n\n📋 Следующее задание для тебя:")
        await show_task(message, participant, participants_data[participant]['current_task'])

@dp.message(F.text)
async def handle_text(message: types.Message, state: FSMContext):
    """Обработчик текстовых сообщений"""
    # Проверяем, не является ли сообщение командой
    if message.text.startswith('/'):
        return  # Пропускаем команды, пусть их обрабатывают другие хендлеры
    
    data = await state.get_data()
    participant = data.get('participant')
    
    if not participant:
        await message.answer("Сначала выбери свое имя!")
        return
    
    current_task = participants_data[participant]['current_task']
    
    # Отладочная информация
    print(f"🔍 Обработка текста: {participant}, задание {current_task + 1}")
    print(f"   Текст: '{message.text}'")
    print(f"   Тип контента для задания: {TASK_CONTENT_TYPES.get(participant, ['не указан'])[current_task] if participant in TASK_CONTENT_TYPES and current_task < len(TASK_CONTENT_TYPES[participant]) else 'не указан'}")
    
    # Специальная обработка для Натальи в задании "Миссия невыполнима"
    if participant == "Наталья" and current_task == 2:
        # Любой текст завершает это задание
        participants_data[participant]['completed_tasks'].append(current_task)
        participants_data[participant]['answers'][current_task] = message.text
        participants_data[participant]['current_task'] += 1
        
        # Сбрасываем счетчик нажатий
        if participant in mission_impossible_clicks:
            mission_impossible_clicks[participant] = 0
        
        # Сохраняем данные после изменения
        save_data()
        
        # Проверяем, не последнее ли это задание
        if participants_data[participant]['current_task'] >= len(TASKS[participant]):
            await message.answer("🎉 Ты очень классно постаралась! Подожди остальных девочек или помоги им в выполнении заданий. А потом все вместе узнайте у координатора Виолетты куда же она дела подарки???")
        else:
            encouragement = get_encouragement_message()
            await message.answer(f"{encouragement}\n\n📋 Следующее задание для тебя:")
            await show_task(message, participant, participants_data[participant]['current_task'])
        return
    
    # Проверяем, подходит ли текст для этого задания
    if not check_content_type(participant, current_task, "text"):
        await message.answer("❌ Для этого задания нужен другой тип контента (фото или видео)!")
        return
    
    # Проверяем правильность ответа если есть
    if participant in CORRECT_ANSWERS and current_task in CORRECT_ANSWERS[participant]:
        correct_answer = CORRECT_ANSWERS[participant][current_task]
        
        # Отладочная информация (только в консоль)
        debug_msg = f"🔍 Проверка ответа для {participant}, задание {current_task + 1}:\n"
        debug_msg += f"Полученный ответ: '{message.text}'\n"
        debug_msg += f"Ожидаемый ответ: '{correct_answer}'\n"
        
        if isinstance(correct_answer, list):
            # Проверяем каждый вариант ответа в нижнем регистре
            user_text_lower = message.text.lower().strip()
            is_correct = any(answer.lower().strip() in user_text_lower for answer in correct_answer)
            debug_msg += f"Тип: список, результат: {is_correct}"
        else:
            # Если правильный ответ "любой ответ", то принимаем любой текст
            if correct_answer == "любой ответ":
                is_correct = True
                debug_msg += f"Тип: любой ответ, результат: {is_correct}"
            else:
                # Проверяем точный ответ в нижнем регистре
                user_text_lower = message.text.lower().strip()
                correct_answer_lower = correct_answer.lower().strip()
                is_correct = correct_answer_lower in user_text_lower
                debug_msg += f"Тип: точный ответ, результат: {is_correct}"
        
        # Отладочная информация только в консоль
        print(debug_msg)
        
        if is_correct:
            await message.answer("✅ Правильно! Задание выполнено!")
        else:
            await message.answer("❌ Попробуй еще раз!")
            return
    
    # Сохраняем ответ
    participants_data[participant]['answers'][current_task] = message.text
    participants_data[participant]['completed_tasks'].append(current_task)
    participants_data[participant]['current_task'] += 1
    
    # Сохраняем данные после изменения
    save_data()
    
    # Проверяем, не последнее ли это задание
    if participants_data[participant]['current_task'] >= len(TASKS[participant]):
        # Последнее задание выполнено - не показываем "следующее задание"
        await message.answer("🎉 Ты очень классно постаралась! Подожди остальных девочек или помоги им в выполнении заданий. А потом все вместе узнайте у координатора Виолетты куда же она дела подарки???")
    else:
        encouragement = get_encouragement_message()
        await message.answer(f"{encouragement}\n\n📋 Следующее задание для тебя:")
        await show_task(message, participant, participants_data[participant]['current_task'])

@dp.message(Command("answers"))
async def cmd_answers(message: types.Message):
    """Команда для просмотра ответов участников (только для администратора)"""
    # Отладочная информация
    debug_info = f"🔍 Отладка:\n"
    debug_info += f"participants_data: {participants_data}\n"
    debug_info += f"Тип данных: {type(participants_data)}\n"
    debug_info += f"Количество ключей: {len(participants_data) if participants_data else 0}\n"
    debug_info += f"Файл данных: {DATA_FILE}\n"
    debug_info += f"Файл существует: {os.path.exists(DATA_FILE)}\n"
    
    if not participants_data:
        await message.answer(f"{debug_info}\n\n❌ Пока нет ответов от участников.")
        return
    
    response = "📊 Ответы участников:\n\n"
    
    for participant, data in participants_data.items():
        # Добавляем эмодзи к имени участника для красоты
        emoji_map = {
            "Наталья": "👸",
            "Юлия Иванова": "🌟", 
            "Анастасия": "💫",
            "Анна": "🌸",
            "Юлия Кузнецова": "✨",
            "Ольга": "🌺"
        }
        emoji = emoji_map.get(participant, "👤")
        
        response += f"{emoji} {participant}:\n"
        response += f"   Выполнено заданий: {len(data['completed_tasks'])}/{len(TASKS[participant])}\n"
        
        for task_num, answer in data['answers'].items():
            if isinstance(answer, str) and (answer.endswith('.jpg') or answer.endswith('.mp4')):
                response += f"   📷 Задание {task_num + 1}: Файл {answer}\n"
            else:
                response += f"   💬 Задание {task_num + 1}: {answer}\n"
        
        response += "\n"
    
    # Добавляем отладочную информацию в конец
    response += f"\n{debug_info}"
    
    # Разбиваем на части если сообщение слишком длинное
    if len(response) > 4096:
        parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
        for part in parts:
            await message.answer(part)
    else:
        await message.answer(response)

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    """Команда для сброса данных (только для администратора)"""
    global participants_data, mission_impossible_clicks
    participants_data = {}
    mission_impossible_clicks = {}
    save_data()
    await message.answer("Данные участников сброшены.")

@dp.message(Command("next_task"))
async def cmd_next_task(message: types.Message, state: FSMContext):
    """Команда для принудительного перехода к следующему заданию"""
    data = await state.get_data()
    participant = data.get('participant')
    
    if not participant:
        await message.answer("❌ Сначала выбери свое имя!")
        return
    
    if participant not in participants_data:
        await message.answer("❌ Данные участника не найдены!")
        return
    
    current_task = participants_data[participant]['current_task']
    
    if current_task >= len(TASKS[participant]):
        await message.answer("�� Все задания уже выполнены!")
        return
    
    # Принудительно переходим к следующему заданию
    participants_data[participant]['current_task'] += 1
    save_data()
    
    await message.answer(f"✅ Принудительно переходим к заданию {participants_data[participant]['current_task'] + 1}")
    await show_task(message, participant, participants_data[participant]['current_task'])

@dp.message(Command("reset_clicks"))
async def cmd_reset_clicks(message: types.Message, state: FSMContext):
    """Команда для сброса счетчика нажатий кнопки 'Миссия невыполнима'"""
    data = await state.get_data()
    participant = data.get('participant')
    
    if not participant:
        await message.answer("❌ Сначала выбери свое имя!")
        return
    
    if participant in mission_impossible_clicks:
        mission_impossible_clicks[participant] = 0
        save_data()
        await message.answer(f"✅ Счетчик нажатий для {participant} сброшен!")
    else:
        await message.answer(f"ℹ️ У {participant} нет активного счетчика нажатий")

@dp.message(Command("save"))
async def cmd_save(message: types.Message):
    """Команда для принудительного сохранения данных"""
    save_data()
    await message.answer("💾 Данные принудительно сохранены!")

@dp.message(Command("test_data"))
async def cmd_test_data(message: types.Message):
    """Команда для тестирования сохранения данных"""
    # Создаем тестовые данные
    global participants_data
    
    if "Наталья" not in participants_data:
        participants_data["Наталья"] = {
            'current_task': 1,
            'completed_tasks': [0],
            'answers': {0: "Тестовый ответ для Натальи"}
        }
        save_data()
        await message.answer("✅ Тестовые данные для Натальи созданы и сохранены!")
    else:
        await message.answer("ℹ️ Тестовые данные уже существуют")
    
    # Показываем текущее состояние
    await message.answer(f"📊 Текущее состояние:\n{participants_data}")

@dp.message(Command("clear_state"))
async def cmd_clear_state(message: types.Message):
    """Команда для сброса состояния пользователя"""
    # Сбрасываем состояние для текущего пользователя
    state = dp.fsm.get_context(bot=bot, user_id=message.from_user.id, chat_id=message.chat.id)
    await state.clear()
    await message.answer("✅ Твое состояние сброшено! Теперь можешь использовать /start заново или команды администратора.")

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Команда для просмотра статуса участников"""
    if not participants_data:
        await message.answer("Пока нет активных участников.")
        return
    
    response = "📈 Статус участников:\n\n"
    
    for participant, data in participants_data.items():
        completed = len(data['completed_tasks'])
        total = len(TASKS[participant])
        response += f"👤 {participant}: {completed}/{total} заданий выполнено\n"
    
    await message.answer(response)

async def main():
    """Главная функция"""
    print("Бот запущен...")
    print(f"📁 Файл данных: {DATA_FILE}")
    print(f"📊 Загружено участников: {len(participants_data)}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
