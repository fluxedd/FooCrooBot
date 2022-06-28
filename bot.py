import os
from typing import Dict
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, PicklePersistence
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras


PORT = int(os.environ.get('PORT', '8443'))
TOKEN = os.environ.get('BOT_TOKEN')

CHOOSING, RESTO_CHOICE, DATE, ATTENDEES, STOP = range(5)

DATABASE_URL = os.environ.get('DB_URL')

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

reply_choices = [
    ['Main Quest', 'Side Quest']
]
markup = ReplyKeyboardMarkup(reply_choices, one_time_keyboard=True, selective=True)

def start(update: Update, context: CallbackContext) -> int:
    reply_text="Please choose an option:"
    update.message.reply_text(
        reply_text, reply_markup=markup
    )

    return CHOOSING

def log_restaurant(update: Update, context: CallbackContext) -> int:
    if update.message.text == 'Main Quest':
        type = 'MQ'
    if update.message.text == 'Side Quest':
        type = 'SQ'
    context.user_data['type'] = type
    update.message.reply_text(
        '<b>Enter the name of the restaurant:</b>\n<i>example: Choichi Ramen</i>',
        parse_mode='HTML'
    )

    return RESTO_CHOICE

def log_date(update: Update, context: CallbackContext) -> int:
    context.user_data['resto'] = update.message.text
    update.message.reply_text(text="<b>Enter the date (YYYY-MM-DD):</b> \n<i>example: 2022-06-27</i>", parse_mode='HTML')

    return DATE

def log_attendees(update: Update, context: CallbackContext) -> int:
    context.user_data['date'] = update.message.text
    update.message.reply_text(text="<b>List the attendees:</b> \n<i>example: Eril, Mark, Jericho, Nick</i>", parse_mode='HTML')

    return ATTENDEES

def logged(update: Update, context: CallbackContext):
    context.user_data['attendees'] = update.message.text

    log_script = "INSERT INTO logs (restaurant, date, attendees, quest_type) VALUES (%s, %s, %s, %s)"
    log_insert = (context.user_data['resto'], context.user_data['date'], context.user_data['attendees'], context.user_data['type'])
    cur.execute(log_script, log_insert)
    conn.commit()
    
    update.message.reply_text(
        text="<b><u>SUCCESSFULLY LOGGED</u></b>\n\nUse /logs to view the log list.",
        parse_mode='HTML'
    )

    del context.user_data['type']
    del context.user_data['resto']
    del context.user_data['date']
    del context.user_data['attendees']

    return ConversationHandler.END

# def restaurant_choice(update: Update, context: CallbackContext) -> int:
#     update.message.reply_text(
#         "Enter the potential Foo'Croo restaurant:\n<i>example: East Ocean</i>",
#         parse_mode='HTML'
#     )

#     return RESTAURANT_CHOICE

# def restaurant_details(update: Update, context: CallbackContext) -> int:
#     context.chat_data['choice'] = update.message.text
#     reply_text = f'What is the address of {update.message.text}?'

#     update.message.reply_text(reply_text)

#     return RESTAURANT_REPLY


# def restaurant_info(update: Update, context: CallbackContext) -> int:
#     category = context.chat_data["choice"]
#     context.chat_data[category] = update.message.text
#     del context.chat_data["choice"]

#     update.message.reply_text(
#         text="<b><u>SUCCESSFULLY ADDED</u></b>\n\nUse /restaurants to view the potential restaurants list.",
#         parse_mode='HTML'
#     )

    # return ConversationHandler.END

def commands_list(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        text="<b><u>Foo'Croo Bot Commands List</u></b>\n\n"
        "/start - <i>starts the process</i>\n"
        "/logs - <i>the complete Foo'Croo Log List</i>\n"
        "/restaurants - <i>the potential Foo'Croo Restaurant List</i>\n"
        "/delete - <i>deletes a specified log entry</i>\n"
        "/source - <i>the source code of this bot</i>",
        parse_mode='HTML'
    )

def source_code(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        text="You can find the source code for this project at:\n\nhttps://github.com/fluxedd/FooCrooBot"
    )

# def delete_entry(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         text="Enter the log name of the entry to be removed:\n"
#              "<i>example: copy and paste -> Ken's Rerun - June 27 2022 - SQ</i>",
#         parse_mode='HTML'
#     )
    
#     return LOG_CHOICE

def logs(update: Update, context: CallbackContext):
    cur.execute('SELECT restaurant, date, attendees, quest_type FROM logs ORDER BY date' )
    data = ''
    for record in cur.fetchall():
        data += f"\n\n<b>{record['restaurant']}</b> | {record['date']} | {record['quest_type']} \n<b>Attendees: </b>{record['attendees']}"
        
    update.message.reply_text(text="<b><u>Foo'Croo Log List</u></b>" + data, parse_mode='HTML')

def flush(update: Update, context: CallbackContext):
    del context.user_data['type']
    del context.user_data['resto']
    del context.user_data['date']
    del context.user_data['attendees']

    update.message.reply_text("Please restart the process using /start.")

def confirm_delete(update: Update, context: CallbackContext):
    context.bot_data.pop(update.message.text)
    update.message.reply_text(
        text=f"{update.message.text} - <b><u>SUCCESSFULLY REMOVED</u></b>\n\nUse /logs to view the log list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def main() -> None: 
    persistence = PicklePersistence(filename='loglist')
    updater = Updater(token=TOKEN, persistence=persistence)
    
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^Main Quest$') | Filters.regex('^Side Quest$'), log_restaurant),
            ],
            RESTO_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), log_date
                ),
            ],
            DATE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), log_attendees
                ),
            ],
            ATTENDEES: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), logged
                ),
            ],
        },
        fallbacks=[MessageHandler(Filters.text, flush)],
        name="log_convo",
        persistent=True,
    )

    # delete_conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler('delete', delete_entry)],
    #     states={
    #         LOG_CHOICE: [
    #             MessageHandler(
    #                 Filters.text & ~(Filters.regex('^Yes$')), confirm_delete
    #             )
    #         ]
    #     },
    #     fallbacks=[MessageHandler(Filters.text, done)],
    # )
    
    dispatcher.add_handler(conv_handler)
    # dispatcher.add_handler(delete_conv_handler)

    dispatcher.add_handler(CommandHandler("commands", commands_list))
    dispatcher.add_handler(CommandHandler('logss', logs))
    dispatcher.add_handler(CommandHandler('flush', flush))
    dispatcher.add_handler(CommandHandler("source", source_code))

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url='https://fierce-sierra-52458.herokuapp.com/' + TOKEN), 
    
    updater.idle()

if __name__ == '__main__':
    main()
    
