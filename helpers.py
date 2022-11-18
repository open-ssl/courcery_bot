import json
from const import Const
from time import sleep
from requests_futures import sessions
from pay_methods.korona import (
    KORONA_URL, KORONA_HEADERS,
    KoronaCountry,
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
API_TOKEN = ''


def get_session_for_request():
    return sessions.FuturesSession()


def get_request(session, url, params, headers):
    while True:
        try:
            request_result = session.get(url=url, params=params, headers=headers)
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
    # теперь можно писать в базу

    return korona_data


def write_cources_for_unistream():
    unistream_country_currencies: dict[str: list] = get_unistream_currency_dependencies_by_country()
    all_params_for_request = prepare_unistream_params_from_currencies_list(unistream_country_currencies)

    unistream_data = get_data_for_unistream(all_params_for_request)

    return unistream_data


def write_cources_for_contact():
    contact_country_currencies: dict[str: list] = get_contact_currency_dependencies_by_country()
    all_params_for_request = prepare_contact_params_from_currencies_list(contact_country_currencies)

    contact_data = get_data_for_contact(all_params_for_request)

    return contact_data


class BotMessage:
    """ Сообщения от бота """
    START_BOT_NESSAGE = '<b>Courcery</b> - Ваш <b>бот-помощник</b> для перевода денег из России в другие страны!\n' \
                        'Больше не нужно вручную следить за разницей курсов для разных систем переводов, <b>бот сделает это за тебя!</b>'
