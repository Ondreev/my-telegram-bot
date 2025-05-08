import requests
import json
from datetime import datetime
from flask import Flask, request
import telebot
from telebot import types
from waitress import serve

app = Flask(__name__)

# Ваш OAuth-токен Яндекс.Диска
YANDEX_TOKEN = "8b118b42c4a84a12b73693e706ed53fe"
DATA_FILE = "bot_data.json"  # Имя файла на Яндекс.Диске для хранения данных

# Ваш Telegram токен и настройки
TOKEN = '7784249517:AAFZdcmFknfTmAf17N2wTifmCoF54BQkeZU'
ADMIN_ID = 530258581
CHANNEL_ID = '@ondreeff'  # Замените на ваш канал, например '@mychannel'

bot = telebot.TeleBot(TOKEN)

def save_to_yadisk(data):
    headers = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
    url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    params = {
        "path": f"/{DATA_FILE}",
        "overwrite": "true"
    }
    response = requests.get(url, headers=headers, params=params)
    upload_url = response.json().get("href")
    response = requests.put(upload_url, data=json.dumps(data))
    return response.status_code == 201

def load_from_yadisk():
    headers = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
    url = "https://cloud-api.yandex.net/v1/disk/resources/download"
    params = {"path": f"/{DATA_FILE}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        download_url = response.json().get("href")
        data = requests.get(download_url).json()
        return data
    except:
        return {"news": [], "last_news_id": 0}

def add_news(news_type, content, caption=None):
    data = load_from_yadisk()
    data["news"].append({
        "type": news_type,
        "content": content,
        "caption": caption,
        "timestamp": datetime.now().isoformat()
    })
    save_to_yadisk(data)

def get_all_news():
    return load_from_yadisk().get("news", [])

def delete_news_by_id(news_id):
    data = load_from_yadisk()
    news_list = data.get("news", [])
    filtered_news = [n for idx, n in enumerate(news_list, 1) if idx != news_id]
    data["news"] = filtered_news
    save_to_yadisk(data)

def get_publish_state():
    return load_from_yadisk().get("last_news_id", 0)

def update_publish_state(news_id):
    data = load_from_yadisk()
    data["last_news_id"] = news_id
    save_to_yadisk(data)

def is_admin(user_id):
    return user_id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
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
    if not is_admin(message.from_user.id):
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
    for idx, item in enumerate(news, 1):
        news_type = item.get("type")
        content = item.get("content")
        caption = item.get("caption")
        timestamp = item.get("timestamp", "")
        if news_type == 'photo':
            desc = caption if caption else "Без описания"
            response += f"{idx}. 📷 Фото: {desc} ({timestamp})\n"
        elif news_type == 'video':
            desc = caption if caption else "Без описания"
            response += f"{idx}. 🎥 Видео: {desc} ({timestamp})\n"
        else:
            response += f"{idx}. 📝 {content} ({timestamp})\n"

    bot.reply_to(message, response)

@bot.message_handler(commands=['delete_news'])
def handle_delete_news(message):
    if not is_admin(message.from_user.id):
        return

    try:
        news_id = int(message.text.split()[1])
        delete_news_by_id(news_id)
        bot.reply_to(message, f"✅ Новость #{news_id} удалена")
    except (IndexError, ValueError):
        bot.reply_to(message, "Используйте: /delete_news <номер>")

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
    next_id = (last_id % len(news)) + 1

    if next_id > len(news):
        return "Ошибка: новость не найдена"

    item = news[next_id - 1]
    news_type = item.get("type")
    content = item.get("content")
    caption = item.get("caption")

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
