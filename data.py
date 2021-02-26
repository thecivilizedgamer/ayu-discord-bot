import os
import pickle
import shutil
import traceback
from asyncio.queues import Queue

from client import Client
from static_data import StaticData

client = Client.get_client()


class Data:
    data = {'global': {'users': {}, 'servers': {}, 'global': {}}}
    save_queue = Queue(loop=client.loop)

    @staticmethod
    def get_user_data(user_id):
        if user_id not in Data.data['global']['users']:
            Data.data['global']['users'][user_id] = {}
        return Data.data['global']['users'][user_id]

    @staticmethod
    def get_server_data(guild_id):
        if guild_id is None:
            return None
        if guild_id not in Data.data['global']['servers']:
            Data.data['global']['servers'][guild_id] = {'administrators': []}
        return Data.data['global']['servers'][guild_id]

    @staticmethod
    def get_global_data():
        return Data.data['global']['global']

    @staticmethod
    def get_user_data_for_feature(user_id, feature_key):
        if feature_key not in Data.data:
            Data.data[feature_key] = {'users': {}, 'servers': {}, 'global': {}}
        if user_id not in Data.data[feature_key]['users']:
            Data.data[feature_key]['users'][user_id] = {}
        return Data.data[feature_key]['users'][user_id]

    @staticmethod
    def get_server_data_for_feature(guild_id, feature_key):
        if feature_key not in Data.data:
            Data.data[feature_key] = {'users': {}, 'servers': {}, 'global': {}}
        if guild_id not in Data.data[feature_key]['servers']:
            Data.data[feature_key]['servers'][guild_id] = {'enabled': True}
        return Data.data[feature_key]['servers'][guild_id]

    @staticmethod
    def get_feature_data(feature_key):
        if feature_key not in Data.data:
            Data.data[feature_key] = {'users': {}, 'servers': {}, 'global': {}}
        return Data.data[feature_key]['global']

    @staticmethod
    async def save_to_disk():
        try:
            if os.path.exists('save.dmp'):
                shutil.copy('save.dmp', 'save.dmp.bak')
            with open('save.dmp', 'wb') as f:
                pickle.dump(Data.data, f)
        except Exception:
            await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                f'ERROR: Failed to save to save.dmp: ```{traceback.format_exc()}```')

    @staticmethod
    async def request_save():
        await Data.save_queue.put(None)

    @staticmethod
    async def load_from_disk(filename='save.dmp'):
        try:
            with open(filename, 'rb') as f:
                Data.data = pickle.load(f)
        except Exception:
            await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                f'ERROR: Failed to load from {filename}: ```{traceback.format_exc()}```')
            try:
                with open(f'{filename}.bak', 'rb') as f:
                    Data.data = pickle.load(f)
            except Exception:
                await client.get_channel(StaticData.get_value('config.debug_channel_id')).send(
                    f'ERROR: Also failed to load backup save file {filename}.bak: ```{traceback.format_exc()}```')
