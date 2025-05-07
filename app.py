import os
import telebot
import json
from datetime import datetime
from flask import Flask
from threading import Thread
from telebot import types

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'messages.json')
STATE_FILE = os.path.join(BASE_DIR, 'publish_state.json')

TOKEN = '7784249517:AAGdOGzTyeXHXZj9sE9nuKAzUdCx8u8HPHw'  # Ваш токен
ADMIN_ID = 530258581  # Ваш Telegram ID
CHANNEL_ID = '@your_channel_username'  # Замените на ваш канал или ID

bot = telebot.TeleBot(TOKEN)

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

# --- Обработчики бота ---

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
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return
    text = message.text
    if text == '➕ Добавить новость':
        msg = bot.reply_to(message, "Отправьте текст новости:")
        bot.register_next_step_handler(msg, add_news)
    elif text == '📋 Список новостей':
        list_news(message)
    elif text == '❌ Удалить новость':
        bot.reply_to(message, "Введите команду /delete_news <номер>")
    else:
        bot.reply_to(message, "Неизвестная команда. Используйте кнопки меню.")

def add_news(message):
    data = load_data()
    data['news'].append({'text': message.text, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_data(data)
    bot.reply_to(message, "✅ Новость добавлена")

def list_news(message):
    data = load_data()
    if not data['news']:
        bot.reply_to(message, "Нет новостей")
        return
    msg = "Новости:\n"
    for i, item in enumerate(data['news'], 1):
        msg += f"{i}. {item['text']} (добавлено {item['timestamp']})\n"
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
        bot.reply_to(message, f"Удалена новость: {removed['text']}")
    else:
        bot.reply_to(message, "Неверный номер")

# --- Веб-сервис для публикации ---

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

# --- Запуск бота и веб-сервера параллельно ---

def run_bot():
    bot.polling(none_stop=True)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    from threading import Thread
    Thread(target=run_bot).start()
    run_flask()
