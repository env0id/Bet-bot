class Constants:
    Currency = "$"
    Confirmations = 6
    Fee = 0.05
    MinDaysPlan = 1
    MinPricePlan = 5

    Abs_path = ''
    DB_path = 'DB\\'
    WithdrawalCancel = "🗙 Withdrawal canceled."
    WithdrawalExpired = "🗙 Withdrawal expired."

    reply_message_insert_address_for_test = ['✏️ Enter your', 'address', 'Network:']

    @staticmethod
    def reply_message_insert_address(CryptoCurrency, Network2):
        reply_message_insert_address = '✏️ Enter your <b>' + str(
            CryptoCurrency) + '</b> address \n\n⚠️ Network: <b>' + str(
            Network2) + "</b>"
        return reply_message_insert_address

    reply_message_insert_amount_to_withdraw = "✏️ Input the amount you wish to withdraw in dollars"
    reply_message_insert_event_name = "✏️ Input the event name"
    reply_message_insert_event_description = "✏️ Input the event description\nto skip type /skip"
    reply_message_insert_event_image = "✏️ Insert the event image\nto skip type /skip"
    reply_message_insert_side_name = "✏️ Insert the side bet name"
    reply_message_insert_side_odds = "✏️ Enter the odds for the side bet\nExample: 0.7 (for a 70% chance of winning this side)"

    error_message_general = '❌ An error has occurred.'
    error_message_not_enough_coins_to_withdraw = "❌ Not enough funds. Please set an amount less than or equal to the balance in your wallet."
    error_message_not_a_number = "❌ Enter a valid number."
    error_message_no_address = "❌ You do not have a valid address to send the coins."
    error_message_below_min = '❌ The minimum amount to withdraw is '

    back_button = '‹ Back'
    withdrawal_button = {"resize_keyboard": True,
                         "inline_keyboard": [[{"text": "💸 Withdraw", 'callback_data': f"withdrawing"}], [
                             {"text": "⚙️ Set Withdrawal Address", 'callback_data': f"set_withdrawal_address"}],
                                             [{"text": "📋 My Withdrawal Address", 'callback_data': f"view_my_address"}],
                                             [{"text": back_button, 'callback_data': "open_wallet"}]]}
