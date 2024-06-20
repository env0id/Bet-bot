import time

import requests
from blockcypher import get_wallet_addresses
from blockcypher import list_wallet_names
from blockcypher import create_unsigned_tx
from blockcypher import simple_spend
from blockcypher import remove_address_from_wallet

import Binance
import Constants
from blockcypher import get_transaction_details
from pprint import pprint

import config_singleton
from DBSingleton import DBSingleton

configuration = config_singleton.ConfigSingleton.getInstance().get_config()
db_ = DBSingleton.getInstance().get_db()


class Wallet:
    def __init__(self, id_, symbol, config, db):
        self.db = db
        self.id = id_
        self.api_key = config['blockcypher_api_key']
        self.config = config
        self.coin = symbol

        self._private_key = self._get_private_key()
        self.wallet_address = self.get_wallet_address()


    def _get_private_key(self):
        response = self.db.read_data([f'Wallets/{self.coin}'])
        if response is not None:
            return response['private_key']

    def get_wallet_address(self):
        wallet_address = get_wallet_addresses(wallet_name=self.id, api_key=self.api_key, coin_symbol=self.coin)
        if 'error' in wallet_address and wallet_address['error'] == 'Wallet not found':
            self._create_wallet()
        else:
            wallet_address = wallet_address['addresses'][0]
        return wallet_address

    def _create_wallet(self):
        # Generate a new address
        print(f'Creating new account:{self.id}')
        url = f"https://api.blockcypher.com/v1/{self.coin}/main/addrs?token={self.api_key}"
        response = requests.post(url)
        if response.status_code == 201:
            self.wallet_address = response.json()["address"]
            private_key = response.json()["private"]
            self._private_key = private_key
            self.db.write_data([f'Wallets/{self.coin}', {"private_key": private_key}])

        else:
            return False

        # Create the wallet with the generated address
        url = f"https://api.blockcypher.com/v1/{self.coin}/main/wallets?token={self.api_key}"
        data = {
            "name": self.id,
            "addresses": [self.wallet_address]
        }
        response = requests.post(url, json=data)
        return True

    def send_transaction(self, recipient_address, amount):
        if not self.wallet_address:
            return False
        resp = simple_spend(api_key=self.api_key, from_privkey=self._private_key,
                            to_address=recipient_address, to_satoshis=int(amount),
                            coin_symbol=self.coin, min_confirmations=20)
        return resp

    def get_balance(self):
        url = f"https://api.blockcypher.com/v1/{self.coin}/main/addrs/{self.wallet_address}/balance"
        response = requests.get(url)
        pprint(response.json())
        return self._satoshi_to_coin(response.json()["balance"])

    def get_balance_in_dollars(self):
        return Binance.BinanceAPI.convert_to_dollars(self.get_balance(),Binance.BinanceAPI.get_price(self.coin))

    def get_address(self):
        return self.wallet_address

    def _satoshi_to_coin(self, satoshi):
        coin = satoshi / 100000000
        return coin

    def coin_to_satoshi(self, coin):
        satoshi = coin * 100000000
        return satoshi

    def get_trans_details(self, trans_hash):
        res = get_transaction_details(trans_hash, coin_symbol=self.coin, api_key=self.api_key)
        return res['confirmations'] > Constants.Constants.Confirmations

