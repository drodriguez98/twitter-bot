import tweepy
import schedule
import time
import os
import requests
import praw
import json
import logging
import threading
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from moviepy.video.io.VideoFileClip import VideoFileClip
import shutil

# Configuration Constants
DOWNLOADS_DIR = "downloads"
UPLOADS_DIR = "uploads"
LOGS_DIR = "logs"
LOG_FILE = "bot.log"
JSON_FILE = "downloaded_urls.json"
MIN_FILES_FOR_TWEET = 5
REDDIT_INTERVAL = 45  # in seconds
TWEET_INTERVAL = 15  # in seconds
MAX_FILES_PER_REDDIT_REQUEST = 7

# Ensure directories exist
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_directory(DOWNLOADS_DIR)
ensure_directory(UPLOADS_DIR)
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

# Initialize the set of already downloaded URLs from the JSON file
def load_downloaded_urls():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            return set(json.load(f))
    return set()

downloaded_urls = load_downloaded_urls()

# Save downloaded URLs to the JSON file
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

# Downloading and handling media
def download_image(url, save_path):
    if url not in downloaded_urls:
        logging.info(f"Downloading image: {url}")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            downloaded_urls.add(url)
            save_downloaded_urls()
        else:
            logging.error(f"Error downloading image from {url}")
    else:
        logging.info(f"Image from {url} already downloaded.")

def download_video(url, save_path):
    if url not in downloaded_urls:
        logging.info(f"Downloading video: {url}")
        response = requests.get(url, stream=True)
        temp_path = save_path.replace(".mp4", ".tmp")
        if response.status_code == 200:
            with open(temp_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            convert_to_mp4(temp_path, save_path)
            os.remove(temp_path)
            downloaded_urls.add(url)
            save_downloaded_urls()
        else:
            logging.error(f"Error downloading video from {url}")
    else:
        logging.info(f"Video from {url} already downloaded.")

def convert_to_mp4(input_path, output_path):
    try:
        clip = VideoFileClip(input_path)
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close()
    except Exception as e:
        logging.error(f"Error converting {input_path} to MP4: {e}")

# Fetch memes from Reddit
def fetch_memes_from_reddit():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit("memes")
    time_limit = datetime.now(timezone.utc) - timedelta(hours=24)

    for post in subreddit.new(limit=MAX_FILES_PER_REDDIT_REQUEST):
        post_time = datetime.fromtimestamp(post.created_utc, timezone.utc)
        if post_time < time_limit:
            continue

        if post.url.endswith(('.jpg', '.png', '.jpeg')):
            save_path = os.path.join(DOWNLOADS_DIR, f"{post.id}.jpg")
            download_image(post.url, save_path)
        elif post.url.endswith(('.gif', '.mp4')):
            save_path = os.path.join(DOWNLOADS_DIR, f"{post.id}.mp4")
            download_video(post.url, save_path)

# Function to post tweet with media
def publish_tweet(texto):
    try:
        response = client.create_tweet(text=texto)
        logging.info(f"Tweet published: {response.data}")
        return True
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")
        return False

# Function to move files to uploads folder
def move_to_uploads(files):
    for file in files:
        origin_path = os.path.join(DOWNLOADS_DIR, file)
        destination_path = os.path.join(UPLOADS_DIR, file)
        shutil.move(origin_path, destination_path)
        logging.info(f"File moved to uploads: {file}")

# Function to handle the bot's operations in separate threads
def bot_operations():
    while True:
        # Check files in the downloads folder
        files = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith(('jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov'))]
        
        # Publish only if there are enough files
        if len(files) >= MIN_FILES_FOR_TWEET:
            for file in files[:MIN_FILES_FOR_TWEET]:
                texto = f"Ruta del file: {os.path.join(DOWNLOADS_DIR, file)}"
                if publish_tweet(texto):
                    move_to_uploads([file])
                    time.sleep(TWEET_INTERVAL)

        time.sleep(10)

# Main function to execute all tasks concurrently
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