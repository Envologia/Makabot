import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from handlers import (
    start, register_name, register_university, register_age, register_gender,
    uni_selection_callback, register_interests, register_bio, register_photo,
    profile, browse, browse_response, matches, start_chat_callback, relay_chat_message, stop_chat
)
from confession import get_confess_conv_handler
from db import init_db

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "supersecret")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")  # e.g. https://your-app.onrender.com

app = Flask(__name__)
init_db()

telegram_app = ApplicationBuilder().token(TOKEN).build()

(NAME, UNIVERSITY, AGE, GENDER, INTERESTS, BIO, PHOTO, SELECT_UNIS) = range(8)
reg_conv = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        UNIVERSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_university)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_age)],
        GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_gender)],
        SELECT_UNIS: [CallbackQueryHandler(uni_selection_callback)],
        INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_interests)],
        BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_bio)],
        PHOTO: [MessageHandler(filters.PHOTO, register_photo)],
    },
    fallbacks=[],
)
telegram_app.add_handler(reg_conv)
telegram_app.add_handler(CommandHandler('profile', profile))
telegram_app.add_handler(CommandHandler('browse', browse))
telegram_app.add_handler(MessageHandler(filters.Regex(r"^(👍 Like|⏭️ Skip)$"), browse_response))
telegram_app.add_handler(CommandHandler('matches', matches))
telegram_app.add_handler(CallbackQueryHandler(start_chat_callback, pattern="^chatwith_"))
telegram_app.add_handler(CommandHandler('stopchat', stop_chat))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay_chat_message))
telegram_app.add_handler(MessageHandler(filters.PHOTO, relay_chat_message))
telegram_app.add_handler(get_confess_conv_handler())

@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "OK"

@app.route("/", methods=["GET"])
def index():
    return "Unimatch Ethio bot is running!"

if __name__ == "__main__":
    import telegram
    bot = telegram.Bot(token=TOKEN)
    webhook_url = f"{RENDER_EXTERNAL_URL}/{WEBHOOK_SECRET}"
    bot.delete_webhook()
    bot.set_webhook(url=webhook_url)
    app.run(host="0.0.0.0", port=10000)
