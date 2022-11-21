import json
import pytz
import sqlite3
from datetime import datetime
from pay_methods.korona import get_korona_currency_dependencies_by_country
from pay_methods.unistream import get_unistream_currency_dependencies_by_country
from pay_methods.contact import get_contact_currency_dependencies_by_country, ContactAccountForCountry
from pay_methods.rico import RicoCurrencyNames

from helpers import Country, Const, Currency, PayType, Operation, BotMessage
# in seconds
EXPIRED_DATA_INTERVAL = 600


def get_connection_for_db():
    return sqlite3.connect('data.db')


def create_all_tables():
    conn = get_connection_for_db()
    country_data = Country.get_country_data()
    currency_data = Currency.get_currency_data()
    pay_types = PayType.get_pay_types()

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    message_chat_id TEXT PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    country TEXT,
                    last_update_data TEXT
                )
            """
            )
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS country (
                    country_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_name TEXT,
                    full_name TEXT
                )
            """
            )
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS currency (
                    currency_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency_name TEXT
                )
            """
            )
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pay_type (
                    pay_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pay_type_name TEXT
                )
            """
            )
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS current_price (
                    country_full_name TEXT,
                    currency_name TEXT,
                    pay_type_name TEXT,
                    current_price TEXT,
                    current_tax TEXT,
                    last_update_date TEXT
                )
            """
            )
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS current_exchange (
                    country_full_name TEXT,
                    currency_name TEXT,
                    base_country_currency TEXT,
                    exchange_operation TEXT, 
                    current_rate TEXT,
                    last_update_date TEXT
                )
            """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS "
                           "user_id_index ON users (message_chat_id);")

            # for country_info in country_data:
            #     country_short_name = country_info[0]
            #     country_full_name = country_info[1]
            #     cursor.execute(f"""
            #         INSERT INTO country (short_name, full_name)
            #         VALUES ('{country_short_name}', '{country_full_name}')
            #     """)
            #
            # for currency_name in currency_data:
            #     cursor.execute(f"""
            #         INSERT INTO currency (currency_name)
            #         VALUES ('{currency_name}')
            #     """)
            #
            # for pay_type in pay_types:
            #     cursor.execute(f"""
            #         INSERT INTO pay_type (pay_type_name)
            #         VALUES ('{pay_type}')
            #     """)

            print('Tables were create!')
    except Exception as e:
        pass


def initialize_korona_pay_in_price_table():
    korona_currencies_by_country = get_korona_currency_dependencies_by_country()
    conn = get_connection_for_db()
    for country, currency_list in korona_currencies_by_country.items():
        country_full_name = Country.get_full_name_by_short(country)
        for currency_id in currency_list:
            currency_name = Currency.get_name_by_korona_id(currency_id)
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    INSERT_DATA_IN_CURRENT_PRICE.format(
                        country_full_name, currency_name, PayType.KORONA_PAY
                    )
                )
    print('Korona_pay price initialized')


def initialize_unistream_in_price_table():
    unistream_currencies_by_country = get_unistream_currency_dependencies_by_country()
    conn = get_connection_for_db()
    for country, currency_list in unistream_currencies_by_country.items():
        country_full_name = Country.get_full_name_by_short(country)
        for currency_name in currency_list:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    INSERT_DATA_IN_CURRENT_PRICE.format(
                        country_full_name, currency_name, PayType.UNISTREAM
                    )
                )

    print('Unistream price initialized')


def initialize_contact_in_price_table():
    contact_currencies_by_country = get_contact_currency_dependencies_by_country()
    conn = get_connection_for_db()
    for country, account_name in contact_currencies_by_country.items():
        country_full_name = Country.get_full_name_by_short(country)
        currency_name = ContactAccountForCountry.get_currency_by_account(account_name)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                INSERT_DATA_IN_CURRENT_PRICE.format(
                    country_full_name, currency_name, PayType.CONTACT
                )
            )
    print('Contact price initialized')


def initialize_current_price_table():
    initialize_korona_pay_in_price_table()
    initialize_unistream_in_price_table()
    initialize_contact_in_price_table()


def initialize_exchange_table():
    list_of_currencies = RicoCurrencyNames.all_currency_names()
    list_of_operations = Operation.get_operations()
    list_of_contries = Country.get_country_data()

    conn = get_connection_for_db()
    for country_info in list_of_contries:
        country_short = country_info[0]
        country = country_info[1]
        for currency in list_of_currencies:
            for operation in list_of_operations:
                base_currency = Country.get_base_currency_for_country(country_short)
                currency = Currency.RUB if currency == 'rur' else currency
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(INSERT_DATA_IN_CURRENT_EXCHANGE.format(country, currency.upper(), base_currency, operation))

    print('Exchange table initialized')


def update_price_for_pay_type_in_db(current_price, current_tax, country_full_name, currency_name, pay_type_name):
    query_template = UPDATA_DATA_IN_CURRENT_PRICE.format(
        current_price, current_tax, country_full_name, currency_name, pay_type_name
    )
    conn = get_connection_for_db()

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
    except Exception as e:
        pass


def update_exchange_cources_pay_type_in_db(current_rate, country_full_name, currency_name, exchange_operation):
    query_template = UPDATE_DATA_IN_CURRENT_EXCHANGE.format(
        current_rate, country_full_name, currency_name, exchange_operation
    )

    conn = get_connection_for_db()

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
    except Exception as e:
        pass


def check_user_in_db(message_obj):
    query_template = CHECK_USER_IN_DB.format(message_obj.chat.id)
    conn = get_connection_for_db()

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
            query_result = cursor.fetchone()
    except Exception as e:
        pass

    return query_result[0]


def add_user_in_db(message_obj):
    chat_id = message_obj.chat.id
    first_name = message_obj.chat.first_name
    last_name = message_obj.chat.last_name
    user_name = message_obj.chat.username

    query_template = ADD_USER_IN_DB.format(
        chat_id, first_name, last_name, user_name
    )
    conn = get_connection_for_db()

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
    except Exception as e:
        pass


def show_country_info_for_user(message_obj, country_name):
    user_id = message_obj.chat.id
    query_template = UPDATE_COUNTRY_FOR_USER_IN_DB.format(
        country_name, user_id
    )
    conn = get_connection_for_db()

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
    except Exception as e:
        pass

    # получаем информацию из базы по стране по переводам
    query_template = GET_INFO_FOR_USER_BY_COUNTRY.format(country_name)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
            query_result = cursor.fetchall()
    except Exception as e:
        pass

    context_for_user = dict()

    for item in query_result:
        item = json.loads(item[0])

        currency_name = item.get(Const.CURRENCY_NAME)
        pay_type_name = item.get(Const.PAY_TYPE_NAME)
        current_price = item.get(Const.CURRENT_PRICE)
        current_tax = item.get(Const.CURRENT_TAX)
        last_update_date = item.get(Const.REFRESH_TIME)

        currency_name = Currency.LIR if currency_name == 'TRY' else currency_name

        if not last_update_date:
            continue

        now_utc_timestamp = datetime.utcnow().timestamp()
        refresh_interval = now_utc_timestamp - datetime.fromisoformat(last_update_date).timestamp()

        if refresh_interval > EXPIRED_DATA_INTERVAL:
            continue

        if currency_name not in context_for_user:
            context_for_user[currency_name] = {}

        inner_context = context_for_user.get(currency_name)
        inner_context[pay_type_name] = [current_price, current_tax]
        context_for_user[currency_name] = inner_context

    country_icon = Country.get_icon_for_country(country_name)
    result_msg = BotMessage.TEMPLATE_FOR_USER_COURCES.format(country_icon, country_name, country_icon)

    pz = pytz.timezone('Europe/Minsk')
    current_time = datetime.now(pz).strftime('%d.%m %H:%M')
    result_msg += BotMessage.TEMPLATE_FOR_TIME.format(current_time)
    for currency_item_name, currency_items in context_for_user.items():
        result_msg += BotMessage.TEMPLATE_FOR_CURRENCY_HEADER.format(currency_item_name)

        for currency_pay_type, currency_items_prices in currency_items.items():
            currency_item_rate = float(currency_items_prices[0])
            currency_item_tax = float(currency_items_prices[1])

            if currency_item_tax:
                real_tax = currency_item_tax * 100
                currency_item_rate = currency_item_rate * (currency_item_tax + 1)
                currency_item_rate = round(currency_item_rate, 4)

                result_msg += BotMessage.TEMPLATE_FOR_CURRENC_RATE_WITH_TAX.format(
                    currency_pay_type, str(currency_item_rate), str(real_tax)
                )

                count_for_currency = Currency.get_count_for_currency(currency_item_name)
                if count_for_currency > 1:
                    result_msg += BotMessage.COUNT_PRECISION.format(count_for_currency)

                result_msg += BotMessage.NEXT_LINE
                continue

            result_msg += BotMessage.TEMPLATE_FOR_CURRENCY_CLEAR_RATE.format(currency_pay_type, str(currency_item_rate))
            count_for_currency = Currency.get_count_for_currency(currency_item_name)
            if count_for_currency > 1:
                result_msg += BotMessage.COUNT_PRECISION.format(count_for_currency)

            result_msg += BotMessage.NEXT_LINE

    query_template = GET_INFO_FOR_EXCHANGE_FOR_USER_BY_COUNTRY.format(country_name)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
            query_result = cursor.fetchall()
    except Exception as e:
        pass

    text_for_append = list()

    for item in query_result:
        item = json.loads(item[0])

        currency_name = item.get(Const.CURRENCY_NAME)
        base_country_currency = item.get(Const.BASE_COUNTRY_NAME)
        exchange_operation = item.get(Const.EXCHANGE_OPERATION)
        current_rate = item.get(Const.CURRENT_RATE)
        last_update_date = item.get(Const.REFRESH_TIME)

        if not last_update_date:
            continue

        now_utc_timestamp = datetime.utcnow().timestamp()
        refresh_interval = now_utc_timestamp - datetime.fromisoformat(last_update_date).timestamp()

        if refresh_interval > EXPIRED_DATA_INTERVAL:
            continue

        if exchange_operation == Operation.BUY:
            text_msg = BotMessage.EXCHANGE_TEXT.format(currency_name, base_country_currency, current_rate)
        else:
            text_msg = BotMessage.EXCHANGE_TEXT.format(base_country_currency, currency_name, current_rate)
            text_msg += BotMessage.NEXT_LINE

        text_for_append.append(text_msg)

    if text_for_append:
        result_msg += BotMessage.EXCHANGE_RATES
        for text in text_for_append:
            result_msg += text

    set_activity_for_user(user_id)

    return result_msg


def set_activity_for_user(user_id):
    conn = get_connection_for_db()
    query_template = UPDATE_ACTIVITY_FOR_USER.format(user_id)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query_template)
    except Exception as e:
        pass


INSERT_DATA_IN_CURRENT_PRICE = """
    INSERT INTO current_price (
        country_full_name, 
        currency_name, 
        pay_type_name
    )
    VALUES ('{0}', '{1}', '{2}')
"""


INSERT_DATA_IN_CURRENT_EXCHANGE = """
    INSERT INTO current_exchange (
        country_full_name, 
        currency_name, 
        base_country_currency,
        exchange_operation
    )
    VALUES ('{0}', '{1}', '{2}', '{3}')
"""


UPDATA_DATA_IN_CURRENT_PRICE = """
    UPDATE current_price
    SET current_price='{0}', current_tax='{1}', last_update_date=datetime('now') 
    WHERE country_full_name='{2}' and currency_name='{3}' and pay_type_name='{4}'  
"""

UPDATE_DATA_IN_CURRENT_EXCHANGE = """
    UPDATE current_exchange
    SET current_rate='{0}', last_update_date=datetime('now')
    WHERE country_full_name='{1}' and currency_name='{2}' and exchange_operation='{3}'
"""


UPDATE_ACTIVITY_FOR_USER = """
    UPDATE users
    SET last_update_date=datetime('now') 
    WHERE message_chat_id='{0}'  
"""


CHECK_USER_IN_DB = """
    SELECT EXISTS (
        SELECT 1 FROM users where message_chat_id='{0}'
    )
"""


ADD_USER_IN_DB = """
    INSERT INTO users (
        message_chat_id, 
        first_name, 
        last_name,
        username,
        last_update_data
    )
    VALUES ('{0}', '{1}', '{2}', '{3}', datetime('now'))
"""


UPDATE_COUNTRY_FOR_USER_IN_DB = """
    UPDATE users
    SET country='{0}', last_update_data=datetime('now')
    WHERE message_chat_id='{1}'
"""

GET_INFO_FOR_USER_BY_COUNTRY = """
    SELECT json_object(
        'currency_name', currency_name,
        'pay_type_name', pay_type_name,
        'current_price', current_price,
        'current_tax', current_tax,
        'refresh_time', last_update_date 
    ) from current_price
    where country_full_name ='{0}'
    order by current_price, currency_name
"""


GET_INFO_FOR_EXCHANGE_FOR_USER_BY_COUNTRY = """
    SELECT json_object(
        'currency_name', currency_name,
        'base_country_currency', base_country_currency,
        'exchange_operation', exchange_operation,
        'current_rate', current_rate,
        'refresh_time', last_update_date
    ) from current_exchange
    where country_full_name ='{0}'
    order by currency_name, exchange_operation
"""
