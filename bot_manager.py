import telebot
import json
from telebot import types

TOKEN = '7784249517:AAGdOGzTyeXHXZj9sE9nuKAzUdCx8u8HPHw'
bot = telebot.TeleBot(TOKEN)

FILE = 'messages.json'

def load_messages():
    try:
        with open(FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('morning', []), data.get('news', [])
    except FileNotFoundError:
        return [], []

def save_messages(morning, news):
    with open(FILE, 'w', encoding='utf-8') as f:
        json.dump({'morning': morning, 'news': news}, f, ensure_ascii=False, indent=2)

morning_messages, news_messages = load_messages()
user_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Добавить утреннее сообщение', 'Добавить новость')
    markup.row('Показать утренние сообщения', 'Показать новости')
    markup.row('Удалить новость', 'Удалить утреннее сообщение')
    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video'])
def handle_message(message):
    user_id = message.from_user.id

    if user_id in user_states:
        state = user_states[user_id]

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            caption = message.caption if message.caption else ''
            item = {'type': 'photo', 'file_id': file_id, 'caption': caption}
        elif message.content_type == 'video':
            file_id = message.video.file_id
            caption = message.caption if message.caption else ''
            item = {'type': 'video', 'file_id': file_id, 'caption': caption}
        elif message.content_type == 'text':
            item = {'type': 'text', 'content': message.text}
        else:
            bot.send_message(message.chat.id, "Этот тип сообщения не поддерживается.")
            return

        if state == 'adding_morning':
            morning_messages.append(item)
            save_messages(morning_messages, news_messages)
            bot.send_message(message.chat.id, "Утреннее сообщение добавлено.")
        elif state == 'adding_news':
            news_messages.append(item)
            save_messages(morning_messages, news_messages)
            bot.send_message(message.chat.id, "Новость добавлена.")

        user_states.pop(user_id)
        return

    if message.content_type == 'text':
        text = message.text.strip()
        if text == 'Добавить утреннее сообщение':
            user_states[user_id] = 'adding_morning'
            bot.send_message(message.chat.id, "Отправьте утреннее сообщение: текст или фото/видео с описанием.")
        elif text == 'Добавить новость':
            user_states[user_id] = 'adding_news'
            bot.send_message(message.chat.id, "Отправьте новость: текст или фото/видео с описанием.")
        elif text == 'Показать утренние сообщения':
            if morning_messages:
                msgs = []
                for i, item in enumerate(morning_messages, 1):
                    if isinstance(item, dict):
                        if item['type'] == 'text':
                            msgs.append(f"{i}. {item['content']}")
                        else:
                            cap = item.get('caption', '')
                            msgs.append(f"{i}. [{item['type']}] {cap}")
                    else:
                        msgs.append(f"{i}. {item}")
                bot.send_message(message.chat.id, "Утренние сообщения:\n" + "\n".join(msgs))
            else:
                bot.send_message(message.chat.id, "Утренних сообщений пока нет.")
        elif text == 'Показать новости':
            if news_messages:
                msgs = []
                for i, item in enumerate(news_messages, 1):
                    if isinstance(item, dict):
                        if item['type'] == 'text':
                            msgs.append(f"{i}. {item['content']}")
                        else:
                            cap = item.get('caption', '')
                            msgs.append(f"{i}. [{item['type']}] {cap}")
                    else:
                        msgs.append(f"{i}. {item}")
                bot.send_message(message.chat.id, "Новости:\n" + "\n".join(msgs))
            else:
                bot.send_message(message.chat.id, "Новостей пока нет.")
        elif text == 'Удалить новость':
            if not news_messages:
                bot.send_message(message.chat.id, "Новостей нет для удаления.")
                return

            markup = types.InlineKeyboardMarkup()
            for i, item in enumerate(news_messages):
                btn_text = f"Удалить новость #{i+1}"
                markup.add(types.InlineKeyboardButton(text=btn_text, callback_data=f"delnews_{i}"))

            bot.send_message(message.chat.id, "Выберите новость для удаления:", reply_markup=markup)
        elif text == 'Удалить утреннее сообщение':
            if not morning_messages:
                bot.send_message(message.chat.id, "Утренних сообщений нет для удаления.")
                return

            markup = types.InlineKeyboardMarkup()
            for i, item in enumerate(morning_messages):
                btn_text = f"Удалить утреннее сообщение #{i+1}"
                markup.add(types.InlineKeyboardButton(text=btn_text, callback_data=f"delmorning_{i}"))

            bot.send_message(message.chat.id, "Выберите утреннее сообщение для удаления:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки для выбора действия.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delnews_'))
def callback_delete_news(call):
    index = int(call.data.split('_')[1])
    if 0 <= index < len(news_messages):
        news_messages.pop(index)
        save_messages(morning_messages, news_messages)
        bot.answer_callback_query(call.id, "Новость удалена.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"Новость #{index+1} удалена.")
    else:
        bot.answer_callback_query(call.id, "Ошибка: новость не найдена.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delmorning_'))
def callback_delete_morning(call):
    index = int(call.data.split('_')[1])
    if 0 <= index < len(morning_messages):
        morning_messages.pop(index)
        save_messages(morning_messages, news_messages)
        bot.answer_callback_query(call.id, "Утреннее сообщение удалено.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"Утреннее сообщение #{index+1} удалено.")
    else:
        bot.answer_callback_query(call.id, "Ошибка: сообщение не найдено.")

if __name__ == '__main__':
    print("Бот-менеджер запущен")
    bot.infinity_polling()