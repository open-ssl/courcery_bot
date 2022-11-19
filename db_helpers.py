import sqlite3
from pay_methods.korona import get_korona_currency_dependencies_by_country
from pay_methods.unistream import get_unistream_currency_dependencies_by_country
from pay_methods.contact import get_contact_currency_dependencies_by_country, ContactAccountForCountry

from helpers import Country, Currency, PayType


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


INSERT_DATA_IN_CURRENT_PRICE = """
    INSERT INTO current_price (
        country_full_name, 
        currency_name, 
        pay_type_name
    )
    VALUES ('{0}', '{1}', '{2}')
"""