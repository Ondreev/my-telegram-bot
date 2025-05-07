import os
import telebot
import json
from flask import Flask

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'messages.json')
STATE_FILE = os.path.join(BASE_DIR, 'publish_state.json')

# Ваш токен и ID канала
TOKEN = '7784249517:AAFZdcmFknfTmAf17N2wTifmCoF54BQkeZU'  # <-- ваш токен
CHANNEL_ID = '@ondreeff'  # <-- замените на ваш канал или ID

bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'news': []}

def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'last_news_index': -1}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f)

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
    app.run(host='0.0.0.0', port=5000)
