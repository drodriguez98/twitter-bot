import tweepy
import schedule
import time
import os
import json
import logging
import threading
import requests
import random
import html
from dotenv import load_dotenv
from datetime import datetime

# Configuration Constants
LOGS_DIR = "logs"
LOG_FILE = "bot.log"
QUESTION_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"  # Example API for trivia questions
QUESTION_INTERVAL = 60  # Interval between questions in seconds

# Ensure directories exist
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

# Initialize Twitter API client
client = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# Fetch a question from an API
def fetch_question():
    try:
        response = requests.get(QUESTION_API_URL)
        if response.status_code == 200:
            question_data = response.json()
            if question_data.get("results"):
                result = question_data["results"][0]
                question_text = result["question"]
                correct_answer = result["correct_answer"]
                incorrect_answers = result["incorrect_answers"]
                options = incorrect_answers + [correct_answer]
                random.shuffle(options)
                return question_text, options
        logging.error(f"Error fetching question: No results found")
        return None, []
    except Exception as e:
        logging.error(f"Exception occurred while fetching question: {e}")
        return None, []

# Post a question with options on Twitter
def post_question_with_options(question, options):
    try:
        if question and options:
            # Convert HTML entities to proper characters
            question = html.unescape(question)
            tweet_text = f"{question}\n\n" + "\n".join([f"{i + 1}) {option}" for i, option in enumerate(options[:4])])
            response = client.create_tweet(text=tweet_text)
            logging.info(f"Question posted: {response.data}")
            return question
    except Exception as e:
        logging.error(f"Error posting question: {e}")
        return None

# Main bot operation
def bot_operations():
    while True:
        question, options = fetch_question()
        if question:
            post_question_with_options(question, options)
        time.sleep(QUESTION_INTERVAL)

# Run the bot
if __name__ == "__main__":
    logging.info("Survey Bot started.")

    # Start the bot operations in a separate thread
    threading.Thread(target=bot_operations, daemon=True).start()

    while True:
        schedule.run_pending()
        time.sleep(1)