class LiquidityPool:
    def __init__(self, db, users_manager, bot):
        self.users_manager = users_manager
        self.db = db
        self.bot = bot
        self.pool_id = '1'
        self._balance = 0
        self._queue = []
        self.init_pool()

    def init_pool(self):
        pool_data = self.db.read_data([f'LiquidityPools/{self.pool_id}'])
        if pool_data is None:
            # User doesn't exist, add them to the database
            new_pool_data = {
                'balance': self._balance,
                'queue': self._queue,

            }
            self.db.write_data([f'LiquidityPools/{self.pool_id}', new_pool_data])

        else:
            # User already exists, load user data from the database
            self._balance = pool_data.get('balance', self._balance)
            self._queue = pool_data.get('queue', self._queue)

    def get_balance(self):
        return self._balance

    def set_balance(self, amount):
        self._balance = amount
        pool_data = self.db.read_data([f'LiquidityPools/{self.pool_id}'])
        pool_data['balance'] = amount
        self.db.write_data([f'LiquidityPools/{self.pool_id}', pool_data])

    def sign_participant_to_queue(self, participant):
        self._queue.append(participant)
        pool_data = self.db.read_data([f'LiquidityPools/{self.pool_id}'])
        pool_data['queue'] = self._queue
        self.db.write_data([f'LiquidityPools/{self.pool_id}', pool_data])

    def pop_participant_from_queue(self):
        self._queue.pop(0)
        pool_data = self.db.read_data([f'LiquidityPools/{self.pool_id}'])
        pool_data['queue'] = self._queue
        self.db.write_data([f'LiquidityPools/{self.pool_id}', pool_data])

    def get_queue(self):
        return self._queue

    def get_next_participant_in_queue(self):
        if len(self._queue) < 1:
            return False
        return self._queue[0]

    def handle_new_participant(self, participant_data, participant_id, multiplier, event):
        try:
            participant_data['multiplier'] = multiplier
            self.set_balance(self.get_balance() + participant_data['amount'])
            participant_data['user_id'] = participant_id
            if multiplier != 0:
                self.bot.send_message(participant_id,
                                      f"🎊 Congratulations!\nYou've just won the event between <b>{event.home_team}</b> and <b>{event.away_team}</b>.")

                self.sign_participant_to_queue(participant_data)

            next_p = self.get_next_participant_in_queue()
            while next_p and next_p['multiplier'] * next_p['amount'] <= self.get_balance():
                user = self.users_manager.get_user(next_p['user_id'])
                user.set_balance(user.get_balance() + next_p['multiplier'] * next_p['amount'])
                self.set_balance(self.get_balance() - next_p['multiplier'] * next_p['amount'])
                self.pop_participant_from_queue()
                self.bot.send_message(next_p['user_id'],
                                      f"✅ New payment of <b>${next_p['multiplier'] * next_p['amount']}</b> received from the pool.")
                next_p = self.get_next_participant_in_queue()


        except Exception as ex:
            print(f"Error from handle_new_participant {ex}")
