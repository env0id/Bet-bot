class DepositRequest:

    def __init__(self, user_id, order_id, creation_time):
        self.completed = False
        self.user_id = user_id
        self.order_id = order_id
        self.creation_time = creation_time
