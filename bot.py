import os
from typing import Dict
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, PicklePersistence
import psycopg2
import psycopg2.extras

PORT = os.environ.get('PORT', '8443')
TOKEN = os.environ.get('BOT_TOKEN')

DB = os.environ.get('DB_DB')
HOST = os.environ.get('DB_HOST')
USER = os.environ.get('DB_USER')
PWD = os.environ.get('DB_PASS')

CHOOSING, RESTO_CHOICE, DATE, ATTENDEES, RESTAURANT, ADDRESS, DELETE_LOG, LOG_DELETED = range(8)

conn = psycopg2.connect(
    host = HOST,
    dbname = DB,
    user = USER,
    password = PWD,
    port = 5432
)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

reply_choices = [
    ['Main Quest', 'Side Quest'],
    ['Add Restaurant', 'Delete Log'],
]

markup = ReplyKeyboardMarkup(reply_choices, one_time_keyboard=True, selective=True, resize_keyboard=True)

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

def add_restaurant(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        '<b>Enter the name of a potential restaurant:</b>\n<i>example: Choichi Ramen</i>',
        parse_mode='HTML'
    )

    return RESTAURANT

def add_address(update: Update, context: CallbackContext) -> int:
    context.user_data['restaurant'] = update.message.text
    update.message.reply_text(
        '<b>Enter the address of the restaurant:</b>',
        parse_mode='HTML'
    )

    return ADDRESS

def restaurant_added(update: Update, context: CallbackContext): 
    context.user_data['address'] = update.message.text
    added_by = update.message.from_user.first_name

    add_script = "INSERT INTO restaurants (restaurant, address, added_by) VALUES (%s, %s, %s)"
    add_insert = (context.user_data['restaurant'], context.user_data['address'], added_by)
    
    cur.execute(add_script, add_insert)
    conn.commit()

    update.message.reply_text(
        text="<b><u>SUCCESSFULLY ADDED</u></b>\n\nUse /restaurants to view the potential restaurants list.",
        parse_mode='HTML'
    )

    del context.user_data['restaurant']
    del context.user_data['address']

    return ConversationHandler.END

def delete_log(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        '<b>Enter the log to be deleted:</b>\n<i>example: RFK Rerun #1</i>',
        parse_mode='HTML'
    )

    return LOG_DELETED

def log_deleted(update: Update, context: CallbackContext): 
    delete_script = "DELETE FROM logs WHERE restaurant = %s"
    record = (update.message.text,)

    cur.execute(delete_script, record)
    conn.commit()

    update.message.reply_text(
        text="<b><u>SUCCESSFULLY DELETED</u></b>\n\nUse /logs to view the updated log list.",
        parse_mode='HTML'
    )

    return ConversationHandler.END

def logs(update: Update, context: CallbackContext):
    cur.execute('SELECT restaurant, date, attendees, quest_type FROM logs ORDER BY date' )
    data = ''
    for record in cur.fetchall():
        data += f"\n\n<b>{record['restaurant']}</b> | {record['date']} | {record['quest_type']} \n<b>Attendees: </b>{record['attendees']}"
        
    update.message.reply_text(text="<b><u>Foo'Croo Log List</u></b>" + data, parse_mode='HTML')

def restaurant_list(update: Update, context: CallbackContext):
    cur.execute('SELECT restaurant, address, added_by FROM restaurants')
    data = ''
    for record in cur.fetchall():
        data += f"\n\n<b>{record['restaurant']}</b> @ {record['address']}\n  <i>added by: {record['added_by']}</i>"
        
    update.message.reply_text(text="<b><u>Potential Foo'Croo Restaurants List</u></b>" + data, parse_mode='HTML')

def commands_list(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        text="<b><u>Foo'Croo Bot Commands List</u></b>\n\n"
        "/start - starts the process\n"
        "/logs - the complete Foo'Croo Log List\n"
        "/restaurants - the potential Foo'Croo Restaurant List\n"
        "/source - the source code of this bot",
        parse_mode='HTML'
    )

def source_code(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        text="You can find the source code for this project at:\n\nhttps://github.com/fluxedd/FooCrooBot"
    )

def flush(update: Update, context: CallbackContext):
    update.message.reply_text("Please restart the process using /start.")
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
                MessageHandler(Filters.regex('^Add Restaurant$'), add_restaurant),
                MessageHandler(Filters.regex('^Delete Log$'), delete_log),
            ],
            RESTO_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), log_date),
            ],
            DATE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), log_attendees),
            ],
            ATTENDEES: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), logged),
            ],
            RESTAURANT: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), add_address)
            ],
            ADDRESS: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), restaurant_added)
            ],
            LOG_DELETED: [
               MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), log_deleted) 
            ]
        },
        fallbacks=[MessageHandler(Filters.text, flush)],
        name="log_convo",
        persistent=True,
    )
    
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('commands', commands_list))
    dispatcher.add_handler(CommandHandler('logs', logs))
    dispatcher.add_handler(CommandHandler('restaurants', restaurant_list))
    dispatcher.add_handler(CommandHandler('source', source_code))
    dispatcher.add_handler(CommandHandler('flush', flush))

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url='https://foocroo-bot.herokuapp.com/' + TOKEN), 
    
    updater.idle()

if __name__ == '__main__':
    main()
    
