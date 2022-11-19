RICO_URL = 'https://www.rico.ge/ru'

RICO_HEADER = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,nb;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Referer': 'https://www.google.com/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

CALCULATOR_CURRENCY_CLASS = 'js-currency-calculator'


class RicoCurrencyNames:
    USD = 'usd'
    EUR = 'eur'
    RUR = 'rur'

    @classmethod
    def all_currency_names(cls):
        return [cls.USD, cls.EUR, cls.RUR]


class RicoCurrencyCalculatorObject:
    BUY_RATE_ATTR = 'data-currency-calculator-buy-rate-'
    SELL_RATE_ATTR = 'data-currency-calculator-sell-rate-'

    def get_custom_buy_rate(self, attr):
        return f'{self.BUY_RATE_ATTR}{attr}'

    def get_custom_sell_rate(self, attr):
        return f'{self.SELL_RATE_ATTR}{attr}'
