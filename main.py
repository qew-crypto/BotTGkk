import asyncio
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "8593909892:AAHs6qWVMLnFJeHpcWMnqslDanF6JgLFEsQ"  # Ваш токен
SCHEDULE_URL = "https://raspisanie.nikasoft.ru/15312761.html#cls"

subscribers = set()
last_update_text = None

# Создаём бота и диспетчер
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
# =================================

def get_last_update_text():
    """Получает текст с датой обновления"""
    try:
        response = requests.get(SCHEDULE_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем текст "Обновлено"
        for element in soup.find_all(string=re.compile(r'Обновлено')):
            text = element.strip()
            match = re.search(r'Обновлено\s+(.+?)(?:\s|$)', text)
            if match:
                return match.group(1).strip()
        return None
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return None

def is_today_update(update_text):
    """Проверка, обновлено сегодня"""
    if not update_text:
        return False
    return 'сегодня' in update_text.lower()

def load_subscribers():
    """Загрузка списка подписчиков"""
    global subscribers
    try:
        with open("subscribers.txt", "r") as f:
            for line in f:
                if line.strip():
                    subscribers.add(int(line.strip()))
        print(f"✅ Загружено подписчиков: {len(subscribers)}")
    except FileNotFoundError:
        print("📭 Новый файл подписчиков")

def save_subscribers():
    """Сохранение подписчиков"""
    with open("subscribers.txt", "w") as f:
        for uid in subscribers:
            f.write(f"{uid}\n")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Подписка на уведомления"""
    user_id = message.chat.id
    subscribers.add(user_id)
    save_subscribers()
    
    await message.answer(
        "✅ *Вы подписаны на уведомления!*\n\n"
        "📌 *Команды:*\n"
        "/status — последнее обновление\n"
        "/unsubscribe — отписаться",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    """Отписка от уведомлений"""
    user_id = message.chat.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        save_subscribers()
        await message.answer("❌ *Вы отписались от уведомлений*", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("ℹ️ *Вы не были подписаны*", parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("status"))
async def cmd_status(message: Message):
    """Показать последнее обновление"""
    update_text = get_last_update_text()
    if update_text:
        await message.answer(f"📅 *Последнее обновление:* {update_text}", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("❌ *Не удалось получить информацию*", parse_mode=ParseMode.MARKDOWN)

async def check_and_notify():
    """Периодическая проверка и рассылка"""
    global last_update_text
    
    while True:
        try:
            current_update = get_last_update_text()
            if current_update:
                print(f"[{datetime.now()}] Обновление: {current_update}")
                
                # Если новое обновление сегодня и это не то, что уже отправляли
                if is_today_update(current_update) and current_update != last_update_text:
                    last_update_text = current_update
                    
                    message = (
                        f"📢 *НОВОЕ ОБНОВЛЕНИЕ РАСПИСАНИЯ!*\n\n"
                        f"📅 Обновлено {current_update}\n\n"
                        f"🔗 [Смотреть расписание]({SCHEDULE_URL})"
                    )
                    
                    # Рассылаем всем подписчикам
                    for user_id in list(subscribers):
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=False
                            )
                            print(f"✅ Уведомление отправлено {user_id}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки {user_id}: {e}")
        except Exception as e:
            print(f"Ошибка в check_and_notify: {e}")
        
        # Ждём 5 минут
        await asyncio.sleep(300)

async def main():
    """Запуск бота"""
    # Загружаем подписчиков
    load_subscribers()
    
    # Запускаем фоновую проверку
    asyncio.create_task(check_and_notify())
    
    print("🤖 Бот запущен на Aiogram!")
    print("⏰ Проверка расписания каждые 5 минут")
    print("📱 Найдите бота в Telegram и напишите /start")
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
