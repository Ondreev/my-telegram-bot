import os
import telebot
import feedparser
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import random

# Получаем данные из переменных окружения
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
GROUP_ID = int(os.getenv('GROUP_ID')) if os.getenv('GROUP_ID') else None

bot = telebot.TeleBot(TOKEN)

# Мотивирующие фразы
MOTIVATIONAL_QUOTES = [
    "Утро — самое время начать свой спортивный день! 💪",
    "Сегодня — новый шанс стать лучше! Давайте тренироваться! 🏋️",
    "Здоровье — лучшая инвестиция! Держите ритм! 🌟",
    "Каждый день — шаг к вашей цели! Давайте вперед! 🚶♂️",
    "Сила воли — ваш главный тренер! Держитесь! 💪"
]

# Функции спам-контроля
def is_spam(text):
    spam_words = [
        'в личку', 'лс', 'заработок', 'подработка', 'доход', 'удаленка',
        'работа', 'работник', 'работников', 'работники', 'деньг', 'работ', 'пиши',
        'работа в интернете', 'бесплатно', 'реклама', 'ссылка', 'vk.com',
        't.me', 'дешево', 'нажми сюда', 'подпишись', 'криптовалюта',
        'биткоин', 'только сегодня', 'взлом', 'пароль', 'онлайн-казино',
        'подраб', 'работ', 'vpn', 'профил', 'личк', 'впн'
    ]
    text_lower = text.lower().replace(" ", "")
    for word in spam_words:
        if word in text_lower:
            return True
    return False

@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_spam(message):
    if message.chat.id == GROUP_ID:
        if is_spam(message.text):
            try:
                bot.delete_message(message.chat.id, message.message_id)
                print(f"Удалено спам-сообщение от {message.from_user.id}")
            except Exception as e:
                print(f"Ошибка удаления: {str(e)}")

# Проверка валидности URL
def is_valid_url(url):
    return url and (url.startswith('http://') or url.startswith('https://'))

# Получение новостей с улучшенным поиском изображений
def get_sports_fashion_news():
    feed = feedparser.parse("https://www.lofficiel.ru/rss.xml")
    articles = []
    for entry in feed.entries[:3]:
        image_url = None
        try:
            page = requests.get(entry.link, timeout=5)
            soup = BeautifulSoup(page.text, 'html.parser')
            og_image = soup.find('meta', property="og:image")
            if og_image and og_image.get('content'):
                image_url = og_image['content']
                if not image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    image_url = None
            if not image_url:
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    src = img_tag['src']
                    if src.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        image_url = src
        except Exception as e:
            print(f"Ошибка при получении изображения: {e}")
            image_url = None

        if not image_url:
            image_url = "https://via.placeholder.com/800x400?text=Sport+Fashion"

        articles.append({
            'title': entry.title,
            'description': entry.summary,
            'url': entry.link,
            'source': {'name': "L'Officiel Russia"},
            'urlToImage': image_url
        })
    print(f"Загружено новостей: {len(articles)}")
    return articles

def format_news_post(article):
    return f"<b>{article['title']}</b>\n\n" \
           f"{article['description'][:1000]}..." \
           f"\n\nИсточник: {article['source']['name']}"

def can_publish_news():
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    current_hour = now.hour
    return not (22 <= current_hour < 8)

def send_news_to_channel():
    if not can_publish_news():
        print("Ночное время, публикация запрещена")
        return

    articles = get_sports_fashion_news()
    if not articles:
        print("Новостей не найдено")
        return

    article = articles[0]
    image_url = article.get('urlToImage')

    if not is_valid_url(image_url):
        print(f"Неверный URL изображения: {image_url}. Используем заглушку.")
        image_url = "https://via.placeholder.com/800x400?text=Sport+Fashion"

    try:
        bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=image_url,
            caption=format_news_post(article),
            parse_mode='HTML'
        )
        print("Новость успешно опубликована")
    except Exception as e:
        print(f"Ошибка публикации: {e}")

# Утреннее приветствие
def morning_greeting():
    quote = random.choice(MOTIVATIONAL_QUOTES)
    bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"Доброе утро! 🌞\n\n{quote}",
        parse_mode='HTML'
    )

# Настройка расписания с учётом московского времени
scheduler = BackgroundScheduler(timezone='Europe/Moscow')
scheduler.add_job(send_news_to_channel, 'interval', hours=3)
scheduler.add_job(morning_greeting, CronTrigger(hour=8, minute=0, timezone='Europe/Moscow'))
scheduler.start()
if __name__ == '__main__':
    print("=== ЗАПУСК БОТА ===")
    morning_greeting()  # Тест утреннего сообщения
    bot.polling()
