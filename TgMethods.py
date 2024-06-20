import requests
import time
import json


class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset, 'allowed_updates': ["message", 'callback_query']}
        resp = requests.get(self.api_url + method, params)
        count = 0
        while 'result' not in resp.json():
            time.sleep(1)
            count += 1
            if count == 5:
                print('Network Error: bot recover')
                return False
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp


    def send_animate(self, chat_id, gif_url):
        params = {'chat_id': chat_id, 'animation': gif_url, 'parse_mode': 'HTML'}
        method = 'sendAnimation'
        resp = requests.post(self.api_url + method, params)
        return resp

    def send_video(self, chat_id, video_url, button, caption):
        params = {'chat_id': chat_id, 'video': video_url, 'caption': caption, 'reply_markup': button,
                  'parse_mode': 'HTML'}
        method = 'sendVideo'
        resp = requests.post(self.api_url + method, params)
        return resp


    def leave_chat(self, chat_id):
        params = {'chat_id': chat_id, 'parse_mode': 'HTML'}
        method = 'leaveChat'
        resp = requests.post(self.api_url + method, params)
        return resp

    def send_photo(self, chat_id, photo_url, caption=None, button=None):
        if button is not None:
            button = json.dumps(button)
            params = {'chat_id': chat_id, 'photo': photo_url, 'caption': caption, 'reply_markup': button,
                      'parse_mode': 'HTML'}
        else:
            params = {'chat_id': chat_id, 'photo': photo_url, 'caption': caption,
                      'parse_mode': 'HTML'}

        method = 'sendPhoto'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_first_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[0]
        else:
            last_update = None

        return last_update

    def send_dice(self, chat_id, emoji):
        params = {'chat_id': chat_id, 'emoji': emoji, 'parse_mode': 'HTML'}
        method = 'sendDice'
        resp = requests.post(self.api_url + method, params)
        return resp

    def send_poll(self, chat_id, question, options, startgametime):
        params = {'chat_id': chat_id, 'question': question, 'options': options, 'is_anonymous': False,
                  'open_period': startgametime, 'parse_mode': 'HTML'}
        method = 'sendPoll'
        resp = requests.post(self.api_url + method, params)
        return resp

    def send_poll_quiz(self, chat_id, question, options, startgametime):
        params = {'chat_id': chat_id, 'question': question, 'options': options, 'type': 'quiz', 'correct_option_id': 0,
                  'is_anonymous': False, 'open_period': startgametime, 'parse_mode': 'HTML'}
        method = 'sendPoll'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_admins(self, chat_id):
        params = {'chat_id': chat_id, 'parse_mode': 'HTML'}
        method = 'getChatAdministrators'
        resp = requests.get(self.api_url + method, params)
        return resp

    def get_chat(self, chat_id):
        params = {'chat_id': chat_id, 'parse_mode': 'HTML'}
        method = 'getChat'
        resp = requests.get(self.api_url + method, params)
        return resp

    def open_keyboard(self, chat_id, text, keyboard):

        params = {'chat_id': chat_id, 'text': text, 'reply_markup': keyboard, 'resize_keyboard': True,
                  'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def remove_keyboard(self, chat_id, text):

        reply_markup = {
            "remove_keyboard": True,
            "selective": False,
        }
        reply_markup = json.dumps(reply_markup)
        params = {'chat_id': chat_id, 'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def remove_keyboard_selective(self, chat_id, text):

        reply_markup = {
            "remove_keyboard": True,
            "selective": True,
        }
        reply_markup = json.dumps(reply_markup)
        params = {'chat_id': chat_id, 'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def force_reply(self, chat_id, text, input_field_placeholder=None):

        reply_markup = {
            "force_reply": True,
            'input_field_placeholder': input_field_placeholder
        }
        reply_markup = json.dumps(reply_markup)
        params = {'chat_id': chat_id, 'text': text, 'reply_markup': reply_markup, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def pin(self, chat_id, message_id):
        params = {'chat_id': chat_id, 'message_id': message_id, 'disable_notification': False, 'parse_mode': 'HTML'}
        method = 'pinChatMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def unpin(self, chat_id, message_id):
        params = {'chat_id': chat_id, 'message_id': message_id, 'parse_mode': 'HTML'}
        method = 'unpinChatMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def restrict(self, chat_id, status):
        perm = {'can_send_messages': status, 'can_send_media_messages': status, 'can_send_polls': False,
                'can_send_other_messages': status}
        perm = json.dumps(perm)
        params = {'chat_id': chat_id, 'permissions': perm, 'parse_mode': 'HTML'}
        method = 'setChatPermissions'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def leave_group(self, chat_id):
        params = {'chat_id': chat_id, 'parse_mode': 'HTML'}
        method = 'leaveChat'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def delete_message(self, chat_id, message_id):
        params = {'chat_id': chat_id, 'message_id': message_id, 'parse_mode': 'HTML'}
        method = 'deleteMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def edit_message(self, chat_id, message_id, text, button=None, disable_web_page_preview=False):
        if button is not None:
            button = json.dumps(button)
            params = {'chat_id': chat_id, 'message_id': message_id, 'reply_markup': button, 'text': text,
                      'disable_web_page_preview': disable_web_page_preview,
                      'parse_mode': 'HTML'}
        else:
            params = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': 'HTML'}
        method = 'editMessageText'
        resp = requests.post(self.api_url + method, params)
        return resp

    def make_admin(self, chat_id, user_id):
        params = {'chat_id': chat_id, 'user_id': user_id, 'can_manage_chat': True, 'parse_mode': 'HTML'}
        method = 'promoteChatMember'
        resp = requests.post(self.api_url + method, params)
        return resp

    def forward_message(self, chat_id, from_chat_id, message_id):
        params = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id, 'parse_mode': 'HTML'}
        method = 'forwardMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def change_title(self, chat_id, user_id, title):
        params = {'chat_id': chat_id, 'user_id': user_id, 'custom_title': title, 'parse_mode': 'HTML'}
        method = 'setChatAdministratorCustomTitle'
        resp = requests.post(self.api_url + method, params)
        print(resp.json())
        return resp

    def send_inline_button(self, chat_id, something, message_text, message_button):
        button = {"inline_keyboard": [[{"text": message_button, "switch_inline_query": something}]]}
        button = json.dumps(button)
        params = {'chat_id': chat_id, 'text': message_text, 'reply_markup': button, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def send_inline_callback_button(self, chat_id, message_text, button):
        button = json.dumps(button)
        params = {'chat_id': chat_id, 'text': message_text, 'reply_markup': button, 'cache_time': 2,
                  'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp.json()


    def awnser_call_back_alert(self, call_back_id, text):

        params = {'callback_query_id': call_back_id, 'text': text, 'show_alert': True, 'cache_time': 5,
                  'next_offset': 'null', 'parse_mode': 'HTML'}
        method = 'answerCallbackQuery'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def awnser_call_back_alert_black(self, call_back_id, text):

        params = {'callback_query_id': call_back_id, 'text': text, 'show_alert': False, 'cache_time': 3,
                  'next_offset': 'null', 'parse_mode': 'HTML'}
        method = 'answerCallbackQuery'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def edit_inline(self, chat_id, message_id, button):
        button = json.dumps(button)
        params = {'chat_id': chat_id, 'message_id': message_id, 'reply_markup': button, 'parse_mode': 'HTML'}
        method = 'editMessageReplyMarkup'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def answer_inline_query(self, inline_query_id, results):
        params = {'inline_query_id': inline_query_id, 'results': results, 'parse_mode': 'HTML'}
        method = 'answerInlineQuery'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def edit_message_inline_id(self, inline_id, text, button):
        params = {'inline_message_id': inline_id, 'text': text, 'reply_markup': button, 'parse_mode': 'HTML'}
        method = 'editMessageText'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def get_chat(self, chat_id):
        params = {'chat_id': chat_id, 'parse_mode': 'HTML'}
        method = 'getChat'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def create_chat_invite_link(self, chat_id, expiration_time=None):
        if expiration_time is None:
            params = {'chat_id': chat_id, 'creates_join_request': True,
                      'parse_mode': 'HTML'}
        else:
            params = {'chat_id': chat_id, 'creates_join_request': True, 'expire_date': expiration_time,
                      'parse_mode': 'HTML'}

        method = 'createChatInviteLink'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def approve_chat_join_request(self, chat_id, user_id):
        params = {'chat_id': chat_id, 'user_id': user_id, 'parse_mode': 'HTML'}
        method = 'approveChatJoinRequest'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def decline_chat_join_request(self, chat_id, user_id):
        params = {'chat_id': chat_id, 'user_id': user_id, 'parse_mode': 'HTML'}
        method = 'declineChatJoinRequest'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def revoke_chat_invite_link(self, chat_id, invite_link):
        params = {'chat_id': chat_id, 'invite_link': invite_link, 'parse_mode': 'HTML'}
        method = 'revokeChatInviteLink'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def ban_chat_member(self, chat_id, user_id, until_date):
        params = {'chat_id': chat_id, 'user_id': user_id, 'until_date': until_date, 'parse_mode': 'HTML'}
        method = 'banChatMember'
        resp = requests.post(self.api_url + method, params)
        return resp.json()

    def get_chat_member(self, chat_id, user_id):
        params = {'chat_id': chat_id, 'user_id': user_id, 'parse_mode': 'HTML'}
        method = 'getChatMember'
        resp = requests.post(self.api_url + method, params)
        return resp.json()
