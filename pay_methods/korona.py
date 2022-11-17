from copy import deepcopy
from const import Const

KORONA_URL = 'https://koronapay.com/transfers/online/api/transfers/tariffs'
KORONA_HEADERS = {
    "Accept": "*/*",
    "Host": "koronapay.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate, br",
    "Cookie": "ROUTEID=29f5eaf1148ee63a|Y3Trv"
}


class KoronaCurrencyId:
    RUB = 810
    USD = 840
    EUR = 978
    GEL = 981
    LIR = 949
    KZT = 398


class KoronaCountry:
    GEO = 'GEO'
    TUR = 'TUR'
    UZB = 'UZB'
    KAZ = 'KAZ'

    @classmethod
    def get_all_countries(cls):
        return [cls.GEO, cls.TUR, cls.UZB, cls.KAZ]


class KoronaCreadentials:
    PARAMS = {
        'receivingAmount': 10000,
        'alternatives': False,
        'sendingCurrencyId': 'RUB',
        'receivingCurrencyId': 'USD',
        'sendingCountryId': 'RUS',
        'receivingCountryId': 'GEO',
        'receivingMethod': 'cash',
        'paymentMethod': 'debitCard'
    }

    @classmethod
    def get_custom_params(cls, currency, country, default_amount=100000):
        """
        Создаем кастомные параметры для гет запроса к короне
        :param currency: Валюта которую хотим получить
        :param country: Страна куда отправляе
        :param default_amount: Количество для отправки
        :return: параметры для вставки в гет запрос
        """
        custom_params = cls.PARAMS
        custom_params[Const.RECEIVING_AMOUNT] = default_amount
        custom_params[Const.SENDING_CURRENCY_ID] = KoronaCurrencyId.RUB
        custom_params[Const.RECEIVING_CURRENCY_ID] = currency
        custom_params[Const.RECEIVING_COUNTRY_ID] = country

        return custom_params


def get_korona_currency_dependencies_by_country():
    """
    Все считаемые для короны пары переводов
    :return: словарь
    """
    return {
        KoronaCountry.GEO: [KoronaCurrencyId.GEL, KoronaCurrencyId.EUR, KoronaCurrencyId.USD],
        KoronaCountry.TUR: [KoronaCurrencyId.LIR, KoronaCurrencyId.EUR, KoronaCurrencyId.USD],
        KoronaCountry.UZB: [KoronaCurrencyId.USD],
        KoronaCountry.KAZ: [KoronaCurrencyId.KZT, KoronaCurrencyId.USD]
    }


def prepare_korona_params_from_currencies_list(country_currencies):
    """
    Подготовка данных для запроса в Золотую Корону
    :param country_currencies: список валют для отправки
    :return: массив параметров для запроса в ЗК
    """
    all_params_for_request = list()
    for country_name, currencies_list in country_currencies.items():
        for currency in currencies_list:
            param = deepcopy(KoronaCreadentials.get_custom_params(currency, country_name))
            all_params_for_request.append(param)

    return all_params_for_request
