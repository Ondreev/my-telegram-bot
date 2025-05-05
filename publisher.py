import os
import telebot
import json

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')  # ID или @username канала/чата

bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'messages.json'
STATE_FILE = 'publish_state.json'  # для хранения индекса последней опубликованной новости

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'morning': [], 'news': []}

def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'last_news_index': -1}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f)

def publish_next_news():
    data = load_data()
    state = load_state()
    news_list = data.get('news', [])
    if not news_list:
        print("Нет новостей для публикации")
        return

    next_index = (state['last_news_index'] + 1) % len(news_list)
    news = news_list[next_index]

    try:
        bot.send_message(CHANNEL_ID, news['text'])
        print(f"Опубликована новость #{next_index + 1}")
        state['last_news_index'] = next_index
        save_state(state)
    except Exception as e:
        print(f"Ошибка при публикации: {e}")

if __name__ == '__main__':
    publish_next_news()
