import os
import telebot

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "Привет! Я бот.")

# Здесь добавьте остальные обработчики команд и функций бота по вашему коду

if __name__ == '__main__':
    print("Бот-менеджер запущен")
    bot.polling(none_stop=True)
