import datetime
import http.client
import json
import config_singleton

config = config_singleton.ConfigSingleton.getInstance().get_config()


class CoinbaseAPI:
    def __init__(self):
        self.conn = http.client.HTTPSConnection("api.commerce.coinbase.com")
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-CC-Api-Key': config['coinbase_commerce_api_key'],
        }

    @staticmethod
    def get_time_left(target_time):
        target_datetime = datetime.datetime.strptime(target_time, "%Y-%m-%dT%H:%M:%SZ")
        current_datetime = datetime.datetime.utcnow()
        time_left = target_datetime - current_datetime

        # Extract days, hours, minutes, and seconds from the time difference
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return days, hours, minutes, seconds

    def create_charge(self, amount, currency, name, description):
        payload = {
            "name": name,
            "description": description,
            "local_price": {
                "amount": amount,
                "currency": currency,
            },
            "pricing_type": "fixed_price",
            "metadata": {
                "customer_id": "CUSTOMER_ID",
            },
            "redirect_url": "https://t.me/durability",
            "cancel_url": "https://t.me/durability",
        }

        self.conn.request("POST", "/charges", json.dumps(payload), self.headers)
        res = self.conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

    def get_charge(self, charge_id):
        endpoint = f"/charges/{charge_id}"
        self.conn.request("GET", endpoint, '', self.headers)
        res = self.conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

    def get_symbol_and_network_using_coin_name(self, coin):
        if coin == "polygon":
            return "PMATIC", "Polygon"
        elif coin == "ethereum":
            return "ETH", "Ethereum (ERC20)"
        elif coin == "bitcoin":
            return "BTC", "BTC"
        elif coin == "litecoin":
            return "LTC", "LTC"
        elif coin == "dogecoin":
            return "DOGE", "DOGE"
        elif coin == "bitcoincash":
            return "BCH", "BCH"
        elif coin == "usdc":
            return "USDC", "Ethereum (ERC20)"
        elif coin == "dai":
            return "DAI", "Ethereum (ERC20)"
        elif coin == "apecoin":
            return "APE", "Ethereum (ERC20)"
        elif coin == "shibainu":
            return "SHIB", "Ethereum (ERC20)"
        elif coin == "tether":
            return "USDT", "Ethereum (ERC20)"
        elif coin == "pusdc":
            return "PUSDC", "Polygon"
        elif coin == "pweth":
            return "PWETH", "Polygon"
        else:
            return None, None

    @staticmethod
    def keep_last_nonzero_decimals(number):
        # Convert the number to a string representation
        number_str = str(number)

        # Find the position of the decimal point
        decimal_pos = number_str.find('.')

        # If the decimal point is not found, return the original number
        if decimal_pos == -1:
            return number

        # Get the substring after the decimal point
        decimals_str = number_str[decimal_pos + 1:]

        # Remove trailing zeros from the decimals string
        trimmed_decimals_str = decimals_str.rstrip('0')

        # If all decimal digits are zeros, return the original number
        if trimmed_decimals_str == '':
            return number

        # Reconstruct the trimmed number by combining the integer part and the trimmed decimals
        trimmed_number_str = number_str[:decimal_pos + 1] + trimmed_decimals_str

        # Convert the trimmed number back to float and return it
        trimmed_number = float(trimmed_number_str)
        return trimmed_number


    def get_charge_details(self, charge_id, coin):
        charge = self.get_charge(charge_id)
        details = {}
        details["coin_name"] = coin.capitalize()
        details["address"] = charge["data"]["addresses"][coin]
        details["order_code"] = charge["data"]["code"]
        details["expires_at"] = 30
        details[
            'pricing'] = f"{self.keep_last_nonzero_decimals(charge['data']['pricing'][coin]['amount'])} {charge['data']['pricing'][coin]['currency']} (${int(float(charge['data']['pricing']['local']['amount']))})"
        details['symbol'], details['network'] = self.get_symbol_and_network_using_coin_name(coin)
        return details

    def list_charges(self):
        self.conn.request("GET", "/charges", '', self.headers)
        res = self.conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

    def check_if_payment_accepted(self, charge):
        payments = charge['payments']

        if payments == []:
            return {"result": False, "data": "User didn't send any coins"}
        status = charge['payments'][0]['status']
        amount_paid = float(charge['payments'][0]['value']['local']['amount'])

        if status == "CONFIRMED":
            return {"result": True, "amount": amount_paid}

        return {"result": False, "amount": "Not CONFIRMED yet"}

