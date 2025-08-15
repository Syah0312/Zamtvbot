import os
import threading
from flask import Flask, send_from_directory
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("8379080026:AAGsyJMsKa7iUzO7m1kZasyTt6ULzQ1LQi8")
BASE_URL = os.getenv("https://zamtvbot.onrender.com")
app = Flask(zamtvbot)

@app.route('/')
def home():
    return "✅ Bot Telegram + Web Server Jalan!"

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory('files', filename)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hantar fail sebagai dokumen, saya akan bagi link stream.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    os.makedirs("files", exist_ok=True)
    save_path = os.path.join("files", doc.file_name)
    await file.download_to_drive(save_path)
    link = BASE_URL.rstrip("/") + "/files/" + doc.file_name
    await update.message.reply_text(f"✅ Link Stream:\n{link}")

def run_bot():
    app_bot = ApplicationBuilder().token(8379080026:AAGsyJMsKa7iUzO7m1kZasyTt6ULzQ1LQi8).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app_bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
