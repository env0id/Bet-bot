import requests


class BinanceAPI:
    BASE_URL = 'https://api.binance.com/api/v3'

    @staticmethod
    def get_price(symbol):
        endpoint = f'{BinanceAPI.BASE_URL}/ticker/price'
        params = {'symbol': symbol.upper()+"USDT"}
        response = requests.get(endpoint, params=params)
        return response.json()['price']

    @staticmethod
    def convert_to_crypto(dollar_amount, crypto_price):
        crypto_amount = float(dollar_amount) / float(crypto_price)
        return crypto_amount.__round__(8)

    @staticmethod
    def convert_to_dollars(coins_amount, crypto_price):
        crypto_amount = float(coins_amount) * float(crypto_price)
        return crypto_amount.__round__(2)
