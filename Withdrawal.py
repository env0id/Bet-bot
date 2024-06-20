import random


class Withdrawal:
    def __init__(self, sender, receiver_address, amount, coin):
        self.sender = sender
        self.withdrawal_id = str(random.randint(10000000,999999999))
        self.receiver_address = receiver_address
        self.coin = coin
        self.amount = amount
        self.transaction_status = "PENDING"  #PENDING / REJECTED / APPROVED