# confession.py

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from config import CONFESSION_CHANNEL_ID
from handlers import check_membership, require_channels

CONFESS = 100

async def confess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await require_channels(update, context)
        return ConversationHandler.END
    await update.message.reply_text(
        "💌 Write your anonymous confession (max 500 characters):\n"
        "Type /cancel to abort."
    )
    return CONFESS

async def receive_confession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if len(text) > 500:
        await update.message.reply_text("❌ Confession too long (max 500 characters). Try again:")
        return CONFESS

    await context.bot.send_message(
        chat_id=CONFESSION_CHANNEL_ID,
        text=f"📩 **New Confession:**\n\n{text}",
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "✅ Your confession has been posted anonymously!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel_confess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Confession cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def get_confess_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('confess', confess)],
        states={
            CONFESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_confession)],
        },
        fallbacks=[CommandHandler('cancel', cancel_confess)],
    )
