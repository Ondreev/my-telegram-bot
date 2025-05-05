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

# Команда /start с кнопками
@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав доступа")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('/add_morning')
    btn2 = types.KeyboardButton('/add_news')
    btn3 = types.KeyboardButton('/list_morning')
    btn4 = types.KeyboardButton('/list_news')
    btn5 = types.KeyboardButton('/delete_morning')
    btn6 = types.KeyboardButton('/delete_news')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)

    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=markup)

# Добавление утреннего сообщения
@bot.message_handler(commands=['add_morning'])
def add_morning(message):
    if not is_admin(message.from_user.id):
        return

    msg = bot.reply_to(message, "Отправьте текст утреннего сообщения:")
    bot.register_next_step_handler(msg, process_morning_step)

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

# Добавление новости
@bot.message_handler(commands=['add_news'])
def add_news(message):
    if not is_admin(message.from_user.id):
        return

    msg = bot.reply_to(message, "Отправьте текст новости:")
    bot.register_next_step_handler(msg, process_news_step)

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

# Просмотр утренних сообщений
@bot.message_handler(commands=['list_morning'])
def list_morning(message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    if not data['morning']:
        bot.reply_to(message, "Нет сохраненных утренних сообщений")
        return

    msg = "Список утренних сообщений:\n"
    for idx, item in enumerate(data['morning'], 1):
        msg += f"{idx}. {item['text']} (Добавлено: {item['timestamp']})\n"
    bot.reply_to(message, msg)

# Просмотр новостей
@bot.message_handler(commands=['list_news'])
def list_news(message):
    if not is_admin(message.from_user.id):
        return

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
