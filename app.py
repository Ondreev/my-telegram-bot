import requests
import json
from datetime import datetime
from flask import Flask, request
import telebot
from telebot import types
from waitress import serve
import threading
import logging
import functools
import time
from requests.exceptions import RequestException

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Константы
YANDEX_TOKEN = "y0__xDPlq0MGOvNNyCmidiHEwSCRFd3yNjmWuWOnADjLKvDPt5B"
DATA_FILE = "bot_data.json"
TOKEN = '7784249517:AAFZdcmFknfTmAf17N2wTifmCoF54BQkeZU'
ADMIN_ID = 530258581
CHANNEL_ID = '@ondreeff'  # Замените на ваш канал
TIMEOUT = 30  # секунд

bot = telebot.TeleBot(TOKEN)

# Кэш для данных
data_cache = {
    'data': None,
    'timestamp': 0,
    'lock': threading.Lock()
}

def save_to_yadisk(data):
    headers = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
    url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    params = {"path": f"/{DATA_FILE}", "overwrite": "true"}
    try:
        logger.info("Начало сохранения данных на Яндекс.Диск")
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        upload_url = response.json().get("href")
        if not upload_url:
            logger.error("Не получен URL для загрузки")
            return False

        put_response = requests.put(upload_url, data=json.dumps(data), timeout=TIMEOUT)
        put_response.raise_for_status()
        logger.info("Данные успешно сохранены на Яндекс.Диск")
        return True
    except RequestException as e:
        logger.error(f"Ошибка сети при сохранении: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при сохранении: {e}")
        return False

def load_from_yadisk():
    with data_cache['lock']:
        current_time = time.time()
        if data_cache['data'] and current_time - data_cache['timestamp'] < 300:
            return data_cache['data']

        headers = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
        url = "https://cloud-api.yandex.net/v1/disk/resources/download"
        params = {"path": f"/{DATA_FILE}"}
        try:
            logger.info("Загрузка данных с Яндекс.Диска")
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            download_url = response.json().get("href")
            if not download_url:
                logger.error("Не получен URL для скачивания")
                return {"news": [], "last_news_id": 0}

            data_response = requests.get(download_url, timeout=TIMEOUT)
            data_response.raise_for_status()
            data = data_response.json()

            # Обновляем кэш
            data_cache['data'] = data
            data_cache['timestamp'] = current_time

            logger.info(f"Данные загружены, новостей: {len(data.get('news', []))}")
            return data
        except RequestException as e:
            logger.error(f"Ошибка сети при загрузке: {e}")
            return {"news": [], "last_news_id": 0}
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке: {e}")
            return {"news": [], "last_news_id": 0}

def async_save_to_yadisk(data):
    def _save():
        try:
            save_to_yadisk(data)
        except Exception as e:
            logger.error(f"Ошибка при асинхронном сохранении: {e}")

    thread = threading.Thread(target=_save)
    thread.start()

def add_news(news_type, content, caption=None):
    data = load_from_yadisk()
    if "news" not in data:
        data["news"] = []
    data["news"].append({
        "type": news_type,
        "content": content,
        "caption": caption,
        "timestamp": datetime.now().isoformat()
    })
    async_save_to_yadisk(data)
    logger.info("Новость добавлена")

def get_all_news():
    data = load_from_yadisk()
    return data.get("news", [])

def delete_news_by_id(news_id):
    data = load_from_yadisk()
    news_list = data.get("news", [])
    if 1 <= news_id <= len(news_list):
        removed = news_list.pop(news_id - 1)
        data["news"] = news_list
        async_save_to_yadisk(data)
        logger.info(f"Новость #{news_id} удалена")
        return True
    return False

def get_publish_state():
    data = load_from_yadisk()
    return data.get("last_news_id", 0)

def update_publish_state(news_id):
    data = load_from_yadisk()
    data["last_news_id"] = news_id
    async_save_to_yadisk(data)

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
    try:
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
    except Exception as e:
        logger.error(f"Ошибка при обработке новости: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при добавлении новости")

def show_news_list(message):
    try:
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
    except Exception as e:
        logger.error(f"Ошибка при показе списка новостей: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при получении списка новостей")

@bot.message_handler(commands=['delete_news'])
def handle_delete_news(message):
    if not is_admin(message.from_user.id):
        return

    try:
        news_id = int(message.text.split()[1])
        if delete_news_by_id(news_id):
            bot.reply_to(message, f"✅ Новость #{news_id} удалена")
        else:
            bot.reply_to(message, "Ошибка: новость с таким номером не найдена")
    except (IndexError, ValueError):
        bot.reply_to(message, "Используйте: /delete_news <номер>")
    except Exception as e:
        logger.error(f"Ошибка при удалении новости: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при удалении новости")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_json())
        threading.Thread(target=bot.process_new_updates, args=([update],)).start()
        return '', 200
    return 'Invalid request', 400

@app.route('/publish_news')
def publish_news():
    try:
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

        if news_type == 'photo':
            bot.send_photo(CHANNEL_ID, content, caption=caption)
        elif news_type == 'video':
            bot.send_video(CHANNEL_ID, content, caption=caption)
        else:
            bot.send_message(CHANNEL_ID, content)

        update_publish_state(next_id)
        return f"✅ Опубликована новость #{next_id}"
    except Exception as e:
        logger.error(f"Ошибка при публикации новости: {e}")
        return f"Ошибка публикации: {str(e)}"

@app.route('/')
def home():
    return "Бот работает. Используйте /webhook для Telegram API"

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://my-telegram-bot-vogy.onrender.com/webhook')
    serve(app, host='0.0.0.0', port=5000, threads=4)
