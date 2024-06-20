import math
import re
import threading
import time
from datetime import datetime

import requests
from pprint import pprint
from datetime import datetime, timedelta

import mock_data
from Constants import Constants
from DBSingleton import DBSingleton
from Event import Event
from LiquidityPool import LiquidityPool
from SportsWithScores import sports_with_scores


class EventsManager:
    def __init__(self, config, bot, users_manager, liquidity_pool):
        self.config = config
        self.api_key = self.config['the_odds_api_key']
        self.users_manager = users_manager
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.bot = bot
        self.value_per_page = 8
        self.events = {}
        self._sports = self.get_sports()

        self.liquidity_pool = liquidity_pool
        self.db = DBSingleton.getInstance().get_db()
        self.unsupported_leagues_BetsAPI = ['ECS Italy, Rome', 'CSA One Day Cup Division 1', 'Super Series Women']
        self.load_all_events_from_db()
        t = threading.Thread(target=self.refresh_events, args=())
        t.start()

    # self.enabled_sports = ['soccer_epl', 'soccer_uefa_champs_league']

    def get_sports(self):
        response = requests.get(f'{self.base_url}/sports', params={'apiKey': self.api_key})
        if response.status_code == 200:
            return response.json()
        return False

    def get_odds(self, sport):
        response = requests.get(f'{self.base_url}/sports/{sport}/odds',
                                params={'apiKey': self.api_key, 'regions': 'us', 'dateFormat': 'unix'})
        if response.status_code == 200:
            return response.json()
        return False

    def get_event_odd(self, sport, event_id):
        response = requests.get(f'{self.base_url}/sports/{sport}/events/{event_id}/odds',
                                params={'apiKey': self.api_key, 'regions': 'us', 'dateFormat': 'unix'})
        if response.status_code == 200:
            if response.status_code == 200:
                return response.json()
            return False

    def get_scores(self, sport):
        response = requests.get(f'{self.base_url}/sports/{sport}/scores',
                                params={'apiKey': self.api_key, 'daysFrom': 3, 'dateFormat': 'unix'})
        if response.status_code == 200:
            return response.json()
        return False

    def load_all_events_from_db(self):
        start_time = time.time()
        if self.config['test_mode']:
            events = mock_data.mock_data
        else:
            events = self.db.get_full_collection('Events')
        for event_id in events:
            event = events[event_id]
            self.events[event_id] = Event(event_id, away_team=event['away_team'], home_team=event['home_team'],
                                          sport_key=event['sport_key'], sport_title=event['sport_title'],
                                          bookmakers=event['bookmakers'], commence_time=event['commence_time'],
                                          sport_group=event['sport_group'],
                                          sport_description=event['sport_description'],
                                          participants=event['participants'],
                                          completed=event['completed']
                                          )
        print(f"Complete load_all_events_from_db in {time.time() - start_time} seconds")

    def handle_cashing(self, event, results, winner=None):
        try:

            msg = "🚨 <b>Event Over</b> 🚨\n\n"
            msg += f'⚫️ <b>{event.home_team} vs {event.away_team}</b> 🔴\n\n'

            if winner is None:
                first_team = results[0]
                second_team = results[1]
                if int(first_team['score']) == int(second_team['score']):
                    winner = 'Draw'
                elif int(first_team['score']) > int(second_team['score']):
                    winner = first_team['name']
                elif int(first_team['score']) < int(second_team['score']):
                    winner = second_team['name']
                else:
                    print(f"Error in handle_cashing, event_id: {event.event_id}")

            participants = event.get_participants()
            winner_odds = 0

            for res in event.bookmakers:
                if res['name'] == winner:
                    winner_odds = float(res['price'])

            msg += f"📊 Results: <b>{'Draw' if winner == 'Draw' else winner + ' won!'}</b>\n"
            msg += f"💰 Multiplier: <b>x{winner_odds:.2f}</b>\n"
            msg += "🍀 Winners:\n"
            there_is_winner = False

            for participant_id in participants:
                if participants[participant_id]['bet'] != winner:
                    self.liquidity_pool.handle_new_participant(participants[participant_id], participant_id, 0, event)

                else:
                    there_is_winner = True
                    msg += "• " + participants[participant_id]['first_name'] + "\n"
                    self.liquidity_pool.handle_new_participant(participants[participant_id], participant_id,
                                                               winner_odds, event)

            if not there_is_winner:
                msg = msg.replace("🍀 Winners:", "😔 There are no winners ")

            msg += f"\nID: <code>{event.event_id}</code>"

            # image = "AgACAgQAAxkBAAIhSmUCocKptcLPnHonHFFNPBYOGsyxAAKpvDEbKcwZUL8rbXsLh_kkAQADAgADeAADMAQ"
            # self.bot.send_photo(self.config['community_chat_id'], image, msg)
            self.bot.send_message(self.config['community_chat_id'], msg)

        except Exception as ex:
            print(f"Error in handle_cashing: {ex}")

    def completed_events(self, scores):
        for score in scores:
            try:
                if score['completed'] and score['id'] in self.events:
                    results = score['scores']
                    event = self.events[score['id']]
                    if not event.get_completed():
                        self.handle_cashing(event, results)
                        event.set_completed(True)
            except Exception as ex:
                print(f"Error from completed_events {ex}")

    def sign_new_events(self, odds, sport):
        for odd in odds:
            try:

                event_id = odd['id']
                if event_id in self.events or self.config['test_mode']:
                    continue
                away_team = odd['away_team']
                home_team = odd['home_team']
                if home_team is None or away_team is None:
                    continue
                sport_key = odd['sport_key']
                sport_title = odd['sport_title']
                bookmakers = odd['bookmakers'][0]['markets'][0]['outcomes']
                commence_time = odd['commence_time']
                sport_group = sport['group']
                sport_description = sport['description']
                new_event = Event(event_id, away_team, home_team, sport_key, sport_title, bookmakers, commence_time,
                                  sport_group, sport_description, None, False, True)
                self.notify_users(new_event)
                self.events[event_id] = new_event
            except Exception as ex:
                continue

    @staticmethod
    def sort_events_by_commence_time(events):
        # Sort the events dictionary by the commence_time attribute of each Event instance.
        sorted_events = dict(sorted(events.items(), key=lambda x: x[1].commence_time))
        return sorted_events

    def handle_TheOddsAPI(self):
        self._sports = self.get_sports()
        for sport in self._sports:
            try:
                if sport['key'] not in sports_with_scores:
                    continue
                odds = self.get_odds(sport['key'])
                scores = self.get_scores(sport['key'])

                self.sign_new_events(odds, sport)
                self.completed_events(scores)
                self.events = self.sort_events_by_commence_time(self.events)
            except Exception as ex:
                print(f"Error: {ex}")
                continue

    @staticmethod
    def get_utc_date_yesterday():
        utc_now = datetime.utcnow()
        yesterday = utc_now - timedelta(days=1)
        utc_date = yesterday.strftime("%Y%m%d")
        return utc_date

    @staticmethod
    def get_utc_date():
        utc_now = datetime.utcnow()
        utc_date = utc_now.strftime("%Y%m%d")
        return utc_date

    def get_upcoming_events(self, sport):

        res = requests.get(f'https://api.b365api.com/v3/events/upcoming',
                           params={'token': self.config['betsapi_key'], 'sport_id': sport,
                                   "day": self.get_utc_date()}).json()
        if res['success'] == 0:
            print(f"Error from get_upcoming_events")
            return False
        return res['results']

    def get_cricket_odds(self, event_id, home, away):
        try:
            odds = requests.get(f'https://api.b365api.com/v2/event/odds',
                                params={'token': self.config['betsapi_key'], 'event_id': event_id}).json()['results'][
                'odds']['3_1'][0]
            return [{"name": home, "price": odds['home_od']}, {"name": away, "price": odds['away_od']}]
        except Exception as ex:
            return False

    def sign_new_events_BetsAPI(self, sport):
        upcoming_events = self.get_upcoming_events(sport['id'])
        if not upcoming_events:
            return False

        for coming_event in upcoming_events:
            pprint(coming_event)
            try:

                event_id = coming_event['id']
                if event_id in self.events or self.config['test_mode']:
                    continue

                away_team = coming_event['away']['name']
                home_team = coming_event['home']['name']
                if home_team is None or away_team is None:
                    continue
                sport_key = coming_event['league']['name']
                sport_title = coming_event['league']['name']
                if sport_title in self.unsupported_leagues_BetsAPI:
                    continue

                odds = self.get_cricket_odds(event_id, home_team, away_team)
                pprint(odds)
                if odds is False:
                    continue

                bookmakers = odds
                commence_time = float(coming_event['time'])
                if commence_time < time.time():
                    continue

                sport_group = sport['name']
                sport_description = None

                new_event = Event(event_id, away_team, home_team, sport_key, sport_title, bookmakers, commence_time,
                                  sport_group, sport_description, None, False, True)
                self.notify_users(new_event)
                self.events[event_id] = new_event
            except Exception as ex:
                continue

    def determine_match_winner(self, result_string):
        # Use regular expressions to extract the relevant information
        pattern = r'(\d+)/(\d+)\((\d+\.?\d*)\)-(\d+)/(\d+)\((\d+\.?\d*)\)'
        match = re.match(pattern, result_string)

        if match:
            home_runs, home_wickets, home_overs, away_runs, away_wickets, away_overs = map(
                lambda x: float(x) if '.' in x else int(x),
                match.groups()
            )

            if home_runs > away_runs:
                return "home"
            elif home_runs < away_runs:
                return "away"
            else:
                return "draw"
        else:
            return False

    def completed_events_BetsAPI(self, sport):
        scores_today = requests.get(f'https://api.b365api.com/v3/events/ended',
                              params={'token': self.config['betsapi_key'], 'sport_id': sport['id'],
                                      "day": self.get_utc_date()}).json()['results']  # Check what about mid-night
        scores_yesterday = requests.get(f'https://api.b365api.com/v3/events/ended',
                              params={'token': self.config['betsapi_key'], 'sport_id': sport['id'],
                                      "day": self.get_utc_date_yesterday()}).json()['results']  # Check what about mid-night
        for scores in [scores_today,scores_yesterday]:
            for score in scores:
                try:
                    if score['ss'] is not None and score['id'] in self.events:
                        results = score['ss']
                        event = self.events[score['id']]
                        winner = self.determine_match_winner(results)

                        if winner == 'home':
                            winner = event.home_team
                        elif winner == 'away':
                            winner = event.away_team
                        else:
                            print(f"Error from completed_events couldnt find a winner: {winner}")
                            continue

                        if not event.get_completed():
                            self.handle_cashing(event, results, winner)
                            event.set_completed(True)
                except Exception as ex:
                    print(f"Error from completed_events {ex}")





    def handle_BetsAPI(self):
        self._sports = [{"id": 3, "name": "Cricket"}]
        for sport in self._sports:
            try:

                self.sign_new_events_BetsAPI(sport)
                self.completed_events_BetsAPI(sport)

                self.events = self.sort_events_by_commence_time(self.events)
            except Exception as ex:
                print(f"Error: {ex}")
                continue

    def refresh_events(self):
        while True:
            try:
                self.handle_TheOddsAPI()
                self.handle_BetsAPI()
                self.clean_events()
                print("Complete refresh events")
                time.sleep(self.config['events_refresh_interval'])
            except Exception as ex:
                print(f"Error from refresh_events")

    def clean_events(self):
        three_days = 260000
        one_day = three_days / 3
        event_ids_to_del = []
        reason = None
        for event in self.events.values():
            if event.get_completed() and time.time() > event.commence_time + three_days:
                event_ids_to_del.append(event.event_id)
                reason = 'completed'

            elif not event.get_completed() and time.time() > event.commence_time + one_day:
                event_ids_to_del.append(event.event_id)
                reason = 'force complete'

                # return the money
                participants = event.get_participants()
                for participant_id in participants:
                    user = self.users_manager.get_user(participant_id)
                    user.set_balance(user.get_balance() + participants[participant_id]['amount'])

            if event.home_team is None or event.away_team is None:
                event_ids_to_del.append(event.event_id)
                reason = 'team is None'

        for event_id in event_ids_to_del:
            self.db.delete_data([f'Events/{event_id}'])
            del self.events[event_id]
            print(f"Event {event_id} has been deleted ({reason})")

    # def sign_new_event(self, event):
    #     self.events[f'{event.event_id}'] = event

    def unix_to_datetime(self, unix_timestamp):
        try:
            # Convert the Unix timestamp to a datetime object
            dt_object = datetime.utcfromtimestamp(unix_timestamp)

            # Format the datetime object as a string without seconds
            formatted_date_time = dt_object.strftime('%Y-%m-%d %H:%M')

            return formatted_date_time
        except Exception as e:
            return str(e)

    def slice_dict_by_indices(self, input_dict, start_index, end_index):
        # Convert the dictionary items into a list of key-value pairs
        dict_items = list(input_dict.items())

        # Check if start_index is within the valid range
        print(start_index)
        print(len(dict_items))
        if start_index < 0 or start_index >= len(dict_items):
            start_index = 0

        # If end_index is greater than or equal to the dictionary size, adjust it
        if end_index >= len(dict_items):
            end_index = len(dict_items) - 1

        # Check if start_index is greater than end_index
        if start_index > end_index:
            if len(dict_items) >= self.value_per_page:
                end_index = self.value_per_page
            else:
                end_index = len(dict_items) % self.value_per_page
        # Slice the list of key-value pairs between start_index and end_index
        sliced_items = dict_items[start_index:end_index + 1]

        # Create a new dictionary from the sliced key-value pairs
        sliced_dict = dict(sliced_items)

        return sliced_dict

    def handle_open_events(self, user_id, message_id=None, page=0):
        page = int(page)
        button = {"resize_keyboard": True,
                  "inline_keyboard": []}

        sports = {}
        # for sport in self._sports:
        #     sports[sport['group']] = None
        for event in self.events.values():
            if event.get_completed():
                continue
            sport = event.sport_group
            sports[sport] = None

        original_sports_size = len(sports)
        sports = self.slice_dict_by_indices(sports, page * self.value_per_page,
                                            page * self.value_per_page + self.value_per_page - 1)
        for sport in sports:
            button['inline_keyboard'].append([{"text": sport, 'callback_data': f"open_sport${sport}_0"}])

        button['inline_keyboard'].append(
            [{"text": "•" if page == 0 else '«', 'callback_data': f"open_events${page if page == 0 else page - 1}"},
             {"text": str(page + 1) + "/" + str(original_sports_size // self.value_per_page + 1),
              'callback_data': f"DROP_VALUE"},
             {"text": "•" if (page + 1) * self.value_per_page >= original_sports_size else '»',
              'callback_data': f"open_events${page if (1 + page) * self.value_per_page >= original_sports_size else page + 1}"}])
        msg = "<b>Events Menu</b>\n🏒🏀⚽️⚾️🏉🥎🥊"
        if message_id is None:
            self.bot.send_inline_callback_button(user_id, msg, button)
        else:
            self.bot.edit_message(user_id, message_id, msg, button)

    def handle_open_sport(self, user_id, message_id, data):
        sport_g = data[0]
        page = int(data[1])
        button = {"resize_keyboard": True,
                  "inline_keyboard": []}
        keys = {}
        for event in self.events.values():
            if event.get_completed():
                continue
            if event.sport_group == sport_g:
                key = event.sport_key.replace("_", "-")
                keys[key] = event.sport_title

        original_sports_size = len(keys)

        keys = self.slice_dict_by_indices(keys, page * self.value_per_page,
                                          page * self.value_per_page + self.value_per_page - 1)
        for key in keys:
            button['inline_keyboard'].append([{"text": keys[key], 'callback_data': f"*${key}_0"}])
        print(original_sports_size)
        button['inline_keyboard'].append([{"text": "•" if page == 0 else '«',
                                           'callback_data': f"open_sport${sport_g}_{page if page == 0 else page - 1}"},
                                          {"text": str(page + 1) + "/" + str(
                                              original_sports_size // self.value_per_page + 1),
                                           'callback_data': f"DROP_VALUE"}, {"text": "•" if (
                                                                                                    page + 1) * self.value_per_page >= original_sports_size else '»',
                                                                             'callback_data': f"open_sport${sport_g}_{page if (page + 1) * self.value_per_page >= original_sports_size else page + 1}"}])

        button['inline_keyboard'].append([{"text": Constants.back_button, 'callback_data': f"open_events$0"}])
        self.bot.edit_message(user_id, message_id, "<b>Events Menu</b>\n🏒🏀⚽️⚾️🏉🥎🥊", button)

    def handle_sport_events(self, user_id, message_id, data):
        sport_key = data[0].replace("-", "_")
        page = int(data[1])
        button = {"resize_keyboard": True, "inline_keyboard": []}
        original_sports_size = 0

        # Create a list to store events within the specified index range
        events_to_display = []

        for event in self.events.values():
            if event.get_completed():
                continue
            if event.sport_key == sport_key:
                original_sports_size += 1
                events_to_display.append(event)

        # Calculate start and end indices for the events to display
        start_index = page * self.value_per_page
        end_index = start_index + self.value_per_page - 1
        events_to_display = events_to_display[start_index:end_index + 1]

        # Add events to the inline keyboard
        for event in events_to_display:
            button['inline_keyboard'].append([{"text": event.home_team + " vs " + event.away_team,
                                               'callback_data': f"p_event${event.event_id[:15]}"}])

        # Add pagination buttons
        button['inline_keyboard'].append([{"text": "•" if page == 0 else '«',
                                           'callback_data': f"*${sport_key.replace('_', '-')}_{page if page == 0 else page - 1}"},
                                          {"text": str(page + 1) + "/" + str(
                                              original_sports_size // self.value_per_page + 1),
                                           'callback_data': f"DROP_VALUE"}, {"text": "•" if (
                                                                                                    page + 1) * self.value_per_page >= original_sports_size else '»',
                                                                             'callback_data': f"*${sport_key.replace('_', '-')}_{page if (page + 1) * self.value_per_page >= original_sports_size else page + 1}"}])
        button['inline_keyboard'].append([{"text": Constants.back_button, 'callback_data': f"open_events$0"}])
        self.bot.edit_message(user_id, message_id, "<b>Events Menu</b>\n🏒🏀⚽️⚾️🏉🥎🥊", button)

    def handle_p_event(self, user_id, message_id, data):
        first_15_id = data[0]
        for event in self.events.values():
            if event.event_id[:15] == first_15_id:
                self.notify_users(event, user_id)

    def notify_users(self, event, chat_id=None):
        try:
            msg = f"📢 <b>New {event.sport_group} Event </b>📢\n\n"
            msg += f'⚫️ <b>{event.home_team} vs {event.away_team}</b> 🔴\n\n<b>📊 Winning Rates:</b>\n'
            for res in event.bookmakers:
                msg += "• <b>" + res['name'] + "</b>  x" + str(res['price']) + "\n"

            msg += f"""
⏱️ <b>Bets close at {self.unix_to_datetime(event.commence_time)} UTC</b>
            
ID: <code>{event.event_id}</code>
                """
            selections = [{"text": f"⚫️ {event.home_team}", 'callback_data': f"sel_t${event.event_id[:15]}_home-team"},
                          {"text": f"🔴 {event.away_team}", 'callback_data': f"sel_t${event.event_id[:15]}_away-team"}]
            for res in event.bookmakers:
                if res['name'] == 'Draw':
                    selections.append({"text": f"🟢 Draw", 'callback_data': f"sel_t${event.event_id[:15]}_Draw"})
            button = {"resize_keyboard": True,
                      "inline_keyboard": [
                          selections
                          ,
                          [{"text": "+ $5", 'callback_data': f"put_bet${event.event_id[:15]}_5"},
                           {"text": "+ $10", 'callback_data': f"put_bet${event.event_id[:15]}_10"},
                           {"text": "+ $25", 'callback_data': f"put_bet${event.event_id[:15]}_25"},
                           {"text": "+ $50", 'callback_data': f"put_bet${event.event_id[:15]}_50"},
                           {"text": "+ $100", 'callback_data': f"put_bet${event.event_id[:15]}_100"}],
                          [{"text": "+ $250", 'callback_data': f"put_bet${event.event_id[:15]}_250"},
                           {"text": "+ $500", 'callback_data': f"put_bet${event.event_id[:15]}_500"},
                           {"text": "+ $1000", 'callback_data': f"put_bet${event.event_id[:15]}_1000"}],

                          [{"text": f"🧹 Clear", 'callback_data': f"clear_b${event.event_id[:15]}"},
                           {"text": f"🔍 Participants", 'callback_data': f"view_p${event.event_id[:15]}"}]]}
            image = "AgACAgQAAxkBAANhZQtC-_9jRSgdBDi-3sl6iEWMPv4AAqW9MRvZ01hQ6sqwlm8Jzk0BAAMCAANtAAMwBA"
            if chat_id is None:
                resp = self.bot.send_photo(self.config['community_chat_id'],
                                           image,
                                           msg,
                                           button)
                try:
                    if resp.json()['ok'] is False:
                        self.bot.send_inline_callback_button(self.config['community_chat_id'], msg, button)
                except Exception as ex:
                    print(ex)

            else:
                resp = self.bot.send_photo(chat_id,
                                           image,
                                           msg,
                                           button)
                try:
                    if resp.json()['ok'] is False:
                        self.bot.send_inline_callback_button(chat_id, msg, button)
                except Exception as ex:
                    print(ex)

        except Exception as ex:
            print(f"Error from notify user {ex}")

    def handle_sel_t(self, chat_id, user_id, first_name, msg_id, data):
        first_15_id = data[0]
        selected_team = None
        event = None
        for ev in self.events.values():
            if first_15_id == ev.event_id[:15]:
                event = ev
                selected_team = event.away_team if data[1] == 'away-team' else (
                    event.home_team if data[1] == 'home-team' else 'Draw')

        if event is None:
            return False

        if event.commence_time <= time.time() + 60 or event.get_completed():
            self.bot.send_message(chat_id, f"❌ <b>{first_name}</b> Failed bets have already been closed.")
            return

        participants = event.get_participants()

        if str(user_id) in participants:
            self.bot.send_message(chat_id,
                                  f"<b>{first_name}</b> selected {selected_team}\n Current bet ${participants[f'{user_id}']['amount']}")

            participants[f'{user_id}'] = {"first_name": first_name, "amount": participants[f'{user_id}']['amount'],
                                          "bet": selected_team}

        else:
            self.bot.send_message(chat_id,
                                  f"👤 <b>{first_name}</b> has selected <b>{selected_team}</b>!\n💰 Current bet: <b>$0</b>")
            participants[f'{user_id}'] = {"first_name": first_name, "amount": 0, "bet": selected_team}

        event.set_participants(participants)

    def handle_put_bet(self, chat_id, user_id, user, first_name, msg_id, data):
        start_time = time.time()
        first_15_id = data[0]
        amount = int(data[1])
        event = None
        for ev in self.events.values():
            if first_15_id == ev.event_id[:15]:
                event = ev

        if event is None:
            return False

        if event.commence_time <= time.time() + 60 or event.get_completed():
            self.bot.send_message(chat_id, f"❌ <b>{first_name}</b>, failed bets have already been closed.")
            return

        participants = event.get_participants()

        if user.get_balance() >= amount:
            if str(user_id) in participants:
                try:
                    if participants[f'{user_id}']['amount'] + amount >= self.config['max_bet']:
                        self.bot.send_message(chat_id,
                                              f"❌ <b>{first_name}</b>, failed the maximum bet is ${self.config['max_bet']}")
                        return
                except Exception as ex:
                    print(f"error from participants[f'{user_id}']['amount'] + amount  {ex} ")
                    return

                self.bot.send_message(chat_id,
                                      f"👤 <b>{first_name}</b> has selected <b>{participants[f'{user_id}']['bet']}</b>!\n💰 Current bet: <b>${participants[f'{user_id}']['amount'] + amount}</b>")

                participants[f'{user_id}'] = {"first_name": first_name,
                                              "amount": participants[f'{user_id}']['amount'] + amount,
                                              "bet": participants[f'{user_id}']['bet']}

                user.set_balance(user.get_balance() - amount)
                user.add_new_event(event.event_id)
                event.set_participants(participants)

            else:
                self.bot.send_message(chat_id, f"🙋‍♂️ <b>{first_name}</b>, please select a team first. ⚽️🏀")
        else:
            self.bot.send_message(chat_id,
                                  f"❌ Sorry, <b>{first_name}</b>, you don't have enough balance to place this bet. 💸😔")

    def handle_clear_b(self, chat_id, user_id, user, first_name, msg_id, data):
        first_15_id = data[0]
        event = None
        for ev in self.events.values():
            if first_15_id == ev.event_id[:15]:
                event = ev

        if event is None:
            return False

        if event.commence_time <= time.time() + 60 or event.get_completed():
            self.bot.send_message(chat_id, f"❌ <b>{first_name}</b>, failed bets have already been closed.")
            return

        participants = event.get_participants()
        if str(user_id) in participants:
            self.bot.send_message(chat_id,
                                  f"🧹 <b>{first_name}</b>, your bet has been cleared.")

            current_bet_amount = participants[f'{user_id}']['amount']
            user.set_balance(user.get_balance() + current_bet_amount)
            user.remove_event(event.event_id)
            current_participants = event.get_participants()
            del current_participants[f'{user.user_id}']
            event.set_participants(current_participants)

        else:
            self.bot.send_message(chat_id,
                                  f"🤷‍♂️ <b>{first_name}</b>, you haven't placed any bets yet. Place a bet to join the action! 💰👍")

    def handle_view_p(self, chat_id, data):
        first_15_id = data[0]
        event = None
        for ev in self.events.values():
            if first_15_id == ev.event_id[:15]:
                event = ev

        if event is None:
            return False

        participants = event.get_participants()
        msg = "<i>Participants:</i>\n\n"
        for part in participants.values():
            msg += f"• <b>{part['first_name']}</b>  |  {part['bet']}  |  {part['amount']}\n"
        if msg == "<i>Participants:</i>\n\n":
            msg = "There are no participants at the moment. Be the first to join!"
        self.bot.send_message(chat_id, msg)
