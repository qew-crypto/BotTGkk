import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "8593909892:AAHs6qWVMLnFJeHpcWMnqslDanF6JgLFEsQ"
SCHEDULE_URL = "https://raspisanie.nikasoft.ru/15312761.html#cls"

subscribers = set()
last_update_text = None
# =================================

def get_last_update_text():
    """Получает дату последнего обновления"""
    try:
        response = requests.get(SCHEDULE_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем "Обновлено"
        for element in soup.find_all(string=re.compile(r'Обновлено')):
            text = element.strip()
            match = re.search(r'Обновлено\s+(.+?)(?:\s|$)', text)
            if match:
                return match.group(1).strip()
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def is_today_update(update_text):
    if not update_text:
        return False
    return 'сегодня' in update_text.lower()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    subscribers.add(user_id)
    
    with open("subscribers.txt", "w") as f:
        for uid in subscribers:
            f.write(f"{uid}\n")
    
    await update.message.reply_text(
        "✅ Подписан!\n"
        "/status — последнее обновление\n"
        "/unsubscribe — отписаться"
    )

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        with open("subscribers.txt", "w") as f:
            for uid in subscribers:
                f.write(f"{uid}\n")
        await update.message.reply_text("❌ Отписан")
    else:
        await update.message.reply_text("Вы не подписаны")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_text = get_last_update_text()
    if update_text:
        await update.message.reply_text(f"📅 Обновлено: {update_text}")
    else:
        await update.message.reply_text("❌ Ошибка получения")

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    """Периодическая проверка"""
    global last_update_text
    
    current_update = get_last_update_text()
    if not current_update:
        return
    
    print(f"[{datetime.now()}] Обновление: {current_update}")
    
    if is_today_update(current_update) and current_update != last_update_text:
        last_update_text = current_update
        
        message = (
            f"📢 *НОВОЕ ОБНОВЛЕНИЕ!*\n\n"
            f"Расписание обновлено {current_update}\n\n"
            f"[Смотреть расписание]({SCHEDULE_URL})"
        )
        
        for user_id in list(subscribers):
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка {user_id}: {e}")

def load_subscribers():
    try:
        with open("subscribers.txt", "r") as f:
            for line in f:
                if line.strip():
                    subscribers.add(int(line.strip()))
        print(f"✅ Загружено: {len(subscribers)} подписчиков")
    except FileNotFoundError:
        print("📭 Новый файл подписчиков")

def main():
    load_subscribers()
    
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Настраиваем JobQueue (проверка каждые 5 минут)
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(check_and_notify, interval=300, first=10)
        print("⏰ Планировщик запущен (проверка каждые 5 минут)")
    else:
        print("❌ JobQueue не доступен!")
        return
    
    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
