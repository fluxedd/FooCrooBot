from typing import Dict
from telegram import InlineKeyboardButton, MessageEntity, ReplyKeyboardMarkup, Update, TelegramObject
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ContextTypes, ConversationHandler, PicklePersistence
import os

API_KEY = os.getenv('API_KEY')

CHOOSING, TYPING_REPLY, USER_CHOICE = range(3)

reply_choices = [
    ['Main Quest', 'Side Quest'], 
    ['Done'],
]
markup = ReplyKeyboardMarkup(reply_choices, one_time_keyboard=True, selective=True)
 
def format_log(log_data: Dict[str, str]) -> str:
    log = [f'\n{key} \nAttendees: {value}' for key, value in log_data.items()]
    return "\n".join(log)
    
def start(update: Update, context: CallbackContext) -> int:
    reply_text="Please choose an option:"
    update.message.reply_text(
        reply_text, reply_markup=markup
    )

    return CHOOSING

def restaurant_choice(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Enter the name of the restaurant and date:\n<i>example: Choichi Ramen - June 9 2022</i>',
        parse_mode='HTML'
    )

    return USER_CHOICE

def quest_details(update: Update, context: CallbackContext) -> int:
    context.user_data['choice'] = update.message.text
    reply_text = f'Who are the participants to go to {update.message.text}?'

    update.message.reply_text(reply_text)

    return TYPING_REPLY

def log_list(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        text=f"<b><u>Foo'Croo Log List</u></b>\n{format_log(context.user_data)}",
        parse_mode='HTML'
    )

def log_info(update: Update, context: CallbackContext) -> int:
    category = context.user_data["choice"]
    context.user_data[category] = update.message.text
    del context.user_data["choice"]

    update.message.reply_text(
        text=f"<b><u>Foo'Croo Log List</u></b>\n{format_log(context.user_data)}",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def done(update: Update, context: CallbackContext) -> int:
    if 'choice' in context.user_data:
        del context.user_data['choice']

    update.message.reply_text(
        text=f"<b><u>Foo'Croo Log List</u></b>\n{format_log(context.user_data)}",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def main() -> None:
    persistence = PicklePersistence(filename='loglist')
    updater = Updater(API_KEY, persistence=persistence)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^Main Quest$'), restaurant_choice), 
            ],
            USER_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), quest_details
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), log_info
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.text, done)],
        name="log_convo",
        persistent=True,
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_handler(CommandHandler("loglist", log_list))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    
