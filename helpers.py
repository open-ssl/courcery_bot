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
API_TOKEN = ''
BEARER_TOKEN = ''


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

    unistream_data = get_data_for_unistream(all_params_for_request)

    for country_short_name, currency_data in unistream_data.items():
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
                PayType.UNISTREAM
            )
    print("write prices for korona")


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

    return rico_data


class Operation:
    BUY = 'BUY'
    SELL = 'SELL'


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


class Currency:
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'
    GEL = 'GEL'
    LIR = 'LIR'
    KZT = 'KZT'

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


class BotMessage:
    """ Сообщения от бота """
    START_BOT_NESSAGE = '<b>Courcery</b> - Ваш <b>бот-помощник</b> для перевода денег из России в другие страны!\n' \
                        'Больше не нужно вручную следить за разницей курсов для разных систем переводов, <b>бот сделает это за тебя!</b>'
