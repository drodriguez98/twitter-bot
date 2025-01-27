import tweepy
import schedule
import time
import os
import json
import logging
import threading
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import praw

# Configuration Constants
LOGS_DIR = "logs"
LOG_FILE = "bot.log"
JSON_FILE = "downloaded_urls.json"
REDDIT_INTERVAL = 45  # in seconds
TWEET_INTERVAL = 15  # in seconds
MAX_POSTS_PER_REDDIT_REQUEST = 7

# Create the necessary folders if they do not exist.
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
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Load the URLs of already tweeted memes from the JSON file to avoid duplicates.
def load_downloaded_urls():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            return set(json.load(f))
    return set()

downloaded_urls = load_downloaded_urls()

# Save downloaded meme URLs in JSON file for persistence.
def save_downloaded_urls():
    with open(JSON_FILE, 'w') as f:
        json.dump(list(downloaded_urls), f)

# Initialize Twitter API client
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# Fetch memes from Reddit's 'memes' subreddit
# It retrieves recent post URLs and skips already tweeted ones.
def fetch_memes_from_reddit():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit("memes")
    time_limit = datetime.now(timezone.utc) - timedelta(hours=24)

    new_urls = []
    for post in subreddit.new(limit=MAX_POSTS_PER_REDDIT_REQUEST):
        post_time = datetime.fromtimestamp(post.created_utc, timezone.utc)
        if post_time < time_limit:
            continue

        if post.shortlink not in downloaded_urls:
            logging.info(f"New meme found: {post.shortlink}")
            new_urls.append(post.shortlink)
            downloaded_urls.add(post.shortlink)

    save_downloaded_urls()
    return new_urls

# Post a tweet with the URL of a meme and handle potential errors in the process.
def publish_tweet(texto):
    try:
        response = client.create_tweet(text=texto)
        logging.info(f"Tweet published: {response.data}")
        return True
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")
        return False

# Control the main flow of the bot: fetch memes and tweet them at regular intervals.
def bot_operations():
    while True:
        # Fetch new meme URLs from Reddit
        new_urls = fetch_memes_from_reddit()

        # Publish tweets for the new URLs
        for url in new_urls:
            texto = f"Meme del día: {url}"
            if publish_tweet(texto):
                time.sleep(TWEET_INTERVAL)

        time.sleep(10)

# Start the bot, configure scheduled tasks, and run the main bot process in the background.
def run_bot():
    logging.info("Bot started.")

    # Schedule meme fetching at regular intervals
    schedule.every(REDDIT_INTERVAL).seconds.do(fetch_memes_from_reddit)

    # Start the bot operations in a separate thread
    threading.Thread(target=bot_operations, daemon=True).start()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
