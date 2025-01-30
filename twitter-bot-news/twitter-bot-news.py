import tweepy
import schedule
import time
import os
import json
import logging
import threading
import requests
import yaml
from dotenv import load_dotenv
from queue import Queue

# Load environment variables
load_dotenv()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Load configuration from YAML file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

FETCH_NEWS_INTERVAL = config.get("fetch_news_interval", 3000)
TWEET_INTERVAL = config.get("tweet_interval", 60)
COUNTRY = config.get("country", "us")
PAGE_SIZE = config.get("page_size", 10)
BLACKLISTED_KEYWORDS = config.get("blacklisted_keywords", [])
LOGS_DIR = config.get("logs_dir", "logs")
LOG_FILE = config.get("log_file", "bot.log")
JSON_FILE = config.get("json_file", "published_news.json")
NEWS_API_URL = config.get("news_api_url", "https://newsapi.org/v2/top-headlines")

# Create a directory if it doesn't exist
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
            'pageSize': PAGE_SIZE
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

# Check if a news headline is valid
def is_valid_news(headline):
    return not any(keyword.lower() in headline.lower() for keyword in BLACKLISTED_KEYWORDS)

# Post a tweet with news headline and URL
def publish_tweet(headline, url):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            tweet_text = f"{headline} \nRead more: {url}"
            response = client.create_tweet(text=tweet_text)
            logging.info(f"Tweet published: {response.data}")
            return True
        except Exception as e:
            logging.error(f"Error posting tweet (attempt {attempt + 1}): {e}")
            time.sleep(5)  # Wait before retrying
    logging.error(f"Failed to publish tweet after {max_retries} attempts: {headline}")
    return False

# Queue for news articles to be tweeted
news_queue = Queue()

# Main bot operation to fetch and tweet news
def bot_operations():
    while True:
        articles = fetch_news()
        for article in articles:
            url = article.get('url')
            headline = article.get('title')
            if url and headline and url not in published_news and is_valid_news(headline):
                news_queue.put((headline, url))
        time.sleep(FETCH_NEWS_INTERVAL)

# Worker function to process news from the queue and tweet them
def tweet_worker():
    while True:
        headline, url = news_queue.get()
        if publish_tweet(headline, url):
            published_news.add(url)
            save_published_news()
        news_queue.task_done()

# Run the bot
if __name__ == "__main__":
    logging.info("News Tweet Bot started.")

    # Start multiple workers for tweeting
    for _ in range(3):  # Number of workers
        threading.Thread(target=tweet_worker, daemon=True).start()

    # Start the bot operations in a separate thread
    threading.Thread(target=bot_operations, daemon=True).start()

    while True:
        schedule.run_pending()
        time.sleep(1)