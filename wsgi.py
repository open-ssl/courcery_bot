from main import bot

from db_helpers import (
    create_all_tables,
    initialize_current_price_table,
    initialize_exchange_table
)


if __name__ == '__main__':
    create_all_tables()
    initialize_current_price_table()
    initialize_exchange_table()
    bot.polling(none_stop=True)
