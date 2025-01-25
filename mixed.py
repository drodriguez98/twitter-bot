import os
import requests
import praw
import tweepy
import time
from datetime import datetime, timedelta, timezone
from moviepy.video.io.VideoFileClip import VideoFileClip
from shutil import move
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Claves de autenticación de Reddit
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Claves de autenticación de Twitter
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Autenticación en Twitter usando API v1.1
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

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
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit("memes")
    time_limit = datetime.now(timezone.utc) - timedelta(hours=24)

    downloads_dir = "downloads"
    ensure_directory(downloads_dir)

    # Descargar hasta 10 memes
    downloaded_count = 0
    for post in subreddit.new(limit=100):  # Ajusta el límite según sea necesario
        if downloaded_count >= 10:
            break
        
        post_time = datetime.fromtimestamp(post.created_utc, timezone.utc)
        if post_time < time_limit:
            continue

        if post.url.endswith(('.jpg', '.png', '.jpeg')):
            save_path = os.path.join(downloads_dir, f"{post.id}.jpg")
            download_image(post.url, save_path)
            downloaded_count += 1
        elif post.url.endswith(('.gif', '.mp4')):
            save_path = os.path.join(downloads_dir, f"{post.id}.mp4")
            download_video(post.url, save_path)
            downloaded_count += 1

    return downloads_dir

def publicar_tweet_with_media(media_path):
    try:
        # Publica la imagen o video directamente en Twitter sin usar media_upload
        if media_path.endswith(('jpg', 'png', 'jpeg')):
            # Si es una imagen
            api.update_status_with_media(status="Meme del día", filename=media_path)
        elif media_path.endswith(('mp4', 'gif')):
            # Si es un video o gif
            api.update_status_with_media(status="Meme del día", filename=media_path)
        
        print(f"Tweet publicado: {media_path}")
        
        # Mover el archivo a la carpeta uploads después de la publicación
        move(media_path, f"uploads/{os.path.basename(media_path)}")
    except Exception as e:
        print(f"Error al publicar el tweet: {e}")

def ejecutar_bot():
    downloads_dir = "downloads"
    ensure_directory(downloads_dir)

    print("Ejecutando bot...")

    while True:
        # Descargar memes de Reddit cada 15 minutos
        fetch_memes_from_reddit()

        # Publicar memes en Twitter
        files = os.listdir(downloads_dir)
        if files:
            for file in files:
                file_path = os.path.join(downloads_dir, file)
                if file.endswith(('jpg', 'png', 'mp4', 'gif')):
                    publicar_tweet_with_media(file_path)

        time.sleep(900)  # Espera 15 minutos antes de descargar y publicar más memes

if __name__ == "__main__":
    ejecutar_bot()
