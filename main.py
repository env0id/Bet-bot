import inspect
import json
import threading
import time
from pprint import pprint
from datetime import datetime, timedelta
import re

import Binance
from EventsManager import EventsManager

import FireBase
import TgMethods
import config_singleton
from AdminPanel import AdminPanel
from CoinbaseAPI import CoinbaseAPI
from Constants import Constants
from DBSingleton import DBSingleton
from DepositRequest import DepositRequest
from LiquidityPool import LiquidityPool
from Untils.DataFilters import *
from User import User
#from translate import Translator
import urllib.parse
from Coins import Coins
from UsersManager import UsersManager
from Wallet import Wallet
from Withdrawal import Withdrawal

withdrawal_waiting_for_approve = {}
address_changes_msg_id = {}
config = config_singleton.ConfigSingleton.getInstance().get_config()
bot = TgMethods.BotHandler(config["api_key"])
users_manager = UsersManager()
admin_panel = AdminPanel(config, bot)
db = DBSingleton.getInstance().get_db()
liquidity_pool = LiquidityPool(db, users_manager, bot)
event_manager = EventsManager(config, bot, users_manager, liquidity_pool)
referred_users = []

paywall = CoinbaseAPI()
active_deposits = {}
test = False


def text_language_filer(text, user_id):
    return text
    # user = users_manager.get_user(user_id)
    # if user.get_language() is None or user.get_language() == 'en':
    #     return text
    # translator = Translator(to_lang=user.get_language(), from_lang='en')
    # translated = translator.translate(text)
    # return translated


def get_fee(amount, percents, user):
    fee = amount * (percents / 100)

    if user.get_fee_credit() > 0:
        if fee <= user.get_fee_credit():
            user.set_fee_credit(user.get_fee_credit() - fee)
            fee = 0
        else:
            fee -= user.get_fee_credit()
            user.set_fee_credit(0)
    return fee


def check_for_status_change():
    if test:
        round_time = 30
    else:
        round_time = 60 * 5
    while True:
        try:
            print("Check for updates")
            charges = paywall.list_charges()
            for charge in charges['data']:
                cid = charge['id']
                for active_deposits_user_lst in active_deposits.values():
                    for deposit_request in active_deposits_user_lst:
                        if str(cid) == str(deposit_request.order_id):
                            result = paywall.check_if_payment_accepted(charge)
                            print(result)

                            if (result['result'] or test) and not deposit_request.completed:
                                user = users_manager.get_user(deposit_request.user_id)
                                deposit_fee = get_fee(result['amount'], config[f'deposit_fee'], user)

                                user.set_balance(
                                    user.get_balance() + result['amount'] - deposit_fee)
                                msg = f"✅ Deposit received: ${round(result['amount'] - deposit_fee, 2)}"
                                bot.send_message(deposit_request.user_id,
                                                 text_language_filer(msg, deposit_request.user_id))
                                active_deposits.get(user.user_id).remove(deposit_request)
                            # deposit_request.completed = True # might be nee

            time.sleep(round_time)
        except Exception as e:
            print(e)


def generate_qr_code_url(crypto_address):
    base_url = "https://api.qrserver.com/v1/create-qr-code/"
    query_params = {
        "data": crypto_address,
        "size": "200x200",  # Adjust the size as per your requirement
        "ecc": "M",  # Error correction level (M: medium, Q: quartile, H: high)
    }
    encoded_params = urllib.parse.urlencode(query_params)
    qr_code_url = f"{base_url}?{encoded_params}"
    return qr_code_url


def handle_deposit_payment_chosen(chat_id, msg_id, data):
    bot.edit_message(chat_id, msg_id, text_language_filer("⏳ Loading ..", chat_id))
    try:
        sub_request = active_deposits[f"{chat_id}"][-1]
        details = paywall.get_charge_details(sub_request.order_id, data[0])
        pprint(details)

        msg = f"💳 {text_language_filer('Deposit with', chat_id)} <b>{details['coin_name']}</b>\n\n{text_language_filer('Use the address below to deposit', chat_id)}\n\n⚠️ Network: <b>{details['network']}</b>."
        msg += '\n\n<code>' + str(details['address']) + '</code>'
        msg += f"\n\n{text_language_filer('This address will be automatically cancelled in', chat_id)} <b>{details['expires_at']}</b> {text_language_filer('minutes if no payment is received', chat_id)}."
        msg += f" Please note that a deposit fee of <b>{config['deposit_fee']}%</b> will be deducted from the total amount,\n<i>if you have referral credit, it will be used.</i>"
        address = str(details['address'])
        qr_code = generate_qr_code_url(address)
        button = {"resize_keyboard": True,
                  "inline_keyboard": [[{"text": "Close", 'callback_data': "close_payment_window"}]]}
        x = bot.send_photo(chat_id, qr_code, caption=msg, button=button)
        print(x.json())
        bot.delete_message(chat_id, msg_id)
    except Exception:
        bot.edit_message(chat_id, msg_id, '❌ ' + text_language_filer("Error, please try again", chat_id))


def handle_deposit(chat_id, msg_id):
    charge = paywall.create_charge(config['max_deposit'], "USD", f"new deposit", f"User: {chat_id}")
    if str(chat_id) in active_deposits:
        active_deposits[f'{chat_id}'].append(DepositRequest(chat_id, charge['data']['id'], time.time()))
    else:
        active_deposits[f'{chat_id}'] = [DepositRequest(chat_id, charge['data']['id'], time.time())]

    coins = Coins().coins
    msg = "💱 Select a coin for deposit"
    button = {
        "resize_keyboard": True,
        "inline_keyboard": []
    }

    for i, coin in enumerate(coins):
        if i % 2 == 0:
            button["inline_keyboard"].append([])
        button["inline_keyboard"][i // 2].append(
            {"text": coin["symbol"], "callback_data": f"deposit_payment_chosen${coin['name']}"})

    button['inline_keyboard'].append([{"text": Constants.back_button, 'callback_data': "open_wallet"}])

    bot.edit_message(chat_id, msg_id, msg, button)


def private_keyboard(user_id, message_id):
    keyboard = {"resize_keyboard": True, 'one_time_keyboard': False,
                "keyboard": [[{"text": "💡 About"}, {"text": "📺 Events"}],
                             [{"text": "🛎 Support"}, {"text": "💼 Wallet"}]]}
    keyboard = json.dumps(keyboard)
    bot.open_keyboard(user_id, 'General Menu', keyboard)
    bot.delete_message(user_id, message_id)


def open_wallet(current_update, from_back=False):
    button = {
        "inline_keyboard": [[{"text": "📤 Withdrawal", 'callback_data': "withdrawal_coins"},
                             {"text": "📥 Deposit", 'callback_data': "deposit_coins"}],
                            [{"text": "👥 Referral", 'callback_data': "referral"}]]}
    if from_back:
        user_id, msg_id, data = get_variables(current_update)
    else:
        user_id = current_update['message']['from']['id']

    user = users_manager.get_user(user_id)

    msg = f'💰 Total Balance \n\n' + "<b>$" + str(user.get_balance()) + "</b>"

    if from_back:
        bot.edit_message(user_id, msg_id, msg, button)
    else:
        bot.send_inline_callback_button(user_id, msg, button)


def get_withdrawal_message():
    return f"""
🏦 <b>Withdrawal Process</b>:

To initiate a withdrawal, set your withdrawal address by selecting the cryptocurrency and providing your wallet address. Make sure to use the correct network for the chosen coin.

Next, withdraw the desired amount from your account balance, keeping in mind that there is a withdrawal fee of <b>{config['withdrawal_fee']}%</b> <i>if you have referral credit, it will be used.</i>. 

Please ensure that your requested withdrawal amount exceeds the minimum threshold of <b>${config['min_withdrawal']}</b> to meet the requirements.

After submitting your withdrawal request, it will be reviewed and accepted within <b>24 hours</b> for security purposes.

Once approved, the specified amount will be transferred to the provided address.

📤 Double-check all the details before submitting your withdrawal request and feel free to reach out to our support team if you need any assistance.
    
    """


def handle_withdrawal(user_id, msg_id):
    global address_changes_msg_id
    msg = get_withdrawal_message()
    button = Constants.withdrawal_button
    x = bot.edit_message(user_id, msg_id, msg, button)
    print(x.json())
    address_changes_msg_id[f"{user_id}"] = msg_id


def set_withdrawal_address(chat_id, msg_id):
    msg = "💱 Select a coin for withdrawal"
    button = {
        "resize_keyboard": True,
        "inline_keyboard": [[{"text": "BTC", "callback_data": f"withdrawal_payment_chosen$bitcoin"},
                             {"text": "LTC", "callback_data": f"withdrawal_payment_chosen$litecoin"}],
                            [{"text": Constants.back_button, 'callback_data': "open_wallet"},
                             {"text": "DOGE", "callback_data": f"withdrawal_payment_chosen$dogecoin"}]]
    }
    # temp_lst = []
    # for i, coin in enumerate(coins):
    #     temp_lst.append({"text": coin["symbol"], "callback_data": f"withdrawal_payment_chosen${coin['name']}"})
    #     if (i + 1) % 2 == 0:
    #         button["inline_keyboard"].append(temp_lst)
    #         temp_lst = []
    #
    # if temp_lst:
    #     button["inline_keyboard"].append(temp_lst)
    button["inline_keyboard"].append([])
    bot.edit_message(chat_id, msg_id, msg, button)


def withdrawal_payment_chosen(user_id, _, data):
    coin = data[0]
    symbol, network = paywall.get_symbol_and_network_using_coin_name(coin)
    user = users_manager.get_user(user_id)
    user.set_withdrawal_coin(symbol)
    user.set_withdrawal_address(None)
    message = Constants.reply_message_insert_address(symbol, network)
    x = bot.force_reply(user_id, message, "e.g. 0xabcd..")
    print(x)


def get_id_for_photo(d):
    try:
        text = d['message']['photo'][-1]['file_id']
        return text
    except Exception:
        return False


def get_text_for_address(d):
    try:
        text = d['message']['text']
        int_text = str(text)
        return int_text
    except Exception:
        return False


def update_address(address, current_update):
    # global users
    global address_changes_msg_id
    user_id = str(current_update['message']['from']['id'])

    try:
        user = users_manager.get_user(user_id)
        user.set_withdrawal_address(address)
        # users[f'{user_id}'] = user
        bot.delete_message(current_update['message']['chat']['id'], current_update['message']['message_id'])
        bot.delete_message(current_update['message']['chat']['id'],
                           current_update['message']['reply_to_message']['message_id'])
        msg_id = address_changes_msg_id[f"{user_id}"]
        msg = get_withdrawal_message()
        bot.edit_message(user_id, msg_id, msg, Constants.withdrawal_button)
    except Exception as ex:
        private_keyboard(user_id, current_update['message']['message_id'])
        print('Error from function - update_address: ' + str(ex))


def withdraw(chat_id):
    user = users_manager.get_user(chat_id)
    if user.get_withdrawal_address() is not None:
        msg = Constants.reply_message_insert_amount_to_withdraw
        bot.force_reply(chat_id, msg, "e.g. 25")

    else:
        set_button = {"resize_keyboard": True,
                      "inline_keyboard": [[{"text": "⚙️ Set Address", 'callback_data': f"set_withdrawal_address"}]]}

        bot.send_inline_callback_button(chat_id, Constants.error_message_no_address, set_button)


def update_amount_to_withdraw(amount, current_update):
    global address_changes_msg_id
    user_id = str(current_update['message']['from']['id'])
    user = users_manager.get_user(user_id=user_id)
    # users[f'{user_id}'] = user
    bot.delete_message(current_update['message']['chat']['id'], current_update['message']['message_id'])
    bot.delete_message(current_update['message']['chat']['id'],
                       current_update['message']['reply_to_message']['message_id'])

    user_balance = user.get_balance()
    try:
        amount = float(amount)
    except Exception:
        bot.send_message(user_id, Constants.error_message_not_a_number)
        return
    user.set_amount_to_withdraw(amount)
    if user_balance < amount:
        bot.send_message(user_id, Constants.error_message_not_enough_coins_to_withdraw)
        return

    if amount < config['min_withdrawal']:
        bot.send_message(user_id, Constants.error_message_below_min + f"<b>${config['min_withdrawal']}</b>")
        return

    new_withdrawal = Withdrawal(user, user.get_withdrawal_address(), user.get_amount_to_withdraw(),
                                user.get_withdrawal_coin())
    withdrawal_waiting_for_approve[f'{new_withdrawal.withdrawal_id}'] = new_withdrawal
    button = {"resize_keyboard": True,
              "inline_keyboard": [
                  [{"text": "❌ No", 'callback_data': f"waiting_for_withdrawal$NO_{new_withdrawal.withdrawal_id}"},
                   {"text": "✅ Yes", 'callback_data': f"waiting_for_withdrawal$YES_{new_withdrawal.withdrawal_id}"}]]}
    msg = f"⚠️ Are you sure you want to withdraw <b>${user.get_amount_to_withdraw()}</b> to the following <b>{user.get_withdrawal_coin()}</b> address?\n\n<code>{user.get_withdrawal_address()}</code>\n\nPlease note that a withdrawal fee of <b>{config['withdrawal_fee']}% (${round(user.get_amount_to_withdraw() * config['withdrawal_fee'] / 100, 2)})</b> will be deducted from the total amount. <i>if you have referral credit, it will be used.</i>"
    bot.send_inline_callback_button(user_id, msg, button)


def sign_manual_withdrawal(user, withdrawal,chat_id):
    withdrawal_fee = get_fee(withdrawal.amount, config['withdrawal_fee'], user)

    msg = f"️️️⚠️ New Withdrawal Request:\n\nUser ID: <b>{user.user_id}</b>\nWithdrawal ID: <b>{withdrawal.withdrawal_id}</b>\nAmount: <b>${str(withdrawal.amount - withdrawal_fee)}</b>\nCoin: <b>{withdrawal.coin}</b>"
    msg += '\n\n<code>' + str(withdrawal.receiver_address) + '</code>'
    button = {"resize_keyboard": True,
              "inline_keyboard": [[{"text": "❌ Deny",
                                    'callback_data': f"withdrawal_request_response$DENY_{withdrawal.withdrawal_id}"},
                                   {"text": "✅ Approve",
                                    'callback_data': f"withdrawal_request_response$APPROVE_{withdrawal.withdrawal_id}"}]]}
    path = f"Withdrawals/{withdrawal.withdrawal_id}"
    data = {"withdrawal_id": withdrawal.withdrawal_id, "user_id": user.user_id,
            "status": withdrawal.transaction_status, "amount": withdrawal.amount - withdrawal_fee,
            "coin": withdrawal.coin,
            "address": withdrawal.receiver_address}
    db.write_data([path, data])
    bot.send_inline_callback_button(config['admin_ids'][0], msg, button)
    bot.send_message(chat_id,
                     f"✅ Withdrawal Request Submitted!\n\nYour request to withdraw <b>${str(withdrawal.amount)}</b> has been successfully submitted. It will be processed shortly and sent to the following <b>{withdrawal.coin}</b> address:\n\n<code>{withdrawal.receiver_address}</code>\n\nRequest ID: <b>{withdrawal.withdrawal_id}</b>")


def commit_withdrawal(chat_id, message_id, data):
    try:
        withdrawal_id = data[1]
        yes_or_no = data[0]
        withdrawal = withdrawal_waiting_for_approve[f'{withdrawal_id}']
        user = withdrawal.sender

        if yes_or_no == 'YES' and str(chat_id) == user.user_id and withdrawal.transaction_status == "PENDING":
            enough_funds = user.get_balance() >= (withdrawal.amount)
            if not enough_funds:
                bot.send_message(chat_id, Constants.error_message_not_enough_coins_to_withdraw)
                return
            user.set_balance(user.get_balance() - (withdrawal.amount))
            withdrawal.transaction_status = "REQUESTED"
            wallet = admin_panel.wallets[f'{withdrawal.coin.lower()}_wallet']
            wallet_balance = wallet.get_balance_in_dollars()
            if wallet_balance < withdrawal.amount or 1000 <= withdrawal.amount:
                sign_manual_withdrawal(user, withdrawal,chat_id)
                return

            amount_in_sat = wallet.coin_to_satoshi(
                Binance.BinanceAPI.convert_to_crypto(withdrawal.amount, Binance.BinanceAPI.get_price(withdrawal.coin)))
            try:
                response = wallet.send_transaction(withdrawal.receiver_address, amount_in_sat)
                if response is False:
                    sign_manual_withdrawal(user, withdrawal,chat_id)
                    return
                print(response)
            except Exception as ex:

                sign_manual_withdrawal(user, withdrawal,chat_id)
                print(f"error from commit_withdrawal {ex}")
                return

            bot.send_message(chat_id,
                             f"✅ Withdrawal Request Submitted!\n\nYour request to withdraw <b>${str(withdrawal.amount)}</b> has been successfully submitted. It will be processed shortly and sent to the following <b>{withdrawal.coin}</b> address:\n\n<code>{withdrawal.receiver_address}</code>\n\nRequest ID: <b>{withdrawal_id}</b>")

            #  bot.send_inline_callback_button(config['admin_id'], msg, button)

        elif yes_or_no == 'NO' and str(chat_id) == withdrawal.sender.id[
                                                   1:] and withdrawal.transaction_status == "PENDING":
            withdrawal.transaction_status = "REJECTED"

            bot.send_message(chat_id, Constants.WithdrawalCancel)


        elif str(chat_id) == user.user_id and withdrawal.transaction_status != "PENDING":
            bot.send_message(chat_id, Constants.WithdrawalExpired)
        else:
            bot.send_message(chat_id, Constants.error_message_general)


    except Exception as ex:
        print(ex)
        bot.delete_message(chat_id, message_id)
        private_keyboard(chat_id, message_id)


def handle_close_payment_window(user_id, message_id, data):
    bot.delete_message(user_id, message_id)


def view_my_address(user_id, msg_id, data):
    user = users_manager.get_user(user_id)
    withdrawal_coin = user.get_withdrawal_coin()
    withdrawal_address = user.get_withdrawal_address()

    if withdrawal_coin is None or withdrawal_address is None:
        message = "⚠️ You haven't set a withdrawal address yet. Please set a withdrawal address first."
    else:
        message = f"📋 Your current withdrawal <b>{withdrawal_coin}</b> address:\n\n<code>{withdrawal_address}</code>"

    bot.send_message(user_id, message)


def withdrawal_request_response(user_id, msg_id, data):
    result = data[0]
    withdrawal_id = data[1]

    withdrawal = db.read_data([f'Withdrawals/{withdrawal_id}'])
    if withdrawal['status'] != "REQUESTED":
        bot.send_message(user_id, "❌ This request already handled")
        return

    if result == "APPROVE":
        withdrawal['status'] = "Completed"
        msg = "✅ Your withdrawal request (ID: <code>{}</code>) has been <b>approved</b> and will be processed shortly.".format(
            withdrawal_id)
    elif result == "DENY":
        msg = "❌ Your withdrawal request (ID: <code>{}</code>) has been <b>denied</b>. Please contact support for further assistance.".format(
            withdrawal_id)
        withdrawal['status'] = "Denied"
    else:
        msg = "⚠️ An <b>error occurred</b> while processing your withdrawal request (ID: <code>{}</code>). Please try again later or contact support.".format(
            withdrawal_id)
        withdrawal['status'] = "Failed"

    path = f"Withdrawals/{withdrawal_id}"
    db.write_data([path, withdrawal])

    bot.send_message(withdrawal['user_id'], msg)


def testing(chat_id, _):
    msg = '⚽ <b>Barcelona vs. Real Madrid</b> ⚽\n\n'
    msg += """
Join the excitement as Barcelona 🔴 faces Real Madrid ⚪ in a thrilling football showdown!
Bet now and be part of this epic clash between two football giants. 🎉

<b>📊 Winning Rates:</b>
Barcelona 🔴 <b>x2</b>
Real Madrid ⚪ <b>x1.5</b>

💰 Your current bet: <b>$55 on Barcelona 🔴</b>

⏱️ <b>Bets close in 15 minutes</b>
    """
    button = {"resize_keyboard": True,
              "inline_keyboard": [
                  [{"text": "Bet on Barcelona 🔴", 'callback_data': "add_selection"},
                   {"text": "Bet on Real Madrid ⚪", 'callback_data': "add_selection"}]
                  ,
                  [{"text": "+ $5", 'callback_data': "add_selection"},
                   {"text": "+ $10", 'callback_data': "add_selection"},
                   {"text": "+ $25", 'callback_data': "add_selection"},
                   {"text": "+ $50", 'callback_data': "add_selection"},
                   {"text": "+ $100", 'callback_data': "add_selection"}]]}
    resp = bot.send_photo(chat_id, "BQACAgQAAxkBAANTZQtCDFuYy1HA0mE86wMtlf-k_lIAAn0RAALZ01hQ-_vhW8tinm0wBA", msg,
                   button)





def handle_pool(chat_id):
    msg = f"🏊 @{config['bot_username']} <b>Pool</b>\n\n"
    msg += f"💰 Current balance: <b>${round(liquidity_pool.get_balance(), 2)}</b>\n\n"
    msg += "🛂 Queue:\n"
    debt = 0
    counter = 0
    for participant in liquidity_pool.get_queue():
        counter += 1
        if counter <= 5:
            msg += f"• <code>{participant['user_id']}</code>  |  <b>{participant['first_name']}</b>  |  <b>${round(participant['multiplier'] * participant['amount'], 2)}</b>\n"
        debt += participant['multiplier'] * participant['amount']

    if counter > 5:
        msg += f'...\n'
    msg += f"\n📈 Total debt: <b>${round(debt, 2)}</b>"
    bot.send_message(chat_id, msg)


def handle_support(chat_id):
    button = {"resize_keyboard": True,
              "inline_keyboard": [[{"text": "Contact Us", 'url': f"t.me/{config['support_username']}"}]]}
    msg = "👋 Need assistance or have questions? Feel free to reach out to our support team. We're here to help you! 🛠️"
    bot.send_inline_callback_button(chat_id, msg, button)


def handle_about(chat_id):
    button = {"resize_keyboard": True,
              "inline_keyboard": [[{"text": "Join now!", 'url': f"t.me/{config['community_username']}"}],
                                  [{"text": "Contact Admin", 'url': f"t.me/{config['admin_username']}"}]]}
    msg = f"📣 About Us 🤝\n\nWelcome to @{config['bot_username']}, where you can bet on your favorite sports events with cryptocurrency! 💰⚽🏀🏈\n\nHow it works:\n\n1️⃣ Deposit cryptocurrency to start betting.\n2️⃣ Place bets on your chosen events.\n3️⃣ If you win, your payout comes from our bot's payment pool (/pool).\n4️⃣ In case the pool doesn't have enough funds, don't worry! You'll join a queue until other users contribute enough to cover the payout.\n\nWe're here to make sports betting fun and secure for you. Feel the thrill and join the action today! 🎉💪\n\nGot questions or need assistance? Contact our support team anytime. 🛠️👇"

    bot.send_inline_callback_button(chat_id, msg, button)


def handle_referral(user_id, msg_id, data):
    user = users_manager.get_user(user_id)
    msg = f"""
    
Your referral link: https://t.me/{config['bot_username']}?start={user_id}

For each referral you get <b>$5</b> cashback on deposit and withdrawal fees!
Your Balance: <b>${user.get_fee_credit()}</b>
"""
    button = {"resize_keyboard": True,
              "inline_keyboard": [[{"text": Constants.back_button, 'callback_data': "open_wallet"}]]}

    bot.edit_message(user_id, msg_id, msg, button)

def handle_new_referral(user_id, text):
    print("!@#!@#@!#!@#@!#!@#@!#@!#@!#@!#")
    if user_id in referred_users:
        return
    referring_user_id = ''
    for letter in text:
        if letter.isnumeric():
            referring_user_id += letter

    if str(user_id) == referring_user_id:
        return
    try:
        referring_user_id = int(referring_user_id)
    except Exception:
        return
    referring_user_id = str(referring_user_id)
    user = users_manager.get_user(referring_user_id)
    user.set_fee_credit(user.get_fee_credit() + 5)
    referred_users.append(user_id)

def main():
    t = threading.Thread(target=check_for_status_change, args=())
    t.start()
    while True:
        print("Bot Started V2")
        try:
            global bot
            bot = TgMethods.BotHandler(config["api_key"])
            new_offset = 0
            # last_all_chats_info_update = datetime.now()
            # update_all_chats_info()
            init = True

            while True:
                if init:
                    all_updates = bot.get_updates(new_offset)
                    if all_updates != False:
                        if len(all_updates) > 0:
                            for current_update in all_updates:
                                first_update_id = current_update['update_id']
                                new_offset = first_update_id + 1
                            init = False
                all_updates = bot.get_updates(new_offset)
                if all_updates == False:
                    time.sleep(30)
                    break
                if len(all_updates) > 0:
                    for current_update in all_updates:
                        current_update_dumped = json.dumps(current_update)
                        print('_____________________\n')
                        pprint(json.loads(current_update_dumped))
                        print('_____________________\n')
                        # print(owner_chat_pd)

                        # if (check_if_time_to_update(last_all_chats_info_update)):
                        #     last_all_chats_info_update = datetime.now()
                        if (check_if_text_message(current_update, '/pool', config['bot_username'])):
                            handle_pool(current_update['message']['chat']['id'])

                        if (check_if_text_message(current_update, '/start')) and is_private_chat(
                                current_update):
                            private_keyboard(current_update['message']['chat']['id'],
                                             current_update['message']['message_id'])

                        elif (check_if_text_in_message(current_update, '/start')) and is_private_chat(
                                current_update):
                            private_keyboard(current_update['message']['chat']['id'],
                                             current_update['message']['message_id'])
                            handle_new_referral(current_update['message']['chat']['id'],current_update['message']['text'])


                        if (check_if_text_message(current_update, '/admin')) and is_private_chat(
                                current_update):
                            admin_panel.open_admin_panel(current_update['message']['chat']['id'])

                        # if check_if_in_callback_data(current_update, "open_admin"):
                        #     user_id, msg_id, _ = get_variables(current_update)
                        #     admin_panel.handle_start_admin(user_id, msg_id)

                        if (check_if_text_message(current_update,
                                                  "🛎 Support") and is_private_chat(
                            current_update)):
                            handle_support(current_update['message']['chat']['id'])

                        if (check_if_text_message(current_update,
                                                  "💡 About") and is_private_chat(
                            current_update)):
                            handle_about(current_update['message']['chat']['id'])

                        if (check_if_text_message(current_update,
                                                  "💼 Wallet") and is_private_chat(
                            current_update)) or check_if_in_callback_data(current_update,
                                                                          "open_wallet"):
                            open_wallet(current_update,
                                        check_if_in_callback_data(current_update, "open_wallet"))

                        if (check_if_text_message(current_update,
                                                  "📺 Events") and is_private_chat(
                            current_update)):
                            event_manager.handle_open_events(current_update['message']['from']['id'])

                        if check_if_in_callback_data(current_update, "deposit_coins"):
                            user_id, msg_id, _ = get_variables(current_update)
                            handle_deposit(user_id, msg_id)
                        if check_if_in_callback_data(current_update, "withdrawal_coins"):
                            user_id, msg_id, _ = get_variables(current_update)
                            handle_withdrawal(user_id, msg_id)

                        if check_if_in_callback_data(current_update, "set_withdrawal_address"):
                            user_id, msg_id, _ = get_variables(current_update)
                            set_withdrawal_address(user_id, msg_id)

                        if check_if_in_callback_data(current_update, "deposit_payment_chosen$"):
                            user_id, msg_id, data = get_variables(current_update)
                            handle_deposit_payment_chosen(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "withdrawal_payment_chosen$"):
                            user_id, msg_id, data = get_variables(current_update)
                            withdrawal_payment_chosen(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "withdrawing"):
                            user_id, msg_id, data = get_variables(current_update)
                            withdraw(user_id)
                        if check_if_in_callback_data(current_update, "waiting_for_withdrawal$"):
                            user_id, msg_id, data = get_variables(current_update)
                            commit_withdrawal(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "withdrawal_request_response$"):
                            user_id, msg_id, data = get_variables(current_update)
                            withdrawal_request_response(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "view_my_address"):
                            user_id, msg_id, data = get_variables(current_update)
                            view_my_address(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "close_payment_window"):
                            user_id, message_id, data = get_variables(current_update)
                            handle_close_payment_window(user_id, message_id, data)

                        if check_if_in_callback_data(current_update, "open_sport$"):
                            user_id, msg_id, data = get_variables(current_update)
                            event_manager.handle_open_sport(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "*$"):
                            user_id, msg_id, data = get_variables(current_update)
                            event_manager.handle_sport_events(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "open_events"):
                            user_id, msg_id, data = get_variables(current_update)
                            event_manager.handle_open_events(user_id, msg_id, data[0])

                        if check_if_in_callback_data(current_update, "p_event$"):
                            user_id, msg_id, data = get_variables(current_update)
                            event_manager.handle_p_event(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "sel_t$"):
                            user_id, msg_id, data = get_variables(current_update)
                            chat_id = current_update['callback_query']['message']['chat']['id']
                            first_name = current_update['callback_query']['from']['first_name']
                            event_manager.handle_sel_t(chat_id, user_id, first_name, msg_id, data)

                        if check_if_in_callback_data(current_update, "referral"):
                            user_id, msg_id, data = get_variables(current_update)
                            handle_referral(user_id, msg_id, data)

                        if check_if_in_callback_data(current_update, "put_bet$"):
                            user_id, msg_id, data = get_variables(current_update)
                            chat_id = current_update['callback_query']['message']['chat']['id']
                            first_name = current_update['callback_query']['from']['first_name']
                            event_manager.handle_put_bet(chat_id, user_id, users_manager.get_user(user_id), first_name,
                                                         msg_id, data)

                        if check_if_in_callback_data(current_update, "clear_b$"):
                            user_id, msg_id, data = get_variables(current_update)
                            chat_id = current_update['callback_query']['message']['chat']['id']
                            first_name = current_update['callback_query']['from']['first_name']
                            event_manager.handle_clear_b(chat_id, user_id, users_manager.get_user(user_id), first_name,
                                                         msg_id, data)

                        if check_if_in_callback_data(current_update, "view_p$"):
                            user_id, msg_id, data = get_variables(current_update)
                            chat_id = current_update['callback_query']['message']['chat']['id']
                            event_manager.handle_view_p(chat_id, data)

                        if is_reply_to_message_text_list_in(current_update,
                                                            Constants.reply_message_insert_address_for_test):
                            address = get_text_for_address(current_update)
                            update_address(address, current_update)

                        if is_reply_to_message(current_update,
                                               Constants.reply_message_insert_amount_to_withdraw):
                            res = get_text_for_address(current_update)
                            update_amount_to_withdraw(res, current_update)

                        first_update_id = current_update['update_id']
                        new_offset = first_update_id + 1

        except Exception as e:
            print("Error: " + str(e))


if __name__ == '__main__':
    main()
