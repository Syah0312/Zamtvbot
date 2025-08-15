import os
from flask import Flask, request
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL", "")

app = Flask(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        # Kalau mesej ada dokumen / video
        if "document" in data["message"]:
            file_id = data["message"]["document"]["file_id"]
            send_stream_link(chat_id, file_id)
        elif "video" in data["message"]:
            file_id = data["message"]["video"]["file_id"]
            send_stream_link(chat_id, file_id)
        else:
            send_message(chat_id, "Hantar dokumen atau video untuk dapatkan link stream.")

    return "ok"

def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})

def send_stream_link(chat_id, file_id):
    # Dapatkan file path dari Telegram
    file_info = requests.get(f"{TELEGRAM_API}/getFile?file_id={file_id}").json()
    file_path = file_info["result"]["file_path"]

    # Buat link stream direct
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    send_message(chat_id, f"🎬 Link Stream:\n{file_url}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
