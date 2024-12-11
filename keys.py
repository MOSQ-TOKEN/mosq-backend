import telebot

def welcome_keyboard():
    app_url = "https://t.me/mosqquitoesbot/mosq"
    community_url = "https://t.me/"

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        telebot.types.InlineKeyboardButton(text="Launch App", url=app_url),
        telebot.types.InlineKeyboardButton(text="Join Community", url=community_url)
    ]
    markup.add(*buttons)
    return markup
