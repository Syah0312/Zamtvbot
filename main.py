import os
import asyncio
import threading
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "supersecret")
BASE_URL = os.environ.get("BASE_URL")

if not TOKEN:
    raise RuntimeError("Set environment variable BOT_TOKEN terlebih dahulu.")

application = Application.builder().token(TOKEN).build()

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Hantar video atau file video, saya akan bagi stream link 📽️➡️🔗"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    file_id = None
    if msg.video:
        file_id = msg.video.file_id
    elif msg.document and (msg.document.mime_type or "").startswith("video/"):
        file_id = msg.document.file_id
    if not file_id:
        return
    file = await context.bot.get_file(file_id)
    stream_link = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
    caption = (
        "✅ Siap! Ini stream link anda:\n"
        f"{stream_link}\n\n"
        "Nota: Link mungkin tidak kekal selama-lamanya. Jika tamat/invalid, "
        "hantar fail semula untuk dapat link baharu."
    )
    await msg.reply_text(caption)

application.add_handler(CommandHandler("start", start_cmd))
application.add_handler(MessageHandler((filters.VIDEO | filters.Document.VIDEO), handle_video))

app = Flask(__name__)

@app.get("/")
def health():
    return jsonify(ok=True, service="telegram-streamlink-bot")

@app.post(f"/webhook/{WEBHOOK_SECRET}")
def telegram_webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return "Bad Request", 400
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

@app.get("/setwebhook")
def set_webhook():
    if not BASE_URL:
        return "Sila set BASE_URL env var kepada URL Render anda", 400
    url = f"{BASE_URL}/webhook/{WEBHOOK_SECRET}"
    loop = asyncio.get_event_loop()
    fut = asyncio.run_coroutine_threadsafe(
        application.bot.set_webhook(url=url, secret_token=WEBHOOK_SECRET, max_connections=40),
        loop
    )
    try:
        result = fut.result(timeout=10)
        return {"set_webhook": result, "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}, 500

def _start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def runner():
        await application.initialize()
        await application.start()
        await application.wait_until_closed()
    loop.create_task(runner())
    loop.run_forever()

bot_thread = threading.Thread(target=_start_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
