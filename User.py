from DBSingleton import DBSingleton


class User:
    def __init__(self, user_id):
        # Default Values
        self.user_id = user_id
        self._balance = 0
        self._referral_users = 0
        self._fee_credit = 0
        self._language = "en"
        self._withdrawal_address = None
        self._withdrawal_coin = None
        self._amount_to_withdraw = None
        self._events = []
        self.db = DBSingleton.getInstance().get_db()
        self.process_new_user()

    def process_new_user(self):
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        if user_data is None:
            # User doesn't exist, add them to the database
            new_user_data = {
                'balance': self._balance,
                'language': self._language,
                'withdrawal_address': self._withdrawal_address,
                'withdrawal_coin': self._withdrawal_coin,
                'amount_to_withdraw': self._amount_to_withdraw,
                'events': self._events,
                'fee_credit': self._fee_credit
            }
            self.db.write_data([f'Users/{self.user_id}', new_user_data])
        else:
            # User already exists, load user data from the database
            self._balance = user_data.get('balance', self._balance)
            self._language = user_data.get('language', self._language)
            self._withdrawal_address = user_data.get('withdrawal_address', self._withdrawal_address)
            self._withdrawal_coin = user_data.get('withdrawal_coin', self._withdrawal_coin)
            self._amount_to_withdraw = user_data.get('amount_to_withdraw', self._amount_to_withdraw)
            self._events = user_data.get('events', self._events)
            self._fee_credit = user_data.get('fee_credit', self._fee_credit)


    def get_language(self):
        return self._language

    def get_balance(self):
        return round(self._balance, 2)

    def set_balance(self, amount):
        self._balance = amount
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        user_data['balance'] = amount
        self.db.write_data([f'Users/{self.user_id}', user_data])

    def pay(self, user, amount):
        user_balance = user.get_balance()
        user.set_balance(user_balance + amount)
        self_balance = self.get_balance()
        self.set_balance(self_balance - amount)

    def get_withdrawal_address(self):
        return self._withdrawal_address

    def set_withdrawal_address(self, address):
        self._withdrawal_address = address
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        user_data['withdrawal_address'] = address
        self.db.write_data([f'Users/{self.user_id}', user_data])

    def set_withdrawal_coin(self, coin):
        self._withdrawal_coin = coin
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        user_data['withdrawal_coin'] = coin
        self.db.write_data([f'Users/{self.user_id}', user_data])

    def get_withdrawal_coin(self):
        return self._withdrawal_coin

    def set_amount_to_withdraw(self, amount):
        self._amount_to_withdraw = amount
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        user_data['amount_to_withdraw'] = amount
        self.db.write_data([f'Users/{self.user_id}', user_data])

    def get_amount_to_withdraw(self):
        return self._amount_to_withdraw

    def get_events(self):
        return self._events

    def add_new_event(self, event_id):
        self._events.append(event_id)
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        user_data['events'] = self._events
        self.db.write_data([f'Users/{self.user_id}', user_data])

    def remove_event(self, event_id):
        if event_id not in self._events:
            return False
        self._events.remove(event_id)
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        user_data['events'] = self._events
        self.db.write_data([f'Users/{self.user_id}', user_data])

    def set_fee_credit(self, credit):
        self._fee_credit = credit
        user_data = self.db.read_data([f'Users/{self.user_id}'])
        user_data['fee_credit'] = credit
        self.db.write_data([f'Users/{self.user_id}', user_data])

    def get_fee_credit(self):
        return self._fee_credit