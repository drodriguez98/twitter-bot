import tweepy
import schedule
import time
import os
import json
import logging
import threading
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

# Configuration Constants
LOGS_DIR = "logs"
LOG_FILE = "bot.log"
JSON_FILE = "published_news.json"
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
COUNTRY = "us"  # Specify the country for news (e.g., 'us', 'gb', 'es')
TWEET_INTERVAL = 60  # Interval between tweets in seconds

# Ensure directories exist
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_directory(LOGS_DIR)

# Logging setup
logging.basicConfig(
    filename=os.path.join(LOGS_DIR, LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Load published news URLs from JSON file
def load_published_news():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            return set(json.load(f))
    return set()

published_news = load_published_news()

# Save published news URLs to JSON file
def save_published_news():
    with open(JSON_FILE, 'w') as f:
        json.dump(list(published_news), f)

# Initialize Twitter API client
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# Fetch news from NewsAPI
def fetch_news():
    try:
        params = {
            'apiKey': NEWS_API_KEY,
            'country': COUNTRY,
            'pageSize': 10  # Number of articles to fetch per request
        }
        response = requests.get(NEWS_API_URL, params=params)
        if response.status_code == 200:
            news_data = response.json()
            return news_data.get('articles', [])
        else:
            logging.error(f"Error fetching news: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        logging.error(f"Exception occurred while fetching news: {e}")
        return []

# Post a tweet with news headline and URL
def publish_tweet(headline, url):
    try:
        tweet_text = f"{headline} \nRead more: {url}"
        response = client.create_tweet(text=tweet_text)
        logging.info(f"Tweet published: {response.data}")
        return True
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")
        return False

# Main bot operation to fetch and tweet news
def bot_operations():
    while True:
        articles = fetch_news()
        for article in articles:
            url = article.get('url')
            headline = article.get('title')
            if url and headline and url not in published_news:
                if publish_tweet(headline, url):
                    published_news.add(url)
                    save_published_news()
                    time.sleep(TWEET_INTERVAL)
        time.sleep(45)  # Wait before fetching news again

# Run the bot
if __name__ == "__main__":
    logging.info("News Tweet Bot started.")

    # Start the bot operations in a separate thread
    threading.Thread(target=bot_operations, daemon=True).start()

    while True:
        schedule.run_pending()
        time.sleep(1)
