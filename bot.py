from typing import Dict
from telegram import Bot, ParseMode, ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, PicklePersistence
import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.environ.get('PORT', '8443'))
CHOOSING, TYPING_REPLY, USER_CHOICE = range(3)

reply_choices = [
    ['Main Quest', 'Side Quest'],
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

def mq_restaurant_choice(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Enter the name of the restaurant and date:\n<i>example: Choichi Ramen - June 9 2022 - MQ</i>',
        parse_mode='HTML'
    )

    return USER_CHOICE

def sq_choice(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Enter the name of the side quest:\n<i>example: Ken's Rerun - June 27 2022 - SQ</i>",
        parse_mode='HTML'
    )

    return USER_CHOICE

def quest_details(update: Update, context: CallbackContext) -> int:
    context.chat_data['choice'] = update.message.text
    reply_text = f'Who are the participants to go to {update.message.text}?'

    update.message.reply_text(reply_text)

    return TYPING_REPLY

def log_list(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        text=f"<b><u>Foo'Croo Log List</u></b>\n{format_log(context.chat_data)}",
        parse_mode='HTML'
    )

def log_info(update: Update, context: CallbackContext) -> int:
    category = context.chat_data["choice"]
    context.chat_data[category] = update.message.text
    del context.chat_data["choice"]

    update.message.reply_text(
        text="<b><u>SUCCESSFULLY LOGGED</u></b>\n\nUse /logs to view the log list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def done(update: Update, context: CallbackContext) -> int:
    if 'choice' in context.chat_data:
        del context.chat_data['choice']

    update.message.reply_text(
        text="<b><u>SUCCESSFULLY LOGGED</u></b>\n\nUse /logs to view the log list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def commands_list(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        text="<b><u>Foo'Croo Bot Commands List</u></b>\n\n"
        "/start - <i>starts the logging process</i>\n"
        "/logs - <i>the complete Foo'Croo Log List</i>\n"
        "/delete - <i>deletes a specified entry</i>\n"
        "/source - <i>the source code of this bot</i>",
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
    
    return USER_CHOICE

def confirm_delete(update: Update, context: CallbackContext):
    context.chat_data.pop(update.message.text)
    update.message.reply_text(
        text=f"{update.message.text} - <b><u>SUCCESSFULLY REMOVED</u></b>\n\nUse /logs to view the log list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def main() -> None: 
    TOKEN = os.getenv("TOKEN")
    persistence = PicklePersistence(filename='loglist')
    updater = Updater(TOKEN, persistence=persistence)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^Main Quest$'), mq_restaurant_choice), 
                MessageHandler(Filters.regex('^Side Quest$'), sq_choice),
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

    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete_entry)],
        states={
            USER_CHOICE: [
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
    dispatcher.add_handler(CommandHandler("commands", commands_list))
    dispatcher.add_handler(CommandHandler("source", source_code))

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url='https://fierce-sierra-52458.herokuapp.com/' + TOKEN), 
    updater.idle()

if __name__ == '__main__':
    main()
    
