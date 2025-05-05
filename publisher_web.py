import os
from flask import Flask, jsonify
import telebot
import json

app = Flask(__name__)

TOKEN = '7784249517:AAGdOGzTyeXHXZj9sE9nuKAzUdCx8u8HPHw'
CHANNEL = '@ondreeff'

STATE_FILE = 'publish_state.json'
FILE = 'messages.json'

bot = telebot.TeleBot(TOKEN)

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'last_morning': 0, 'last_news': 0}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

@app.route('/publish_morning')
def publish_morning():
    try:
        with open(FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            morning = data.get('morning', [])
            state = load_state()

            if len(morning) > state['last_morning']:
                item = morning[state['last_morning']]
                if item['type'] == 'text':
                    bot.send_message(CHANNEL, item['content'])
                elif item['type'] == 'photo':
                    bot.send_photo(CHANNEL, item['file_id'], caption=item.get('caption', ''))
                elif item['type'] == 'video':
                    bot.send_video(CHANNEL, item['file_id'], caption=item.get('caption', ''))

                state['last_morning'] += 1
                save_state(state)
                return jsonify({'status': 'success', 'message': 'Утреннее сообщение опубликовано'})
            else:
                return jsonify({'status': 'empty', 'message': 'Нет новых утренних сообщений'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/publish_news')
def publish_news():
    try:
        with open(FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            news = data.get('news', [])
            state = load_state()

            if len(news) > state['last_news']:
                item = news[state['last_news']]
                if item['type'] == 'text':
                    bot.send_message(CHANNEL, item['content'])
                elif item['type'] == 'photo':
                    bot.send_photo(CHANNEL, item['file_id'], caption=item.get('caption', ''))
                elif item['type'] == 'video':
                    bot.send_video(CHANNEL, item['file_id'], caption=item.get('caption', ''))

                state['last_news'] += 1
                save_state(state)
                return jsonify({'status': 'success', 'message': 'Новость опубликована'})
            else:
                return jsonify({'status': 'empty', 'message': 'Нет новых новостей'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)