import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler


updater = None
dispatcher = None
classifyGame = None
detect_checkers = None


def send_message(bot, chat_id, text):
    bot.send_message(chat_id=chat_id, text=text)


def start(update: Update, context: CallbackContext):
    send_message(context.bot, update.effective_chat.id, 'Hello!\nSend me a picture of a board game and i will try to classify it!')


def send_checkers_options(update: Update):
    keyboard = [
        [InlineKeyboardButton("White", callback_data='White')],
        [InlineKeyboardButton("Black", callback_data='Black')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Who started playing on top?', reply_markup=reply_markup)


def checkers_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    query.edit_message_text(text=f"{query.data} started playing on top")

    try:
        send_message(context.bot, update.effective_chat.id, 'Analyzing checkers game field...')
        detect_checkers('image.png', update.effective_chat.id, query.data=='Black')
    except:
        send_message(context.bot, update.effective_chat.id, 'Analyzing failed!')


def image_handler(update: Update, context: CallbackContext):
    image_id = None
    if update.message.document is not None:
        image_id = update.message.document.file_id
    elif update.message.photo != []:
        image_id = update.message.photo[len(update.message.photo) - 1].file_id

    if image_id is not None:
        obj = context.bot.get_file(image_id)
        obj.download('image.png')

        game_type = classifyGame('image.png')
        send_message(context.bot, update.effective_chat.id, 'This is a "' + game_type + '" game!')
        if game_type == 'checkers':
            send_checkers_options(update=update)
    else:
        send_message(context.bot, update.effective_chat.id, 'The error has occured')


def initBot(token=None, classifyGameFunction=None, detect_checkersFunction=None):
    global updater
    global dispatcher
    global classifyGame
    global detect_checkers

    if token is None:
        print('Please specify telegram bot token')
        return

    classifyGame = classifyGameFunction
    detect_checkers = detect_checkersFunction

    updater = Updater(token=token, use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler((Filters.document.image | Filters.photo) & (~Filters.command), image_handler))
    dispatcher.add_handler(CallbackQueryHandler(checkers_button))

    updater.start_polling()
    return updater.bot


def stopBot():
    if updater is not None:
        updater.stop_polling()
        print('Bot has stopped')
    else:
        print('Bot was already stopped')
