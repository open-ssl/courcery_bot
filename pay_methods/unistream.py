from copy import deepcopy
from const import Const

UNISTREAM_URL = 'https://online.unistream.ru/card2cash/calculate'
UNISTREAM_HEADERS = {
    "Accept": "*/*",
    "Host": "online.unistream.ru",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate, br",
    "Cookie": "PHPSESSID=q27iiktu4p123b2t30mpfsd4ds; __lhash_=6b1b7fa9075825b7470dfaef6b640a10"
}


class UnistreamCurrency:
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'
    GEL = 'GEL'
    TRY = 'TRY'
    UZS = 'UZS'
    KZT = 'KZT'

    @classmethod
    def get_amount_for_currency(cls):
        return {
            cls.RUB: 1,
            cls.USD: 1000,
            cls.EUR: 1000,
            cls.GEL: 1000,
            cls.TRY: 1000,
            cls.UZS: 100000,
            cls.KZT: 10000
        }


    @classmethod
    def get_names_for_count_price(cls):
        return [cls.GEL, cls.TRY, cls.USD, cls.EUR]


class UnistreamCountry:
    GEO = 'GEO'
    TUR = 'TUR'
    UZB = 'UZB'
    KAZ = 'KAZ'

    @classmethod
    def get_all_countries(cls):
        return [cls.GEO, cls.TUR, cls.UZB, cls.KAZ]


class UnistreamCredentials:
    PARAMS = {
        'destination': 'GEO',
        'amount': 1,
        'currency': 'USD',
        'accepted_currency': 'RUB',
        'profile': 'unistream'
    }

    @classmethod
    def get_custom_params(cls, currency, country, amount=1):
        """
        Создаем кастомные параметры для гет запроса к короне
        :param currency: Валюта которую хотим получить
        :param country: Страна куда отправляем
        :param amount: Количество валюты для посчета курса
        :return: параметры для вставки в гет запрос
        """
        custom_params = cls.PARAMS

        custom_params[Const.CURRENCY] = currency
        custom_params[Const.AMOUNT] = amount
        custom_params[Const.DESTINATION] = country

        return custom_params


def get_unistream_currency_dependencies_by_country():
    """
    Все считаемые для юнистрима пары переводов
    :return: словарь
    """
    return {
        UnistreamCountry.GEO: [UnistreamCurrency.GEL, UnistreamCurrency.EUR, UnistreamCurrency.USD],
        UnistreamCountry.TUR: [UnistreamCurrency.TRY, UnistreamCurrency.EUR, UnistreamCurrency.USD],
        UnistreamCountry.UZB: [UnistreamCurrency.USD, UnistreamCurrency.EUR, UnistreamCurrency.UZS],
        UnistreamCountry.KAZ: [UnistreamCurrency.KZT, UnistreamCurrency.USD]
    }


def prepare_unistream_params_from_currencies_list(country_currencies):
    """
    Подготовка данных для запроса в Юнистрим
    :param country_currencies: список валют для отправки
    :return: массив параметров для запроса в Юнистрим
    """
    all_params_for_request = list()
    amount_for_currency_info = UnistreamCurrency.get_amount_for_currency()

    for country_name, currencies_list in country_currencies.items():
        for currency in currencies_list:
            amount = amount_for_currency_info.get(currency)
            param = deepcopy(UnistreamCredentials.get_custom_params(currency, country_name, amount))
            all_params_for_request.append(param)

    return all_params_for_request
