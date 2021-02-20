import json
import os
import random

from misc import capitalize


class DataStore:
    def __init__(self, data_file_path, catch_errors=False):
        self._data = None
        self.data_file_path = data_file_path
        self.catch_errors = catch_errors

    @property
    def data(self):
        if self._data is None:
            try:
                with open(self.data_file_path) as f:
                    self._data = json.load(f)
            except Exception:
                msg = f'Unable to load {self.data_file_path}'
                if self.catch_errors:
                    print(msg)
                else:
                    raise
            else:
                print(f'Loaded {self.data_file_path}')
        return self._data


class Chat(DataStore):

    def __init__(self):
        DataStore.__init__(self, os.path.join('data', 'chat.json'), True)

    @property
    def response_map(self):
        return self.data['response_map']


class Quotes(DataStore):

    def __init__(self):
        DataStore.__init__(self, os.path.join('data', 'quotes.json'), True)

    def get_quote(self):
        return random.choice(self.data['quotes'])


class Images(DataStore):

    def __init__(self):
        DataStore.__init__(self, os.path.join('data', 'images.json'), True)

    def get_greeting_image(self):
        return random.choice(self.data['greeting'])


class Phrases(DataStore):
    def __init__(self):
        DataStore.__init__(self, os.path.join('data', 'phrases.json'), True)

    def get_phrase(self, phrase_key):
        return random.choice(self.data[phrase_key]).replace('<bot_name>', Data.config.bot_name)

    def get_greeting_phrase(self):
        return Phrases.get_phrase(self, 'greeting')

    def get_dm_message(self):
        return Phrases.get_phrase(self, 'dm')

    def get_timer_message(self):
        return Phrases.get_phrase(self, 'timer')


class ReminderMessages(DataStore):
    def __init__(self):
        DataStore.__init__(self, os.path.join('data', 'reminder_messages.json'), True)

    data_file_path = os.path.join('data', 'reminder_messages.json')
    catch_errors = True

    def get_first_remind_image(self):
        return random.choice(self.data['remind_first']['images'])

    def get_first_remind_message(self):
        return random.choice(self.data['remind_first']['messages'])

    def get_late_remind_image(self):
        return random.choice(self.data['remind_late']['images'])

    def get_late_remind_message(self):
        return random.choice(self.data['remind_late']['messages'])

    def get_very_late_remind_image(self):
        return random.choice(self.data['remind_late']['images'])

    def get_very_late_remind_message(self):
        return random.choice(self.data['remind_late']['messages'])


class Config(DataStore):
    def __init__(self):
        DataStore.__init__(self, 'config.json')

    @property
    def owner_user_id(self):
        return self.data['owner_user_id']

    @property
    def bot_token(self):
        return self.data['bot_token']

    @property
    def debug_channel_id(self):
        return self.data['debug_channel_id']

    @property
    def max_alarm_snooze_hours(self):
        return self.data['max_alarm_snooze_hours']

    @property
    def alarm_snooze_sec(self):
        return self.data['alarm_snooze_sec']

    @property
    def pin_threshold(self):
        return self.data['pin_threshold'],

    @property
    def command_word(self):
        return self.data['command_word'].lower()

    @property
    def bot_name(self):
        return self.data.get('bot_name', capitalize(self.command_word))


class Data:
    chat = Chat()
    quotes = Quotes()
    images = Images()
    phrases = Phrases()
    reminder_messages = ReminderMessages()
    config = Config()

    all_stores = [chat, quotes, images, phrases, reminder_messages, config]

    @staticmethod
    def reload_all():
        for store in Data.all_stores:
            # Clear and then reload
            store._data = None
            _ = store.data
