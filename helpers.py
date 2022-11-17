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
        request_result = get_request(session, KORONA_URL, params=single_params, headers=KORONA_HEADERS)
        futures_task.append((request_result, single_params.get(Const.RECEIVING_COUNTRY_ID)))

    for futures_task, country in futures_task:
        result_text = futures_task.result()
        data_obj = json.loads(result_text.text)[0]
        receiving_currency = data_obj.get(Const.RECEIVING_CURRENCY).get(Const.CODE)
        actual_cource = data_obj.get(Const.EXCHANGE_RATE)

        result_context[country].append({receiving_currency: actual_cource})

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
        request_result = get_request(session, UNISTREAM_URL, params=single_params, headers=UNISTREAM_HEADERS)
        futures_task.append((request_result, single_params.get(Const.DESTINATION)))

    for futures_task, country in futures_task:
        result_text = futures_task.result()
        data_obj = json.loads(result_text.text).get(Const.FEES)[0]
        receiving_currency = data_obj.get(Const.WITHDRAW_CURRENCY)
        actual_cource = data_obj.get(Const.ACCEPTED_AMOUNT)

        result_context[country].append({receiving_currency: actual_cource})

    return result_context


def write_cources_for_korona():
    korona_country_currencies: dict[str: list] = get_korona_currency_dependencies_by_country()
    all_params_for_request = prepare_korona_params_from_currencies_list(korona_country_currencies)

    korona_data = get_data_for_corona(all_params_for_request)
    # теперь можно писать в базу

    return None


def write_cources_for_unistream():
    unistream_country_currencies: dict[str: list] = get_unistream_currency_dependencies_by_country()
    all_params_for_request = prepare_unistream_params_from_currencies_list(unistream_country_currencies)

    unistream_data = get_data_for_unistream(all_params_for_request)

    return None


class BotMessage:
    """ Сообщения от бота """
    START_BOT_NESSAGE = '<b>Courcery</b> - Ваш <b>бот-помощник</b> для перевода денег из России в другие страны!\n' \
                        'Больше не нужно вручную следить за разницей курсов для разных систем переводов, <b>бот сделает это за тебя!</b>'


