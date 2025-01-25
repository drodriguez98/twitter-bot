# pip install beautifulsoup4 requests tweepy schedule python-dotenv

import tweepy
import schedule
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Claves de autenticación (configura estas en un archivo .env)
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # Necesario para API v2

# Autenticación en Twitter usando API v2
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Función para publicar un tweet
def publicar_tweet(texto):
    try:
        response = client.create_tweet(text=texto)
        print(f"Tweet publicado: {response.data}")
    except Exception as e:
        print(f"Error al publicar el tweet: {e}")

# Función principal para ejecutar todas las tareas
def ejecutar_bot():

    print("Ejecutando bot...")
    publicar_tweet("¡Buenos díassds! 🌅")

    # Configuración de tareas programadas
    schedule.every().day.at("01:27").do(lambda: publicar_tweet("¡Buenos díasss! 🌅")) # Tweet diario a las 9 AM

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    ejecutar_bot()