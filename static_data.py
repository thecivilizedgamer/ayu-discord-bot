import json
import os
import random
import traceback

from client import Client

client = Client.get_client()


class StaticData:
    data = {}  # Stores data for command handlers (e.g. timers and alarms)

    @staticmethod
    def load_static_data(initialized=True):
        StaticData.data = {}  # Clear existing data

        msg = ''

        # Load all json files
        for original_filename in os.listdir('static_data'):
            filename = original_filename.lower()
            if filename.endswith('.json'):
                if filename[:-5] in StaticData.data:
                    error = f'Unable to load {original_filename}: shares name with another file'
                    if initialized:
                        msg += error + '\n'
                    else:
                        raise RuntimeError(error)
                try:
                    with open(os.path.join('static_data', filename)) as f:
                        StaticData.data[filename[:-5]] = json.load(f)
                except Exception:
                    if initialized:
                        msg += f'Unable to load {original_filename}: {traceback.format_exc()}\n'
                    else:
                        raise
                else:
                    if initialized:
                        msg += f'Loaded {original_filename}\n'
                    else:
                        print(f'Loaded {original_filename}')
        return msg

    @staticmethod
    def get_value(key):
        value = StaticData.data
        layers = key.split('.')
        for layer in layers:
            value = value[layer]
        return value

    @staticmethod
    def get_random_choice(key):
        return random.choice(StaticData.get_value(key))
