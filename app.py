import os
import telebot
import sqlite3
from datetime import datetime
from flask import Flask, request
from telebot import types
from waitress import serve

app = Flask(__name__)

# Настройки базы данных (файл news.db в текущей директории)
DATABASE = "news.db"
TOKEN = '7784249517:AAFZdcmFknfTmAf17N2wTifmCoF54BQkeZU'
ADMIN_ID = 530258581
CHANNEL_ID = '@ondreeff'  # Замените на ваш канал

bot = telebot.TeleBot(TOKEN)

# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Таблица для новостей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,  -- 'text', 'photo', 'video'
            content TEXT,        -- Текст или file_id для медиа
            caption TEXT,        -- Описание для медиа
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Таблица для отслеживания состояния публикации
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publish_state (
            last_news_id INTEGER DEFAULT 0
        )
    ''')
    # Убедимся, что таблица publish_state имеет начальное значение
    cursor.execute('INSERT OR IGNORE INTO publish_state (last_news_id) VALUES (0)')
    conn.commit()
    conn.close()

init_db()  # Создаём таблицы при старте

# --- Функции для работы с базой ---
def add_news(news_type, content, caption=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO news (type, content, caption) VALUES (?, ?, ?)',
        (news_type, content, caption)
    )
    conn.commit()
    conn.close()

def get_all_news():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news ORDER BY timestamp DESC')
    news = cursor.fetchall()
    conn.close()
    return news

def delete_news(news_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()

def get_publish_state():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT last_news_id FROM publish_state LIMIT 1')
    state = cursor.fetchone()[0]
    conn.close()
    return state

def update_publish_state(news_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE publish_state SET last_news_id = ?', (news_id,))
    conn.commit()
    conn.close()

# --- Обработчики команд бота ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('➕ Добавить новость'),
        types.KeyboardButton('📋 Список новостей'),
        types.KeyboardButton('❌ Удалить новость')
    )
    bot.reply_to(message, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return
    text = message.text
    if text == '➕ Добавить новость':
        msg = bot.reply_to(
            message,
            "Отправьте текст, фото или видео с описанием:\n"
            "⚠️ Для фото/видео описание пишите в поле 'Описание'"
        )
        bot.register_next_step_handler(msg, process_news_input)
    elif text == '📋 Список новостей':
        show_news_list(message)
    elif text == '❌ Удалить новость':
        bot.reply_to(message, "Введите команду /delete_news <номер>")
    else:
        bot.reply_to(message, "Неизвестная команда. Используйте кнопки меню.")

def process_news_input(message):
    if message.content_type == 'text':
        add_news('text', message.text)
        bot.reply_to(message, "✅ Текстовая новость добавлена")
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        caption = message.caption or ''
        add_news('photo', file_id, caption)
        bot.reply_to(message, "✅ Новость с фото добавлена")
    elif message.content_type == 'video':
        file_id = message.video.file_id
        caption = message.caption or ''
        add_news('video', file_id, caption)
        bot.reply_to(message, "✅ Новость с видео добавлена")
    else:
        bot.reply_to(message, "❌ Неподдерживаемый формат. Отправьте текст, фото или видео.")

def show_news_list(message):
    news = get_all_news()
    if not news:
        bot.reply_to(message, "Нет новостей")
        return

    response = "📰 Список новостей:\n"
    for item in news:
        news_id, news_type, content, caption, timestamp = item
        if news_type == 'photo':
            desc = caption if caption else "Без описания"
            response += f"{news_id}. 📷 Фото: {desc} ({timestamp})\n"
        elif news_type == 'video':
            desc = caption if caption else "Без описания"
            response += f"{news_id}. 🎥 Видео: {desc} ({timestamp})\n"
        else:
            response += f"{news_id}. 📝 {content} ({timestamp})\n"

    bot.reply_to(message, response)

@bot.message_handler(commands=['delete_news'])
def handle_delete_news(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        news_id = int(message.text.split()[1])
        delete_news(news_id)
        bot.reply_to(message, f"✅ Новость #{news_id} удалена")
    except (IndexError, ValueError):
        bot.reply_to(message, "Используйте: /delete_news <номер>")

# --- Вебхук и публикация ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid request', 400

@app.route('/publish_news')
def publish_news():
    news = get_all_news()
    if not news:
        return "Нет новостей для публикации"

    last_id = get_publish_state()
    next_id = (last_id % len(news)) + 1  # Циклическая ротация

    # Находим новость по следующему ID
    target_news = None
    for item in news:
        if item[0] == next_id:
            target_news = item
            break

    if not target_news:
        return "Ошибка: новость не найдена"

    news_type, content, caption = target_news[1], target_news[2], target_news[3]

    try:
        if news_type == 'photo':
            bot.send_photo(CHANNEL_ID, content, caption=caption)
        elif news_type == 'video':
            bot.send_video(CHANNEL_ID, content, caption=caption)
        else:
            bot.send_message(CHANNEL_ID, content)

        update_publish_state(next_id)
        return f"✅ Опубликована новость #{next_id}"
    except Exception as e:
        return f"Ошибка публикации: {str(e)}"

@app.route('/')
def home():
    return "Бот работает. Используйте /webhook для Telegram API"

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://my-telegram-bot-vogy.onrender.com/webhook')  # Замените на ваш URL Render
    serve(app, host='0.0.0.0', port=5000)
