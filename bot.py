import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# =====================
# CONFIG
# =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# =====================
# LOGGING
# =====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# =====================
# COMMANDS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm a ChatGPT-powered bot.\nJust send me any message and I'll reply."
    )

# =====================
# MESSAGE HANDLER
# =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    user_message = update.message.text

    payload = {
        "chat_id": chat_id,
        "username": username,
        "message": user_message,
    }

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=90,
        )

        logging.info("Status: %s", response.status_code)
        logging.info("Raw response: %s", response.text)

        response.raise_for_status()
        data = response.json()

        reply = None

        # ==========================
        # HANDLE ARRAY RESPONSE
        # ==========================
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                reply = first_item.get("output")

        # ==========================
        # HANDLE OBJECT RESPONSE
        # ==========================
        elif isinstance(data, dict):
            reply = (
                data.get("reply")
                or data.get("output")
                or data.get("body", {}).get("reply")
                or data.get("body", {}).get("output")
            )

        if not reply:
            reply = "⚠️ AI responded, but no readable message was found."

        await update.message.reply_text(reply)

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏳ AI response timed out.")
    except Exception as e:
        logging.exception("Error contacting n8n")
        await update.message.reply_text("❌ Error communicating with AI.")


# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()