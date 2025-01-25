import tweepy
import schedule
import time
import os
from dotenv import load_dotenv
import shutil

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Claves de autenticación (configura estas en un archivo .env)
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # Necesario para API v2

# Directorios de archivos
DOWNLOADS_DIR = "downloads"
UPLOADS_DIR = "uploads"

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
        return True
    except Exception as e:
        print(f"Error al publicar el tweet: {e}")
        return False

# Función para mover archivos a la carpeta uploads
def mover_a_uploads(archivos):
    for archivo in archivos:
        ruta_origen = os.path.join(DOWNLOADS_DIR, archivo)
        ruta_destino = os.path.join(UPLOADS_DIR, archivo)
        shutil.move(ruta_origen, ruta_destino)
        print(f"Archivo movido a uploads: {archivo}")

# Función principal para ejecutar todas las tareas
def ejecutar_bot():
    print("Ejecutando bot...")

    while True:
        # Verificar archivos en la carpeta de descargas
        archivos = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith(('jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov'))]
        
        # Si hay al menos 17 archivos, publicar tweet
        if len(archivos) >= 2:
            for archivo in archivos[:2]:  # Solo se publican los dos primeros archivos encontrados
                texto = f"Ruta del archivo: {os.path.join(DOWNLOADS_DIR, archivo)}"
                if publicar_tweet(texto):
                    mover_a_uploads([archivo])
                    time.sleep(30)  # Esperar 30 segundos entre tweets
        time.sleep(5)  # Revisar la carpeta cada 5 segundos

if __name__ == "__main__":
    ejecutar_bot()
