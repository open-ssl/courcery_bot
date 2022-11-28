import json
from bs4 import BeautifulSoup
from const import Const
from time import sleep
from requests_futures import sessions
from pay_methods.korona import (
    KORONA_URL, KORONA_HEADERS,
    KoronaCountry,
    KoronaCurrencyId,
    get_korona_currency_dependencies_by_country,
    prepare_korona_params_from_currencies_list
)

from pay_methods.unistream import (
    UNISTREAM_URL,
    UNISTREAM_HEADERS,
    UnistreamCountry,
    UnistreamCurrency,
    prepare_unistream_params_from_currencies_list,
    get_unistream_currency_dependencies_by_country
)
from pay_methods.contact import (
    CONTACT_URL,
    CONTACT_HEADERS,
    CONTACT_COOKIES,
    ContactCountry,
    ContactAccountForCountry,
    prepare_contact_params_from_currencies_list,
    get_contact_currency_dependencies_by_country
)
from pay_methods.rico import (
    RICO_URL,
    RICO_HEADER,
    CALCULATOR_CURRENCY_CLASS,
    RicoCurrencyCalculatorObject,
    RicoCurrencyNames
)
import db_helpers

HTML_PARSER_TYPE = 'html.parser'
FORM_CLASS_NAME = 'form'
REFRESH_INTERVAL = 120
API_TOKEN = ''
BEARER_TOKEN = ''
SUPPORT_URL = 'https://t.me/Stanislav_Lukyanov'


def get_session_for_request():
    return sessions.FuturesSession()


def get_request(session, url, headers, params=None, verify=True):
    while True:
        try:
            request_result = session.get(url=url, params=params, headers=headers, verify=verify)
            break
        except Exception as e:
            print('Unknown error %s' % e)
            session = get_session_for_request()
            sleep(0.5)

    return request_result


def post_request(session, url, cookies, headers, json_data):
    while True:
        try:
            request_result = session.post(url=url, cookies=cookies, headers=headers, json=json_data)
            break
        except Exception as e:
            print('Unknown error %s' % e)
            session = get_session_for_request()
            sleep(0.5)

    return request_result


def get_completed_request(url, params, headers):
    session = get_session_for_request()

    while True:
        try:
            request_result = session.get(url=url, params=params, headers=headers)
            break
        except Exception as e:
            print('Unknown error %s' % e)
            session = get_session_for_request()
            sleep(0.5)

    return request_result.result()


def get_data_for_corona(all_params_for_request):
    """
    Делаем кучу запросов в ЗК на получение различной информации по валютам
    и возвращаем словарь данных для записи в БД
    :param all_params_for_request:
    :return: словарь сооветствия - страна массив с данными
    """
    futures_task = list()
    session = get_session_for_request()
    result_context = {country: [] for country in KoronaCountry.get_all_countries()}

    for single_params in all_params_for_request:
        try:
            request_result = get_request(session, KORONA_URL, params=single_params, headers=KORONA_HEADERS)
            futures_task.append((request_result, single_params.get(Const.RECEIVING_COUNTRY_ID)))
        except Exception as e:
            pass

    for futures_task, country in futures_task:
        try:
            result_text = futures_task.result()
            data_obj = json.loads(result_text.text)[0]
            receiving_currency = data_obj.get(Const.RECEIVING_CURRENCY).get(Const.CODE)
            actual_cource = data_obj.get(Const.EXCHANGE_RATE)
            actual_tax = data_obj.get(Const.EXCHANGE_RATE_DISCOUNT)

            result_context[country].append({receiving_currency: (actual_cource, actual_tax)})
        except Exception as e:
            pass

    return result_context


def get_data_for_unistream(all_params_for_request):
    """
    Делаем кучу запросов в ЗК на получение различной информации по валютам
    и возвращаем словарь данных для записи в БД
    :param all_params_for_request:
    :return: словарь сооветствия - страна массив с данными
    """
    futures_task = list()
    session = get_session_for_request()
    result_context = {country: [] for country in UnistreamCountry.get_all_countries()}

    for single_params in all_params_for_request:
        try:
            request_result = get_request(session, UNISTREAM_URL, params=single_params, headers=UNISTREAM_HEADERS)
            futures_task.append((request_result, single_params.get(Const.DESTINATION)))
        except Exception as e:
            pass

    for futures_task, country in futures_task:
        try:
            result_text = futures_task.result()
            data_obj = json.loads(result_text.text).get(Const.FEES)[0]
            receiving_currency = data_obj.get(Const.WITHDRAW_CURRENCY)
            actual_cource = data_obj.get(Const.ACCEPTED_AMOUNT)
            actual_tax = data_obj.get(Const.ACCEPTED_TOTAL_FEE)

            result_context[country].append({receiving_currency: (actual_cource, actual_tax)})
        except Exception as e:
            pass

    return result_context


def get_data_for_contact(all_params_for_request):
    """
    Делаем кучу запросов в Contact на получение различной информации по валютам
    и возвращаем словарь данных для записи в БД
    :param all_params_for_request:
    :return: словарь сооветствия - страна массив с данными
    """
    futures_task = list()
    session = get_session_for_request()
    result_context = {country: [] for country in ContactCountry.get_all_countries()}

    for single_params in all_params_for_request:
        try:
            request_result = post_request(
                session,
                url=CONTACT_URL,
                cookies=CONTACT_COOKIES,
                headers=CONTACT_HEADERS,
                json_data=single_params
            )
            account = single_params.get(Const.ACCOUNT)
            futures_task.append((request_result, ContactAccountForCountry.get_country_by_account(account)))
        except Exception as e:
            pass

    for futures_task, country in futures_task:
        try:
            result_text = futures_task.result()
            parsed_text = json.loads(result_text.text)
            request_account_name = json.loads(result_text.request.body).get(Const.ACCOUNT)
            currency_name = ContactAccountForCountry.get_currency_by_account(request_account_name)

            actual_cource = parsed_text.get(Const.ELEMENTS)[0].get(Const.VALUE)
            actual_tax = parsed_text.get(Const.TERMS).get(Const.COMMISSION).get(Const.RANGES)[0].get(Const.RATE)

            result_context[country].append({currency_name: (actual_cource, actual_tax)})
        except Exception as e:
            pass

    return result_context


def write_cources_for_korona():
    korona_country_currencies: dict[str: list] = get_korona_currency_dependencies_by_country()
    all_params_for_request = prepare_korona_params_from_currencies_list(korona_country_currencies)

    korona_data = get_data_for_corona(all_params_for_request)

    for country_short_name, currency_data in korona_data.items():
        for currency_obj in currency_data:
            currency_name = set(currency_obj.keys()).pop()
            currency_values = currency_obj[currency_name]

            current_price = currency_values[0]
            current_tax = currency_values[1]

            country_full_name = Country.get_full_name_by_short(country_short_name)

            currency_name = Currency.LIR if currency_name == 'TRY' else currency_name
            if currency_name == Currency.KZT:
                current_price = float(current_price) * Currency.get_count_for_currency(Currency.KZT)
                current_price = str(current_price)

            db_helpers.update_price_for_pay_type_in_db(
                current_price,
                current_tax,
                country_full_name,
                currency_name,
                PayType.KORONA_PAY
            )
    print("write prices for korona")


def write_cources_for_unistream():
    unistream_country_currencies: dict[str: list] = get_unistream_currency_dependencies_by_country()
    all_params_for_request = prepare_unistream_params_from_currencies_list(unistream_country_currencies)
    amount_for_currency_info = UnistreamCurrency.get_amount_for_currency()
    unistream_data = get_data_for_unistream(all_params_for_request)

    for country_short_name, currency_data in unistream_data.items():
        for currency_obj in currency_data:
            currency_name = set(currency_obj.keys()).pop()
            currency_values = currency_obj[currency_name]

            current_price = currency_values[0]
            current_tax = currency_values[1]

            if currency_name in UnistreamCurrency.get_names_for_count_price():
                count_for_request = amount_for_currency_info.get(currency_name)
                current_price = round(float(current_price) / count_for_request, 3)
                current_price = str(current_price)

            country_full_name = Country.get_full_name_by_short(country_short_name)

            db_helpers.update_price_for_pay_type_in_db(
                current_price,
                current_tax,
                country_full_name,
                currency_name,
                PayType.UNISTREAM
            )
    print("write prices for unistream")


def write_cources_for_contact():
    contact_country_currencies: dict[str: list] = get_contact_currency_dependencies_by_country()
    all_params_for_request = prepare_contact_params_from_currencies_list(contact_country_currencies)

    contact_data = get_data_for_contact(all_params_for_request)

    for country_short_name, currency_data in contact_data.items():
        for currency_obj in currency_data:
            currency_name = set(currency_obj.keys()).pop()
            currency_values = currency_obj[currency_name]

            current_price = currency_values[0]
            current_tax = currency_values[1]

            country_full_name = Country.get_full_name_by_short(country_short_name)

            db_helpers.update_price_for_pay_type_in_db(
                current_price,
                current_tax,
                country_full_name,
                currency_name,
                PayType.CONTACT
            )
    print("write prices for contact")


def write_cources_for_rico():
    rico_data = {}

    rico_currency_names = RicoCurrencyNames.all_currency_names()
    rico_currency_object = RicoCurrencyCalculatorObject()
    try:
        session = get_session_for_request()
        response = get_request(session, url=RICO_URL, headers=RICO_HEADER, verify=False)
        rico_calculator_object = BeautifulSoup(response.result().text, HTML_PARSER_TYPE) \
            .find(FORM_CLASS_NAME, class_=CALCULATOR_CURRENCY_CLASS)
        rico_attrs = rico_calculator_object.attrs

        for rico_currency_name in rico_currency_names:
            buy_attr = rico_currency_object.get_custom_buy_rate(rico_currency_name)
            sell_attr = rico_currency_object.get_custom_sell_rate(rico_currency_name)

            buy_value = rico_attrs.get(buy_attr)
            sell_value = rico_attrs.get(sell_attr)
            rico_data[f'{rico_currency_name}_{Operation.BUY}'.upper()] = buy_value
            rico_data[f'{rico_currency_name}_{Operation.SELL}'.upper()] = sell_value

    except Exception as e:
        pass

    for currency_operation, current_rate in rico_data.items():
        currency_name, exchange_operation = currency_operation.split('_')
        currency_name = Currency.RUB if currency_name == 'RUR' else currency_name
        db_helpers.update_exchange_cources_pay_type_in_db(
            current_rate,
            Country.GEO_NAME,
            currency_name,
            exchange_operation
        )

    print("write prices for rico")


def write_all_cources():
    while True:
        try:
            write_cources_for_korona()
            write_cources_for_unistream()
            write_cources_for_contact()
            write_cources_for_rico()

            print('refreshed all prices in db')
            sleep(REFRESH_INTERVAL)
        except Exception as e:
            pass


class Operation:
    BUY = 'BUY'
    SELL = 'SELL'

    @classmethod
    def get_operations(cls):
        return [cls.BUY, cls.SELL]


class Country:
    GEO = 'GEO'
    TUR = 'TUR'
    UZB = 'UZB'
    KAZ = 'KAZ'

    GEO_NAME = 'Грузия'
    TUR_NAME = 'Турция'
    UZB_NAME = 'Узбекистан'
    KAZ_NAME = 'Казахстан'

    @classmethod
    def get_country_data(cls):
        return [
            (cls.GEO, cls.GEO_NAME),
            (cls.TUR, cls.TUR_NAME),
            (cls.UZB, cls.UZB_NAME),
            (cls.KAZ, cls.KAZ_NAME)
        ]

    @classmethod
    def get_full_name_by_short(cls, country):
        return {
            cls.GEO: cls.GEO_NAME,
            cls.TUR: cls.TUR_NAME,
            cls.UZB: cls.UZB_NAME,
            cls.KAZ: cls.KAZ_NAME
        }.get(country)

    @classmethod
    def get_full_name_by_contact_account(cls, account):
        return {
            cls.GEO: cls.GEO_NAME,
            cls.TUR: cls.TUR_NAME,
            cls.UZB: cls.UZB_NAME,
            cls.KAZ: cls.KAZ_NAME
        }.get(account)

    @classmethod
    def get_base_currency_for_country(cls, country):
        return {
            cls.GEO: Currency.GEL,
            cls.TUR: Currency.LIR,
            cls.UZB: Currency.UZB,
            cls.KAZ: Currency.KZT
        }.get(country)

    @classmethod
    def get_icon_for_country(cls, country):
        return {
            cls.TUR_NAME: BotMessage.EMOJI_TURKEY,
            cls.GEO_NAME: BotMessage.EMOJI_GEORGIA,
            cls.UZB_NAME: BotMessage.EMOJI_UZBEKISTAN,
            cls.KAZ_NAME: BotMessage.EMOJI_KAZAHSTAN
        }.get(country)


class Currency:
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'
    GEL = 'GEL'
    KZT = 'KZT'

    LIR = 'LIR'
    TRY = 'TRY'

    UZS = 'UZS'
    UZB = 'UZB'

    @classmethod
    def get_currency_data(cls):
        return [
            cls.RUB, cls.USD, cls.EUR, cls.GEL, cls.LIR, cls.KZT
        ]

    @classmethod
    def get_name_by_korona_id(cls, currency_id):
        return {
            KoronaCurrencyId.RUB_ID: cls.RUB,
            KoronaCurrencyId.USD_ID: cls.USD,
            KoronaCurrencyId.EUR_ID: cls.EUR,
            KoronaCurrencyId.GEL_ID: cls.GEL,
            KoronaCurrencyId.LIR_ID: cls.LIR,
            KoronaCurrencyId.KZT_ID: cls.KZT
        }.get(currency_id)

    @classmethod
    def get_count_for_currency(cls, currency):
        return {
            cls.RUB: 1,
            cls.USD: 1,
            cls.EUR: 1,
            cls.GEL: 1,
            cls.LIR: 1,
            cls.TRY: 1,
            cls.UZS: 100000,
            cls.KZT: 10000
        }.get(currency)


class PayType:
    KORONA_PAY = 'Korona Pay'
    UNISTREAM = 'Unistream'
    CONTACT = 'Contact'
    RICO = 'Rico'

    @classmethod
    def get_pay_types(cls):
        return [
            cls.KORONA_PAY, cls.UNISTREAM, cls.CONTACT, cls.RICO
        ]


class BotCommand:
    MAIN_MENU = 'main_menu'
    CHOICE_COUNTRY = 'choice_country'
    HELP_PROJECT = 'help_project'
    WRITE_DEVELOPER = 'write_developer'
    GEORGIA_COUNTRY = 'GEORGIA_COUNTRY'
    TURKEY_COUNTRY = 'TURKEY_COUNTRY'
    KAZAHSTAN_COUNTRY = 'KAZAHSTAN_COUNTRY'
    UZBEKISTAN_COUNTRY = 'UZBEKISTAN_COUNTRY'

    @classmethod
    def get_country_commands(cls):
        return [
            cls.GEORGIA_COUNTRY, cls.TURKEY_COUNTRY,
            cls.KAZAHSTAN_COUNTRY, cls.UZBEKISTAN_COUNTRY
        ]

    @classmethod
    def get_main_menu_commands(cls):
        return {
            cls.CHOICE_COUNTRY: BotMessage.CHOICE_COUNTRY,
            cls.HELP_PROJECT: BotMessage.HELP_PROJECT,
            cls.WRITE_DEVELOPER: BotMessage.WRITE_DEVELOPER,
        }

    @classmethod
    def get_commands_for_countries(cls):
        return {
            cls.GEORGIA_COUNTRY: BotMessage.GEORGIA_COUNTRY,
            cls.TURKEY_COUNTRY: BotMessage.TURKEY_COUNTRY,
            cls.KAZAHSTAN_COUNTRY: BotMessage.KAZAHSTAN_COUNTRY,
            cls.UZBEKISTAN_COUNTRY: BotMessage.UZBEKISTAN_COUNTRY
        }

    @classmethod
    def get_country_by_command(cls, command):
        return {
            cls.GEORGIA_COUNTRY: Country.GEO_NAME,
            cls.TURKEY_COUNTRY: Country.TUR_NAME,
            cls.KAZAHSTAN_COUNTRY: Country.KAZ_NAME,
            cls.UZBEKISTAN_COUNTRY: Country.UZB_NAME
        }.get(command)


class BotMessage:
    """ Сообщения от бота """

    EMOJI_COUNTRY = '🌍'
    EMOJI_HELP = '⛏'
    EMOJI_WRITE = '✍️'
    EMOJI_TOP = '🔝'
    EMOJI_REFRESH = '🔄'
    EMOJI_GEORGIA = '🇬🇪'
    EMOJI_TURKEY = '🇹🇷'
    EMOJI_KAZAHSTAN = '🇰🇿'
    EMOJI_UZBEKISTAN = '🇺🇿'

    START_BOT_NESSAGE = '<b>Courcery</b> - Ваш <b>бот-помощник</b> для перевода денег из России в другие страны!\n' \
                        'Больше не нужно вручную следить за разницей курсов для разных систем переводов, <b>бот сделает это за тебя!</b>'
    CHOICE_COUNTRY_FOR_COURCE = 'Выберите страну для отслеживания актуального курса'
    #########################################################################################################
    CHOICE_COUNTRY = EMOJI_COUNTRY + 'Выберите страну' + EMOJI_COUNTRY
    HELP_PROJECT = EMOJI_HELP + 'Помочь боту' + EMOJI_HELP
    WRITE_DEVELOPER = EMOJI_WRITE + 'Написать автору' + EMOJI_WRITE
    MAIN_MENU = EMOJI_TOP + 'Главное меню' + EMOJI_TOP
    REFRESH_COURCE = EMOJI_REFRESH + 'Обновить курс' + EMOJI_REFRESH
    HELP_PROJECT_TEXT = 'Каждый может помочь <b>CourceryBot</b> стать лучше!\n\nЕсли Вы не обнаружили вашу страну, вы можете написать автору, приложив информацию о используемых платежных системах и обменниках в этой стране!\n\nЕсли вы хотите поблагодарить автора, вы можете отправить любую сумму на криптокошелек - <b>0x70f41e569Fa320cc8c177859C4a218a741E1f064</b>\nЭти деньги пойдут на оплату хостинга для бота.'
    WRITE_DEVELOPER_TEXT = 'Текст в написать автору'
    GEORGIA_COUNTRY = EMOJI_GEORGIA + ' Грузия ' + EMOJI_GEORGIA
    TURKEY_COUNTRY = EMOJI_TURKEY + ' Турция ' + EMOJI_TURKEY
    KAZAHSTAN_COUNTRY = EMOJI_KAZAHSTAN + ' Казахстан ' + EMOJI_KAZAHSTAN
    UZBEKISTAN_COUNTRY = EMOJI_UZBEKISTAN + ' Узбекистан ' + EMOJI_UZBEKISTAN
    #########################################################################################################
    TEMPLATE_FOR_USER_COURCES = 'Актуальные курсы для страны - <b>{}{}{}</b>\n'
    TEMPLATE_FOR_TIME = 'Найдено для Вас <b><u>{}</u></b> по Московскому времени\n'
    TEMPLATE_FOR_CURRENCY_HEADER = '\nПереводим 💳<b>RUB</b> ➙ <b>{}</b>💳:\n'
    TEMPLATE_FOR_CURRENCY_CLEAR_RATE = '{} - <b>{}</b>'
    TEMPLATE_FOR_CURRENC_RATE_WITH_TAX = '{} - <b>{}</b> с учетом комиссии {}%'
    COUNT_PRECISION = ' за {}'
    NEXT_LINE = '\n'
    EXCHANGE_RATES = '\nКурсы обмена валют:\n'
    EXCHANGE_TEXT = '{} 🔄 {} - <b>{}</b>💰\n'
