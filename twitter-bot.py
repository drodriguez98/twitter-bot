# Bot to download Reddit memes and post them on Twitter automatically (limited to free plan)

# Required Libraries
import tweepy
import schedule
import time
import os
import requests
import praw
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from moviepy.video.io.VideoFileClip import VideoFileClip
import shutil

# File directories
DOWNLOADS_DIR = "downloads"
UPLOADS_DIR = "uploads"

# List of url images already downloaded
downloaded_urls = set()

# Load environment variables (configure these in a .env file)
load_dotenv()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # Required for API v2
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Authentication on Twitter using API v2
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# Download files from Reddit
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_image(url, save_path):
    if url not in downloaded_urls: # Check if the URL has already been downloaded
        print(f"Downloading image: {url}") # Make sure to use 'url'
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            downloaded_urls.add(url) # Add the URL to the set after downloading
        else:
            print(f"Error downloading image from {url}")
    else:
        print(f"Image from {url} already downloaded.")

def download_video(url, save_path):
    if url not in downloaded_urls: # Check if the URL has already been downloaded
        print(f"Downloading video: {url}") # Make sure to use 'url'
        response = requests.get(url, stream=True)
        temp_path = save_path.replace(".mp4", ".tmp")
        if response.status_code == 200:
            with open(temp_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            convert_to_mp4(temp_path, save_path)
            os.remove(temp_path)
            downloaded_urls.add(url) # Add the URL to the set after downloading
        else:
            print(f"Error downloading video from {url}")
    else:
        print(f"Video from {url} already downloaded.")

def convert_to_mp4(input_path, output_path):
    try:
        clip = VideoFileClip(input_path)
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close()
    except Exception as e:
        print(f"Error converting {input_path} to MP4: {e}")

def fetch_memes_from_reddit():
    # Configure the Reddit instance with the credentials
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit("memes")
    time_limit = datetime.now(timezone.utc) - timedelta(hours=24)

    ensure_directory(DOWNLOADS_DIR)

    for post in subreddit.new(limit=7):  # Download 6 memes
        post_time = datetime.fromtimestamp(post.created_utc, timezone.utc)
        if post_time < time_limit:
            continue

        if post.url.endswith(('.jpg', '.png', '.jpeg')): # If it is image
            save_path = os.path.join(DOWNLOADS_DIR, f"{post.id}.jpg")
            download_image(post.url, save_path)
        elif post.url.endswith(('.gif', '.mp4')): # If it is video
            save_path = os.path.join(DOWNLOADS_DIR, f"{post.id}.mp4")
            download_video(post.url, save_path)

# Feature to post a tweet with the path of the downloaded file
def publish_tweet(texto):
    try:
        response = client.create_tweet(text=texto)
        print(f"Tweet published: {response.data}")
        return True
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return False

# Function to move files to uploads folder
def move_to_uploads(files):
    for file in files:
        origin_path = os.path.join(DOWNLOADS_DIR, file)
        destination_path = os.path.join(UPLOADS_DIR, file)
        shutil.move(origin_path, destination_path)
        print(f"File moved to uploads: {file}")

# Main function to execute all tasks
def run_bot():
    print("Running bot...")

    # Download memes every 15 seconds
    schedule.every(15).seconds.do(fetch_memes_from_reddit)

    while True:
        # Run scheduled tasks
        schedule.run_pending()
        
        # Check files in the downloads folder
        files = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith(('jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov'))]
        
        # Publish only if there are at least 5 files
        if len(files) >= 5:
            for file in files[:5]: # Only the first 5 files found are published
                texto = f"Ruta del file: {os.path.join(DOWNLOADS_DIR, file)}"
                if publish_tweet(texto):
                    move_to_uploads([file]) # Move file to uploads after publishing  
                    time.sleep(15) # Wait 15 seconds between tweets

        time.sleep(10)  # Check the folder every 10 seconds

if __name__ == "__main__":
    run_bot()