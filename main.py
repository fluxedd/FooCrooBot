from telegram import Update 
from telegram.ext import Updater, CommandHandler
import os

API_KEY = os.getenv('API_KEY')

updater = Updater(API_KEY)
dispatcher = updater.dispatcher