import telebot
from telebot import types
from functools import partial

from db_helpers import (
    create_all_tables,
    initialize_current_price_table,
    initialize_exchange_table,
    check_user_in_db,
    add_user_in_db,
    show_country_info_for_user
)

import db_helpers
from helpers import (
    API_TOKEN,
    Country,
    BotMessage,
    BotCommand,
    write_cources_for_korona,
    write_cources_for_unistream,
    write_cources_for_contact,
    write_cources_for_rico
)


bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    """
    Входная команда нашего бота
    :param message: обьект сообщения для пользователя
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()
    have_user_in_db = check_user_in_db(message)

    if not have_user_in_db:
        add_user_in_db(message)

    bot_actual_commands = BotCommand.get_main_menu_commands()
    for callback_command, command_text in bot_actual_commands.items():
        keyboard_button = partial(types.InlineKeyboardButton, text=command_text,
                                  callback_data=callback_command, url=None)

        keyboard.add(keyboard_button())

    bot.send_message(
        message.chat.id,
        BotMessage.START_BOT_NESSAGE, parse_mode="html",
        reply_markup=keyboard
    )


def сhoice_country_for_cource(message):
    keyboard = types.InlineKeyboardMarkup()
    bot_actual_commands = BotCommand.get_commands_for_countries()

    for callback_command, command_text in bot_actual_commands.items():
        keyboard_button = partial(types.InlineKeyboardButton, text=command_text, callback_data=callback_command, url=None)
        keyboard.add(keyboard_button())

    bot.send_message(message.chat.id, BotMessage.CHOICE_COUNTRY_FOR_COURCE, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    """
    Проверяем все колбеки и в зависимости от выбранной секции, основная или админская, даем ему ответ на сообщение
    """
    if call.message:
        if call.data == BotCommand.MAIN_MENU:
            start_command(call.message)
        elif call.data == BotCommand.CHOICE_COUNTRY:
            сhoice_country_for_cource(call.message)
        elif call.data == BotCommand.WRITE_DEVELOPER:
            bot.send_message(call.message.chat.id, BotMessage.HELP_PROJECT_TEXT)
        elif call.data == BotCommand.HELP_PROJECT:
            bot.send_message(call.message.chat.id, BotMessage.HELP_PROJECT)
        elif call.data in BotCommand.get_country_commands():
            country_name = BotCommand.get_country_by_command(call.data)
            result_message = show_country_info_for_user(call.message, country_name)
            bot.send_message(call.message.chat.id, result_message, parse_mode="html")


if __name__ == '__main__':
    # create_all_tables()
    # initialize_current_price_table()
    # initialize_exchange_table()
    # write_cources_for_korona()
    # write_cources_for_unistream()
    # write_cources_for_contact()
    # write_cources_for_rico()
    bot.polling(none_stop=True)
