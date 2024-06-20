class Coins:
    def __init__(self):
        self.coins = [
            {"symbol": "BTC", "name": "bitcoin"},
            {"symbol": "ETH", "name": "ethereum"},
            {"symbol": "USDT", "name": "tether"},
            {"symbol": "LTC", "name": "litecoin"},
            {"symbol": "DOGE", "name": "dogecoin"},
            {"symbol": "BCH", "name": "bitcoincash"},
            {"symbol": "SHIB", "name": "shibainu"}
        ]

    @staticmethod
    def get_symbol_and_network_using_coin_name(self, coin):
        if coin == "polygon":
            return "PMATIC", "Polygon"
        elif coin == "ethereum":
            return "ETH", "Ethereum \\(ERC20\\)"
        elif coin == "bitcoin":
            return "BTC", "BTC"
        elif coin == "litecoin":
            return "LTC", "LTC"
        elif coin == "dogecoin":
            return "DOGE", "DOGE"
        elif coin == "bitcoincash":
            return "BCH", "BCH"
        elif coin == "usdc":
            return "USDC", "Ethereum \\(ERC20\\)"
        elif coin == "dai":
            return "DAI", "Ethereum \\(ERC20\\)"
        elif coin == "apecoin":
            return "APE", "Ethereum \\(ERC20\\)"
        elif coin == "shibainu":
            return "SHIB", "Ethereum (ERC20)"
        elif coin == "tether":
            return "USDT", "Ethereum \\(ERC20\\)"
        elif coin == "pusdc":
            return "PUSDC", "Polygon"
        elif coin == "pweth":
            return "PWETH", "Polygon"
        else:
            return None, None
