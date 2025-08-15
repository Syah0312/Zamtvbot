import os
import asyncio
import threading
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ===== Config =====
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "supersecret")
BASE_URL = os.environ.get("BASE_URL", "")
RUN_MODE = os.environ.get("RUN_MODE", "local")  # 'local' atau 'render'

if not TOKEN:
    raise RuntimeError("Set environment variable BOT_TOKEN terlebih dahulu.")

# ===== PTB Application =====
application = Application.builder().token(TOKEN).build()

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Hantar video atau fail video, saya akan beri link stream 📽️➡️🔗"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    file_id = None
    if msg and msg.video:
        file_id = msg.video.file_id
    elif msg and msg.document and (msg.document.mime_type or '').startswith('video/'):
        file_id = msg.document.file_id

    if not file_id:
        return

    # Dapatkan file_path daripada Telegram & bina stream link
    file = await context.bot.get_file(file_id)
    stream_link = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"

    await msg.reply_text(
        f"✅ Siap! Ini stream link anda:\n{stream_link}\n\n"
        "Nota: Link mungkin tidak kekal selama-lamanya. Jika tamat, hantar fail semula untuk dapat link baru."
    )

application.add_handler(CommandHandler("start", start_cmd))
application.add_handler(MessageHandler((filters.VIDEO | filters.Document.VIDEO), handle_video))

# ===== Flask App (untuk Render) =====
app = Flask(__name__)

@app.get('/')
def home():
    return jsonify(ok=True, service='telegram-streamlink-bot')

@app.post(f'/webhook/{WEBHOOK_SECRET}')
def telegram_webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return 'Bad Request', 400
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return 'OK', 200

@app.get('/setwebhook')
def set_webhook():
    if not BASE_URL:
        return 'Sila set BASE_URL env var kepada URL Render anda', 400
    url = f"{BASE_URL}/webhook/{WEBHOOK_SECRET}"
    loop = asyncio.get_event_loop()
    fut = asyncio.run_coroutine_threadsafe(
        application.bot.set_webhook(url=url, secret_token=WEBHOOK_SECRET, max_connections=40),
        loop
    )
    try:
        result = fut.result(timeout=10)
        return {'set_webhook': result, 'url': url}
    except Exception as e:
        return {'error': str(e), 'url': url}, 500

# ===== Booting modes =====
def _start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def runner():
        await application.initialize()
        await application.start()
        await application.wait_until_closed()
    loop.create_task(runner())
    loop.run_forever()

# Bila di Render (RUN_MODE=render), mula thread PTB semasa import (gunicorn akan serve Flask app)
if RUN_MODE == 'render':
    bot_thread = threading.Thread(target=_start_bot_thread, daemon=True)
    bot_thread.start()

# Bila di local, jalankan polling terus
if __name__ == '__main__' and RUN_MODE != 'render':
    application.run_polling()
