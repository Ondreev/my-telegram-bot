import telebot
import json
import os

TOKEN = '7784249517:AAGdOGzTyeXHXZj9sE9nuKAzUdCx8u8HPHw'
CHANNEL = '@ondreeff'  # замените на ваш канал, если нужно

bot = telebot.TeleBot(TOKEN)

FILE = 'messages.json'
STATE_FILE = 'publish_state.json'  # для хранения индексов опубликованных сообщений

def load_messages():
    try:
        with open(FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('morning', []), data.get('news', [])
    except FileNotFoundError:
        return [], []

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {'morning_index': 0, 'news_index': 0}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def publish_message(item):
    try:
        if item['type'] == 'text':
            bot.send_message(CHANNEL, item['content'])
        elif item['type'] == 'photo':
            bot.send_photo(CHANNEL, item['file_id'], caption=item.get('caption', ''))
        elif item['type'] == 'video':
            bot.send_video(CHANNEL, item['file_id'], caption=item.get('caption', ''))
        else:
            print(f"Неизвестный тип сообщения: {item['type']}")
            return False
        return True
    except Exception as e:
        print(f"Ошибка при публикации: {e}")
        return False

def main():
    morning_messages, news_messages = load_messages()
    state = load_state()

    # Публикуем утреннее сообщение, если есть и не публиковали
    if state['morning_index'] < len(morning_messages):
        item = morning_messages[state['morning_index']]
        if publish_message(item):
            state['morning_index'] += 1
            save_state(state)
            print("Утреннее сообщение опубликовано")
            return

    # Публикуем новость, если есть и не публиковали
    if state['news_index'] < len(news_messages):
        item = news_messages[state['news_index']]
        if publish_message(item):
            state['news_index'] += 1
            save_state(state)
            print("Новость опубликована")
            return

    print("Нет новых сообщений для публикации")

if __name__ == '__main__':
    main()