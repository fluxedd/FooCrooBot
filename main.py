from telegram import InlineKeyboardButton, Update 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os

API_KEY = os.getenv('API_KEY')

def start(update, context):
    update.message.reply_text("Hello. Welcome to Foo'Croo Bot.")

def bot_reply(update, context):
    update.message.reply_text(f"You said {update.effective_user.first_name}")

updater = Updater(API_KEY)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text, bot_reply))
updater.start_polling()
updater.idle()

