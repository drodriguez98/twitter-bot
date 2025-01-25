# pip install praw moviepy python-dotenv

import os
import requests
import praw
from datetime import datetime, timedelta, timezone
from moviepy.video.io.VideoFileClip import VideoFileClip
from dotenv import load_dotenv

# Cargar las credenciales desde el archivo .env
load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

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
    # Configurar la instancia de Reddit con las credenciales
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit("memes")
    time_limit = datetime.now(timezone.utc) - timedelta(hours=24)

    downloads_dir = "downloads"
    ensure_directory(downloads_dir)

    for post in subreddit.new(limit=10):  # Ajusta el límite según sea necesario
        post_time = datetime.fromtimestamp(post.created_utc, timezone.utc)
        if post_time < time_limit:
            continue

        if post.url.endswith(('.jpg', '.png', '.jpeg')):
            save_path = os.path.join(downloads_dir, f"{post.id}.jpg")
            print(f"Downloading image: {post.url}")
            download_image(post.url, save_path)
        elif post.url.endswith(('.gif', '.mp4')):
            save_path = os.path.join(downloads_dir, f"{post.id}.mp4")
            print(f"Downloading video: {post.url}")
            download_video(post.url, save_path)

if __name__ == "__main__":
    fetch_memes_from_reddit()