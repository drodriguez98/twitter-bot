# Bot to download 15 Reddit memes daily and post them on Twitter automatically with Free plan

## 1- Download 15 Reddit memes daily at a set time.

## 2- When there are at least 15 memes in the downloads folder, publish a tweet with each of them every 30 seconds. If there are more than 15 memes in the folder, it will publish the first 15 it finds.

## 3- Move the published memes to the uploads folder.

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
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

def download_video(url, save_path):
    response = requests.get(url, stream=True)
    temp_path = save_path.replace(".mp4", ".tmp")
    if response.status_code == 200:
        with open(temp_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        convert_to_mp4(temp_path, save_path)
        os.remove(temp_path)

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

    for post in subreddit.new(limit=15): # Download 15 new memes
        post_time = datetime.fromtimestamp(post.created_utc, timezone.utc)
        if post_time < time_limit:
            continue

        if post.url.endswith(('.jpg', '.png', '.jpeg')): # If it is image
            save_path = os.path.join(DOWNLOADS_DIR, f"{post.id}.jpg")
            print(f"Downloading image: {post.url}")
            download_image(post.url, save_path)
        elif post.url.endswith(('.gif', '.mp4')): # If it is video
            save_path = os.path.join(DOWNLOADS_DIR, f"{post.id}.mp4")
            print(f"Downloading video: {post.url}")
            download_video(post.url, save_path)

# Feature to post a tweet with the path of the downloaded file
def publicar_tweet(texto):
    try:
        response = client.create_tweet(text=texto)
        print(f"Tweet publicado: {response.data}")
        return True
    except Exception as e:
        print(f"Error al publicar el tweet: {e}")
        return False

# Function to move files to uploads folder
def mover_a_uploads(archivos):
    for archivo in archivos:
        ruta_origen = os.path.join(DOWNLOADS_DIR, archivo)
        ruta_destino = os.path.join(UPLOADS_DIR, archivo)
        shutil.move(ruta_origen, ruta_destino)
        print(f"Archivo movido a uploads: {archivo}")

# Main function to execute all tasks
def ejecutar_bot():
    print("Ejecutando bot...")

    # Download memes once a day (change the time as you prefer)
    schedule.every().day.at("18:38").do(fetch_memes_from_reddit)

    while True:
        # Run scheduled tasks
        schedule.run_pending()
        
        # Check files in the downloads folder
        archivos = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith(('jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov'))]
        
        # Publish only if there are at least 15 files
        if len(archivos) >= 15:
            for archivo in archivos[:15]: # Only the first 15 files found are published
                texto = f"Ruta del archivo: {os.path.join(DOWNLOADS_DIR, archivo)}"
                if publicar_tweet(texto):
                    mover_a_uploads([archivo]) # Move file to uploads after publishing  
                    time.sleep(30) # Wait 30 seconds between tweets

        time.sleep(5)  # Check the folder every 5 seconds

if __name__ == "__main__":
    ejecutar_bot()
