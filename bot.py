import os
from typing import Dict
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, PicklePersistence
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.environ.get('PORT', '8443'))
TOKEN = os.getenv("TOKEN")
CHOOSING, LOG_REPLY, RESTAURANT_REPLY, LOG_CHOICE, RESTAURANT_CHOICE = range(5)

reply_choices = [
    ['Main Quest', 'Side Quest'],
    ['Add Restaurant']
]
markup = ReplyKeyboardMarkup(reply_choices, one_time_keyboard=True, selective=True)
 
def format_log(log_data: Dict[str, str]) -> str:
    log = [f'\n{key} \nAttendees: {value}' for key, value in log_data.items()]
    return "\n".join(log)

def format_restaurants(restaurant_data: Dict[str, str]) -> str:
    list = [f'\n{key} @ {value}' for key, value in restaurant_data.items()]
    return "\n".join(list)


def start(update: Update, context: CallbackContext) -> int:
    reply_text="Please choose an option:"
    update.message.reply_text(
        reply_text, reply_markup=markup
    )

    return CHOOSING

def mq_restaurant_choice(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Enter the name of the restaurant and date:\n<i>example: Choichi Ramen - June 9 2022 - MQ</i>',
        parse_mode='HTML'
    )

    return LOG_CHOICE

def sq_choice(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Enter the name of the side quest:\n<i>example: Ken's Rerun - June 27 2022 - SQ</i>",
        parse_mode='HTML'
    )

    return LOG_CHOICE

def restaurant_choice(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Enter the potential Foo'Croo restaurant:\n<i>example: East Ocean</i>",
        parse_mode='HTML'
    )

    return RESTAURANT_CHOICE

def quest_details(update: Update, context: CallbackContext) -> int:
    context.bot_data['choice'] = update.message.text
    reply_text = f'Who are the participants to go to {update.message.text}?'

    update.message.reply_text(reply_text)

    return LOG_REPLY

def restaurant_details(update: Update, context: CallbackContext) -> int:
    context.chat_data['choice'] = update.message.text
    reply_text = f'What is the address of {update.message.text}?'

    update.message.reply_text(reply_text)

    return RESTAURANT_REPLY

def log_info(update: Update, context: CallbackContext) -> int:
    category = context.bot_data["choice"]
    context.bot_data[category] = update.message.text
    del context.bot_data["choice"]

    update.message.reply_text(
        text="<b><u>SUCCESSFULLY LOGGED</u></b>\n\nUse /logs to view the log list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def restaurant_info(update: Update, context: CallbackContext) -> int:
    category = context.chat_data["choice"]
    context.chat_data[category] = update.message.text
    del context.chat_data["choice"]

    update.message.reply_text(
        text="<b><u>SUCCESSFULLY ADDED</u></b>\n\nUse /restaurants to view the potential restaurants list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def done(update: Update, context: CallbackContext) -> int:
    if 'choice' in context.bot_data:
        del context.bot_data['choice']

    update.message.reply_text(
        text="There was an error. Restart the process.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def commands_list(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        text="<b><u>Foo'Croo Bot Commands List</u></b>\n\n"
        "/start - <i>starts the process</i>\n"
        "/logs - <i>the complete Foo'Croo Log List</i>\n"
        "/restaurants - <i>the potential Foo'Croo Restaurant List\n"
        "/delete - <i>deletes a specified log entry</i>\n"
        "/source - <i>the source code of this bot</i>",
        parse_mode='HTML'
    )

def log_list(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        text=f"<b><u>Foo'Croo Log List</u></b>\n{format_log(context.bot_data)}",
        parse_mode='HTML'
    )

def restaurant_list(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        text=f"<b><u>Potential Foo'Croo Restaurants List</u></b>\n{format_restaurants(context.chat_data)}",
        parse_mode='HTML'
    )
    
def source_code(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        text="You can find the source code for this project at:\n\nhttps://github.com/fluxedd/FooCrooBot"
    )

def delete_entry(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="Enter the log name of the entry to be removed:\n"
             "<i>example: copy and paste -> Ken's Rerun - June 27 2022 - SQ</i>",
        parse_mode='HTML'
    )
    
    return LOG_CHOICE

def confirm_delete(update: Update, context: CallbackContext):
    context.bot_data.pop(update.message.text)
    update.message.reply_text(
        text=f"{update.message.text} - <b><u>SUCCESSFULLY REMOVED</u></b>\n\nUse /logs to view the log list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def main() -> None: 
    persistence = PicklePersistence(filename='loglist')
    updater = Updater(token="5347268144:AAFXNbTHI2JZ8FT32CT8P6j7viv43vAFbgQ", persistence=persistence)
    
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^Main Quest$'), mq_restaurant_choice), 
                MessageHandler(Filters.regex('^Side Quest$'), sq_choice),
                MessageHandler(Filters.regex('^Add Restaurant$'), restaurant_choice),
            ],
            LOG_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), quest_details
                ),
            ],
            RESTAURANT_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), restaurant_details
                ),
            ],
            LOG_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), log_info
                ),
            ],
            RESTAURANT_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), restaurant_info
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.text, done)],
        name="log_convo",
        persistent=True,
    )

    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete_entry)],
        states={
            LOG_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.regex('^Yes$')), confirm_delete
                )
            ]
        },
        fallbacks=[MessageHandler(Filters.text, done)],
    )
    
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(delete_conv_handler)

    dispatcher.add_handler(CommandHandler("logs", log_list))
    dispatcher.add_handler(CommandHandler("restaurants", restaurant_list))
    dispatcher.add_handler(CommandHandler("commands", commands_list))
    dispatcher.add_handler(CommandHandler("source", source_code))

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path="5347268144:AAFXNbTHI2JZ8FT32CT8P6j7viv43vAFbgQ",
                          webhook_url='https://fierce-sierra-52458.herokuapp.com/' + "5347268144:AAFXNbTHI2JZ8FT32CT8P6j7viv43vAFbgQ"), 
    updater.idle()

if __name__ == '__main__':
    main()
    
