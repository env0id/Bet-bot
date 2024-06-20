from User import User


class UsersManager:
    def __init__(self):
        self.users = {}

    def get_user(self,user_id):
        if str(user_id) not in self.users:
            self.users[f'{user_id}'] = User(f'{user_id}')
        return self.users[f'{user_id}']
