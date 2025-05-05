import os
import telebot
import json
from datetime import datetime
from telebot import types

# Получаем токен и ID администратора из переменных окружения
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Не задана переменная окружения TELEGRAM_BOT_TOKEN")

ADMIN_ID = os.environ.get('ADMIN_ID')
if not ADMIN_ID:
    raise ValueError("Не задана переменная окружения ADMIN_ID")
try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("Переменная ADMIN_ID должна быть числом")

DATA_FILE = 'messages.json'

bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'morning': [], 'news': []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(
        types.KeyboardButton('➕ Добавить утреннее сообщение'),
        types.KeyboardButton('➕ Добавить новость'),
        types.KeyboardButton('📋 Список утренних сообщений'),
        types.KeyboardButton('📋 Список новостей'),
        types.KeyboardButton('❌ Удалить утреннее сообщение'),
        types.KeyboardButton('❌ Удалить новость')
    )
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return
    text = message.text
    if text == '➕ Добавить утреннее сообщение':
        msg = bot.reply_to(message, "Отправьте текст утреннего сообщения:")
        bot.register_next_step_handler(msg, add_morning)
    elif text == '➕ Добавить новость':
        msg = bot.reply_to(message, "Отправьте текст новости:")
        bot.register_next_step_handler(msg, add_news)
    elif text == '📋 Список утренних сообщений':
        list_morning(message)
    elif text == '📋 Список новостей':
        list_news(message)
    elif text == '❌ Удалить утреннее сообщение':
        bot.reply_to(message, "Введите команду /delete_morning <номер>")
    elif text == '❌ Удалить новость':
        bot.reply_to(message, "Введите команду /delete_news <номер>")
    else:
        bot.reply_to(message, "Неизвестная команда. Используйте кнопки меню.")

def add_morning(message):
    data = load_data()
    data['morning'].append({'text': message.text, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_data(data)
    bot.reply_to(message, "✅ Утреннее сообщение добавлено")

def add_news(message):
    data = load_data()
    data['news'].append({'text': message.text, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_data(data)
    bot.reply_to(message, "✅ Новость добавлена")

def list_morning(message):
    data = load_data()
    if not data['morning']:
        bot.reply_to(message, "Нет утренних сообщений")
        return
    msg = "Утренние сообщения:\n"
    for i, item in enumerate(data['morning'], 1):
        msg += f"{i}. {item['text']} (добавлено {item['timestamp']})\n"
    bot.reply_to(message, msg)

def list_news(message):
    data = load_data()
    if not data['news']:
        bot.reply_to(message, "Нет новостей")
        return
    msg = "Новости:\n"
    for i, item in enumerate(data['news'], 1):
        msg += f"{i}. {item['text']} (добавлено {item['timestamp']})\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['delete_morning'])
def delete_morning(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "Используйте: /delete_morning <номер>")
        return
    idx = int(parts[1]) - 1
    data = load_data()
    if 0 <= idx < len(data['morning']):
        removed = data['morning'].pop(idx)
        save_data(data)
        bot.reply_to(message, f"Удалено утреннее сообщение: {removed['text']}")
    else:
        bot.reply_to(message, "Неверный номер")

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

if __name__ == '__main__':
    bot.polling(none_stop=True)
