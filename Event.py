from DBSingleton import DBSingleton



class Event:
    def __init__(self, event_id, away_team, home_team, sport_key, sport_title, bookmakers, commence_time, sport_group,
                 sport_description, participants, completed, write_to_db=False):

        self.event_id = event_id
        self.away_team = away_team
        self.home_team = home_team
        self.sport_key = sport_key
        self.sport_title = sport_title
        self.bookmakers = bookmakers
        self.commence_time = commence_time
        self.sport_group = sport_group
        self.sport_description = sport_description

        self._completed = completed
        self._participants = {} if participants is None else participants  # Format: {"user_id" : {"first_name": first_name, "amount": 0, "bet": selected_team} ..}

        self.db = DBSingleton.getInstance().get_db()
        self.process_new_event(write_to_db)

        # if self.event_id == "725a53137d523a689adbbfb415f277a7":
        #     self._participants = {"5200784418": {"first_name": "Mr Badihi", "amount": 10, "bet": "New York Mets"}}

    def process_new_event(self, write_to_db):
        if write_to_db:
            new_event_data = {
                'participants': self._participants,
                'away_team': self.away_team,
                'home_team': self.home_team,
                'sport_key': self.sport_key,
                'sport_title': self.sport_title,
                'bookmakers': self.bookmakers,
                'commence_time': self.commence_time,
                'sport_group': self.sport_group,
                'sport_description': self.sport_description,
                'completed': self._completed
            }
            self.db.write_data([f'Events/{self.event_id}', new_event_data])

    def get_participants(self):
        return self._participants

    def set_participants(self, participants):
        self._participants = participants
        event_data = self.db.read_data([f'Events/{self.event_id}'])
        event_data['participants'] = participants
        self.db.write_data([f'Events/{self.event_id}', event_data])

    def get_completed(self):
        return self._completed

    def set_completed(self, completed):
        self._completed = completed
        event_data = self.db.read_data([f'Events/{self.event_id}'])
        event_data['completed'] = completed
        self.db.write_data([f'Events/{self.event_id}', event_data])

