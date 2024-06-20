from DBSingleton import DBSingleton
from Event import Event
from pprint import pprint

from Wallet import Wallet


class AdminPanel:
    def __init__(self, config, bot):
        self.config = config
        self.bot = bot
        self.db = DBSingleton.getInstance().get_db()
        self.wallets = {"btc_wallet": Wallet("btc_wallet", "btc", config, self.db),
                        "ltc_wallet": Wallet("ltc_wallet", "ltc", config, self.db),
                        "doge_wallet": Wallet("doge_wallet", "doge", config, self.db)}

    def open_admin_panel(self, chat_id):
        if chat_id not in self.config['admin_ids']:
            return False

        msg = "<b>Withdrawal Wallets</b>\n\n"
        for wallet in self.wallets.values():
            msg += f"<b>{wallet.coin.upper()}</b>\n" + "<b>Balance:</b> " +"$"+ str(
                wallet.get_balance_in_dollars()) + "\n<b>Address:</b> <code>" + wallet.wallet_address + '</code>\n\n'

        self.bot.send_message(chat_id, msg)
