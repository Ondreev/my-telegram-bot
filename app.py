import os
import telebot
import json
from datetime import datetime
from flask import Flask, request
from telebot import types

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'messages.json')
STATE_FILE = os.path.join(BASE_DIR, 'publish_state.json')

TOKEN = '7784249517:AAGdOGzTyeXHXZj9sE9nuKAzUdCx8u8HPHw'
ADMIN_ID = 530258581
CHANNEL_ID = '@ondreeff'  # Замените на ваш канал

bot = telebot.TeleBot(TOKEN)

# Отключаем вебхук при старте (на всякий случай)
bot.remove_webhook()

# --- Функции для работы с данными ---
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

# --- Обработчики команд бота ---
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

# ... (остальные обработчики остаются без изменений)

# --- Вебхук обработчик ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

# --- Публикация новостей ---
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
        bot.send_message(CHANNEL_ID, news['text'])
        state['last_news_index'] = next_index
        save_state(state)
        return f"Опубликована новость #{next_index + 1}"
    except Exception as e:
        return f"Ошибка при публикации: {e}"

if __name__ == '__main__':
    # Устанавливаем вебхук при запуске
    bot.remove_webhook()
    bot.set_webhook(url='https://my-telegram-bot-vogy.onrender.com/webhook')
    app.run(host='0.0.0.0', port=5000)
