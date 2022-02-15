import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler


USERS_IMAGES = '/output/users'
updater = None
dispatcher = None
handlers = None
checkers_img = None
carcassone_img = None


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
    global checkers_img
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"{query.data} started playing on top")

    try:
        send_message(context.bot, update.effective_chat.id, 'Analyzing checkers game field...')
        handlers['detect_checkers'](checkers_img, update.effective_chat.id, query.data=='Black')
    except:
        send_message(context.bot, update.effective_chat.id, 'Analyzing failed!')

    checkers_img = None


def image_handler(update: Update, context: CallbackContext):
    global carcassone_img
    global checkers_img

    user_dir = f'{USERS_IMAGES}/{update.effective_chat.username}'
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
    
    user_images = [s for s in os.listdir(user_dir) if os.path.isfile(os.path.join(user_dir, s))]
    image_suffix = str(len(user_images) + 1)

    image_path = f'{user_dir}/image_{image_suffix}.png'

    image_id = None
    if update.message.document is not None:
        image_id = update.message.document.file_id
    elif update.message.photo != []:
        image_id = update.message.photo[len(update.message.photo) - 1].file_id

    if image_id is not None:
        if carcassone_img is not None:
            carcassone_img = None
            obj = context.bot.get_file(image_id)
            carcassone_card_path = carcassone_img.replace('image', 'carcassone_card')
            obj.download(carcassone_card_path)
            try:
                send_message(context.bot, update.effective_chat.id, 'Analyzing carcassone game field...')
                handlers['detect_carcassone'](carcassone_img, carcassone_card_path, update.effective_chat.id)
            except:
                send_message(context.bot, update.effective_chat.id, 'Analyzing failed!')
        else:
            obj = context.bot.get_file(image_id)
            obj.download(image_path)

            game_type = handlers['classifyGame'](image_path)
            send_message(context.bot, update.effective_chat.id, 'This is a "' + game_type + '" game!')
            if game_type == 'checkers':
                checkers_img = image_path
                send_checkers_options(update=update)
            elif game_type == 'ttt':
                send_message(context.bot, update.effective_chat.id, 'Analyzing tictactoe game field...')
                handlers['detect_tictactoe'](image_path, update.effective_chat.id)
            elif game_type == 'carcassone':
                carcassone_img = image_path
                send_message(context.bot, update.effective_chat.id, 'Please send a photo of the card')
    else:
        send_message(context.bot, update.effective_chat.id, 'The error has occured')


def initBot(token=None, handlers_fns=None):
    global updater
    global dispatcher
    global handlers

    handlers = handlers_fns

    if not os.path.exists(USERS_IMAGES):
        os.mkdir(USERS_IMAGES)

    if token is None:
        print('Please specify telegram bot token')
        return

    updater = Updater(token=token, use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler((Filters.document.image | Filters.photo) & (~Filters.command), image_handler))
    dispatcher.add_handler(CallbackQueryHandler(checkers_button))

    updater.start_polling()
    return updater.bot
