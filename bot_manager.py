import os
import telebot
import json
from datetime import datetime
from telebot import types

# Конфигурация
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не задан TELEGRAM_BOT_TOKEN в переменных окружения")

DATA_FILE = 'messages.json'
ADMIN_ID = 530258581  # Ваш ID администратора

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Загрузка данных
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'morning': [], 'news': []}

# Сохранение данных
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Проверка прав администратора
def is_admin(user_id):
    return user_id == ADMIN_ID

# Команда /start с русскими кнопками
@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn1 = types.KeyboardButton('➕ Добавить утреннее сообщение')
    btn2 = types.KeyboardButton('➕ Добавить новость')
    btn3 = types.KeyboardButton('📋 Список утренних сообщений')
    btn4 = types.KeyboardButton('📋 Список новостей')
    btn5 = types.KeyboardButton('❌ Удалить утреннее сообщение')
    btn6 = types.KeyboardButton('❌ Удалить новость')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Обработчик текста кнопок
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return

    text = message.text

    if text == '➕ Добавить утреннее сообщение':
        msg = bot.reply_to(message, "Отправьте текст утреннего сообщения:")
        bot.register_next_step_handler(msg, process_morning_step)
    elif text == '➕ Добавить новость':
        msg = bot.reply_to(message, "Отправьте текст новости:")
        bot.register_next_step_handler(msg, process_news_step)
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

def process_morning_step(message):
    try:
        data = load_data()
        data['morning'].append({
            'text': message.text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data(data)
        bot.reply_to(message, "✅ Утреннее сообщение добавлено")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

def process_news_step(message):
    try:
        data = load_data()
        data['news'].append({
            'text': message.text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data(data)
        bot.reply_to(message, "✅ Новость добавлена")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

def list_morning(message):
    data = load_data()
    if not data['morning']:
        bot.reply_to(message, "Нет сохраненных утренних сообщений")
        return

    msg = "Список утренних сообщений:\n"
    for idx, item in enumerate(data['morning'], 1):
        msg += f"{idx}. {item['text']} (Добавлено: {item['timestamp']})\n"
    bot.reply_to(message, msg)

def list_news(message):
    data = load_data()
    if not data['news']:
        bot.reply_to(message, "Нет сохраненных новостей")
        return

    msg = "Список новостей:\n"
    for idx, item in enumerate(data['news'], 1):
        msg += f"{idx}. {item['text']} (Добавлено: {item['timestamp']})\n"
    bot.reply_to(message, msg)

# Удаление утреннего сообщения
@bot.message_handler(commands=['delete_morning'])
def delete_morning(message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Используйте: /delete_morning <номер>")
        return

    try:
        idx = int(args[1]) - 1
        data = load_data()
        if 0 <= idx < len(data['morning']):
            removed = data['morning'].pop(idx)
            save_data(data)
            bot.reply_to(message, f"✅ Удалено: {removed['text']}")
        else:
            bot.reply_to(message, "❌ Неверный номер")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# Удаление новости
@bot.message_handler(commands=['delete_news'])
def delete_news(message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Используйте: /delete_news <номер>")
        return

    try:
        idx = int(args[1]) - 1
        data = load_data()
        if 0 <= idx < len(data['news']):
            removed = data['news'].pop(idx)
            save_data(data)
            bot.reply_to(message, f"✅ Удалено: {removed['text']}")
        else:
            bot.reply_to(message, "❌ Неверный номер")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

if __name__ == '__main__':
    print("Бот-менеджер запущен")
    bot.polling(none_stop=True)
