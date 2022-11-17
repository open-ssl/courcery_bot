import telebot
from telebot import types
import helpers

from helpers import (
    write_cources_for_korona,
    write_cources_for_unistream
)


bot = telebot.TeleBot(helpers.API_TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    """
    Входная команда нашего бота
    :param message: обьект сообщения для пользователя
    :return:
    """
    # занести пользователя в базу - имя, уникальный айдишник, дата последнего обращения к боту
    bot.send_message(message.chat.id, helpers.BotMessage.START_BOT_NESSAGE, parse_mode="html")


if __name__ == '__main__':

    write_cources_for_korona()
    write_cources_for_unistream()
    bot.polling(none_stop=True)