import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "8593909892:AAHs6qWVMLnFJeHpcWMnqslDanF6JgLFEsQ"  # Ваш токен
SCHEDULE_URL = "https://raspisanie.nikasoft.ru/15312761.html#cls"

subscribers = set()
last_update_text = None
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
        print(f"Ошибка: {e}")
        return None

def is_today_update(update_text):
    """Проверка, обновлено сегодня"""
    if not update_text:
        return False
    return 'сегодня' in update_text.lower()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подписка на уведомления"""
    user_id = update.effective_chat.id
    subscribers.add(user_id)
    
    # Сохраняем в файл
    with open("subscribers.txt", "w") as f:
        for uid in subscribers:
            f.write(f"{uid}\n")
    
    await update.message.reply_text(
        "✅ *Вы подписаны на уведомления!*\n\n"
        "📌 *Команды:*\n"
        "/status — последнее обновление\n"
        "/unsubscribe — отписаться",
        parse_mode="Markdown"
    )

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отписка от уведомлений"""
    user_id = update.effective_chat.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        with open("subscribers.txt", "w") as f:
            for uid in subscribers:
                f.write(f"{uid}\n")
        await update.message.reply_text("❌ *Вы отписались от уведомлений*", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ *Вы не были подписаны*", parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать последнее обновление"""
    update_text = get_last_update_text()
    if update_text:
        await update.message.reply_text(f"📅 *Последнее обновление:* {update_text}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ *Не удалось получить информацию*", parse_mode="Markdown")

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    """Периодическая проверка и рассылка"""
    global last_update_text
    
    current_update = get_last_update_text()
    if not current_update:
        return
    
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
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
                print(f"✅ Уведомление отправлено {user_id}")
            except Exception as e:
                print(f"❌ Ошибка отправки {user_id}: {e}")

def load_subscribers():
    """Загрузка списка подписчиков из файла"""
    try:
        with open("subscribers.txt", "r") as f:
            for line in f:
                if line.strip():
                    subscribers.add(int(line.strip()))
        print(f"✅ Загружено подписчиков: {len(subscribers)}")
    except FileNotFoundError:
        print("📭 Файл с подписчиками не найден, начинаем с нуля")

def main():
    # Загружаем подписчиков
    load_subscribers()
    
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Настраиваем периодическую проверку (каждые 5 минут)
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(check_and_notify, interval=300, first=10)
        print("⏰ Планировщик запущен (проверка каждые 5 минут)")
    else:
        print("⚠️ JobQueue не доступен, проверка не запущена")
        print("Попробуйте установить: pip install python-telegram-bot[job-queue]")
        return
    
    print("🤖 Бот запущен и готов к работе!")
    print("📱 Найдите бота в Telegram и напишите /start")
    
    # Запускаем бота
    app.run_polling()

if __name__ == "__main__":
    main()
