import os
from flask import Flask, request
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "dummy_token")
BASE_URL = os.getenv("BASE_URL", "")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if BOT_TOKEN == "dummy_token":
        return "BOT_TOKEN not set", 400
    update = request.get_json()
    chat_id = update.get("message", {}).get("chat", {}).get("id")
    text = update.get("message", {}).get("text")
    if chat_id and text:
        send_message(chat_id, f"Echo: {text}")
    return "ok"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
