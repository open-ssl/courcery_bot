from copy import deepcopy
from const import Const

CONTACT_URL = 'https://edge.qiwi.com/sinap/api/refs/c8a305b5-3c36-4060-a1f4-553504d0dba7/containers'
CONTACT_HEADERS = {
    'authority': 'edge.qiwi.com',
    'accept': 'application/vnd.qiwi.v1+json',
    'accept-language': 'ru',
    'authorization': 'Bearer ',
    'client-software': 'WEB v4.126.0',
    'dnt': '1',
    'origin': 'https://qiwi.com',
    'referer': 'https://qiwi.com/',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'x-application-id': '0ec0da91-65ee-496b-86d7-c07afc987007',
    'x-application-secret': '66f8109f-d6df-49c6-ade9-5692a0b6d0a1',
}
CONTACT_COOKIES = {
    'spa_upstream': '04a06381f58c86ebf1357fb6e24b0ad3',
    'token-tail': 'de3f84bb3db8d25b',
    'token-tail-web-qw': '76d08bdfb69e7e5f',
    'auth_ukafokfuabbuzdckyiwlunsh': 'MDExfF98X3x/M3JiKVN/eHxEMF4lZVEKXwtbUnxOQ0t4XVlXBmYEeERaeWxIfAFVd35DVlEFUnFAFFJcBQFwLFR5YEt2YQRVcTBvaXgBf2EyETFcdnFVWl1SRgphSEBQdlxcV1JiBg==',
}

USD_NAME = 'USD'


class ContactCountry:
    GEO = 'GEO'
    TUR = 'TUR'
    UZB = 'UZB'
    KAZ = 'KAZ'

    @classmethod
    def get_all_countries(cls):
        return [cls.GEO, cls.TUR, cls.UZB, cls.KAZ]


class ContactAccountForCountry:
    GEO = 'CFRN'
    TUR = 'GXXU'
    UZB = 'ATOV'
    KAZ = 'AUEJ'

    @classmethod
    def get_country_by_account(cls, account):
        return {
            cls.GEO: ContactCountry.GEO,
            cls.TUR: ContactCountry.TUR,
            cls.UZB: ContactCountry.UZB,
            cls.KAZ: ContactCountry.KAZ
        }.get(account)

    @classmethod
    def get_currency_by_account(cls, account):
        return {
            cls.GEO: USD_NAME,
            cls.TUR: USD_NAME,
            cls.UZB: USD_NAME,
            cls.KAZ: USD_NAME
        }.get(account)


def get_contact_currency_dependencies_by_country():
    """
    Все считаемые для контакта пары переводов
    :return: словарь
    """
    return {
        ContactCountry.GEO: ContactAccountForCountry.GEO,
        ContactCountry.TUR: ContactAccountForCountry.TUR,
        ContactCountry.UZB: ContactAccountForCountry.UZB,
        ContactCountry.KAZ: ContactAccountForCountry.KAZ
    }


def prepare_contact_params_from_currencies_list(country_currencies):
    """
    Подготовка данных для запроса в Контакт
    :param country_currencies: список валют для отправки
    :return: массив параметров для запроса в Юнистрим
    """
    all_params_for_request = list()
    for country_name, currency_account_name in country_currencies.items():
        param = deepcopy(ContactJsonData.get_custom_contact_json_data(currency_account_name))
        all_params_for_request.append(param)

    return all_params_for_request


class ContactJsonData:
    CONTACT_JSON_DATA = {
        'providerGroupId': '26580',
        'account': 'CFRN',
        'rec_amount': '10000',
        'rec_currcode': '840',
    }

    @classmethod
    def get_custom_contact_json_data(cls, account):
        custom_json_data = cls.CONTACT_JSON_DATA
        custom_json_data[Const.ACCOUNT] = account
        return custom_json_data


class ContactCreads:
    CONTACT_API_ACCESS_TOKEN = ''
    PROVIDER_FROUP_ID = '26580'
    REC_AMOUNT = '1000'
    CURRENCY_CODE = '840'
