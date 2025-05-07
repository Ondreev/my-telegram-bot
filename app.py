import os
import telebot
import json
from datetime import datetime
from flask import Flask, request
from telebot import types
from waitress import serve

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'messages.json')
STATE_FILE = os.path.join(BASE_DIR, 'publish_state.json')

TOKEN = '7784249517:AAGdOGzTyeXHXZj9sE9nuKAzUdCx8u8HPHw'
ADMIN_ID = 530258581
CHANNEL_ID = '@ondreeff'  # Замените на ваш канал

bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'news': []}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")

def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'last_news_index': -1}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f)

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
        msg = bot.reply_to(message, "Отправьте фото или видео с описанием новости:")
        bot.register_next_step_handler(msg, add_media_news)
    elif text == '📋 Список новостей':
        list_news(message)
    elif text == '❌ Удалить новость':
        bot.reply_to(message, "Введите команду /delete_news <номер>")
    else:
        bot.reply_to(message, "Неизвестная команда. Используйте кнопки меню.")

def add_media_news(message):
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id  # Берём фото с максимальным разрешением
        caption = message.caption or ''
        news_item = {
            'type': 'photo',
            'file_id': file_id,
            'caption': caption,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    elif message.content_type == 'video':
        file_id = message.video.file_id
        caption = message.caption or ''
        news_item = {
            'type': 'video',
            'file_id': file_id,
            'caption': caption,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        bot.reply_to(message, "Ошибка: нужно отправить фото или видео с описанием.")
        return

    data = load_data()
    data['news'].append(news_item)
    save_data(data)
    bot.reply_to(message, "✅ Новость с медиа добавлена")

def list_news(message):
    data = load_data()
    if not data['news']:
        bot.reply_to(message, "Нет новостей")
        return
    msg = "Новости:\n"
    for i, item in enumerate(data['news'], 1):
        t = item.get('type', 'text')
        if t == 'photo':
            desc = item.get('caption', '')
            msg += f"{i}. Фото: {desc} (добавлено {item['timestamp']})\n"
        elif t == 'video':
            desc = item.get('caption', '')
            msg += f"{i}. Видео: {desc} (добавлено {item['timestamp']})\n"
        else:
            msg += f"{i}. {item.get('text', '')} (добавлено {item['timestamp']})\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['delete_news'])
def delete_news(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "Используйте: /delete_news <номер>")
        return
    idx = int(parts[1]) - 1
    data = load_data()
    if 0 <= idx < len(data['news']):
        removed = data['news'].pop(idx)
        save_data(data)
        bot.reply_to(message, f"Удалена новость #{idx+1}")
    else:
        bot.reply_to(message, "Неверный номер")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

@app.route('/publish_news')
def publish_news():
    data = load_data()
    state = load_state()
    news_list = data.get('news', [])
    if not news_list:
        return "Нет новостей для публикации"

    next_index = (state['last_news_index'] + 1) % len(news_list)
    news = news_list[next_index]

    try:
        if news['type'] == 'photo':
            bot.send_photo(CHANNEL_ID, news['file_id'], caption=news.get('caption', ''))
        elif news['type'] == 'video':
            bot.send_video(CHANNEL_ID, news['file_id'], caption=news.get('caption', ''))
        else:
            bot.send_message(CHANNEL_ID, news.get('text', ''))
        state['last_news_index'] = next_index
        save_state(state)
        return f"Опубликована новость #{next_index + 1}"
    except Exception as e:
        return f"Ошибка при публикации: {e}"

@app.route('/')
def home():
    return "Бот работает. Используйте /webhook для Telegram API"

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://my-telegram-bot-vogy.onrender.com/webhook')  # Замените на ваш URL Render
    serve(app, host='0.0.0.0', port=5000)
