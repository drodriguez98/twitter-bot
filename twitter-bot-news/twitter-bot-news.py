import tweepy
import time
import os
import json
import logging
import requests
import yaml
from dotenv import load_dotenv

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

FETCH_NEWS_INTERVAL = config.get("fetch_news_interval", 300)
TWEET_INTERVAL = config.get("tweet_interval", 60)
COUNTRY = config.get("country", "us")
PAGE_SIZE = config.get("page_size", 10)
BLACKLISTED_KEYWORDS = config.get("blacklisted_keywords", [])
LOGS_DIR = config.get("logs_dir", "logs")
LOG_FILE = config.get("log_file", "bot.log")
JSON_FILE = config.get("json_file", "published_news.json")
NEWS_API_URL = config.get("news_api_url", "https://newsapi.org/v2/top-headlines")

# Ensure log directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

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
            return response.json().get('articles', [])
        else:
            logging.error(f"Error fetching news: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Exception while fetching news: {e}")
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

# Main bot operation
def run_bot():
    logging.info("News Tweet Bot started.")
    while True:
        articles = fetch_news()
        for article in articles:
            url = article.get('url')
            headline = article.get('title')
            if url and headline and url not in published_news and not any(keyword.lower() in headline.lower() for keyword in BLACKLISTED_KEYWORDS):
                if publish_tweet(headline, url):
                    published_news.add(url)
                    save_published_news()
                    time.sleep(TWEET_INTERVAL)
        time.sleep(FETCH_NEWS_INTERVAL)

if __name__ == "__main__":
    run_bot()
