import os
import telebot
import json
from datetime import datetime
from telebot import types

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'messages.json')

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

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
        print("Данные успешно сохранены")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")

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

if __name__ == '__main__':
    bot.polling(none_stop=True)
