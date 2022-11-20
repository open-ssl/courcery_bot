import telebot
from telebot import types

from db_helpers import (
    create_all_tables,
    initialize_current_price_table,
    initialize_exchange_table
)

import db_helpers
from helpers import (
    API_TOKEN,
    BotMessage,
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
    # занести пользователя в базу - имя, уникальный айдишник, дата последнего обращения к боту

    bot.send_message(message.chat.id, BotMessage.START_BOT_NESSAGE, parse_mode="html")


if __name__ == '__main__':
    create_all_tables()
    initialize_current_price_table()
    initialize_exchange_table()
    write_cources_for_korona()
    write_cources_for_unistream()
    write_cources_for_contact()
    write_cources_for_rico()
    bot.polling(none_stop=True)
