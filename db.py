import asyncio
import datetime
import os
import pickle
import shutil
import time
import traceback
from asyncio.queues import Queue

from client import Client
from data_store import Data

client = Client.get_client()


DEFAULT_DB_SCHEMA = {
    'bot': {
        'ringing_alarms': {},
        'acknowledged_alarms': [],
        'alarm_message_mappings': {},
        'administrators': {},
        'enabled_features': {}
    }
}


async def enforce_schema(document, schema):
    # Loosely make sure that the data loaded from the save file matches the format we expect, although
    # it's fine if there's new items in the schema that aren't in the save file
    if not isinstance(document, type(schema)):
        await client.get_channel(Data.config.debug_channel_id).send(
            'ERROR: Found an inconsistency with the save file. '
            'Please reconcile the inconsistency or delete the save file')
        raise RuntimeError('Found an inconsistency in the save file')
    if isinstance(schema, dict):
        for key, val in schema.items():
            if key in document:
                await enforce_schema(document[key], val)
            else:
                document[key] = val


class DB:
    save_queue = Queue(loop=client.loop)
    db = DEFAULT_DB_SCHEMA

    @staticmethod
    def ensure_user_id(user_id):
        if user_id not in DB.db:
            DB.db[user_id] = {
                'timers': {},
                'alarms': {}
            }

    @staticmethod
    async def save_to_disk():
        try:
            if os.path.exists('save.dmp'):
                shutil.copy('save.dmp', 'save.dmp.bak')
            with open('save.dmp', 'wb') as f:
                pickle.dump(DB.db, f)
        except Exception:
            await client.get_channel(Data.config.debug_channel_id).send(
                f'ERROR: Failed to save to save.dmp: ```{traceback.format_exc()}```')

    @staticmethod
    async def request_save():
        await DB.save_queue.put(None)

    @staticmethod
    async def load_from_disk(filename='save.dmp'):
        try:
            with open(filename, 'rb') as f:
                DB.db = pickle.load(f)
        except Exception:
            await client.get_channel(Data.config.debug_channel_id).send(
                f'ERROR: Failed to load from {filename}: ```{traceback.format_exc()}```')
            try:
                with open(f'{filename}.bak', 'rb') as f:
                    DB.db = pickle.load(f)
            except Exception:
                await client.get_channel(Data.config.debug_channel_id).send(
                    f'ERROR: Also failed to load backup save file {filename}.bak: ```{traceback.format_exc()}```')
        await enforce_schema(DB.db, DEFAULT_DB_SCHEMA)

    @staticmethod
    def get_utc_time_offset_mins(user_id):
        DB.ensure_user_id(user_id)
        return DB.db[user_id].get('utc_offset_mins')

    @staticmethod
    async def set_utc_time_offset_mins(user_id, utc_offset):
        DB.ensure_user_id(user_id)
        DB.db[user_id]['utc_offset_mins'] = utc_offset
        await DB.request_save()

    @staticmethod
    def get_timers(user_id):
        DB.ensure_user_id(user_id)
        return DB.db[user_id]['timers']

    @staticmethod
    def get_all_timers():
        return {key: val['timers'] for key, val in DB.db.items() if key != 'bot'}

    @staticmethod
    async def add_timer(user_id, timer_name, timer_end):
        DB.ensure_user_id(user_id)
        DB.db[user_id]['timers'][timer_name] = timer_end
        await DB.request_save()

    @staticmethod
    async def delete_timer(user_id, timer_name):
        DB.ensure_user_id(user_id)
        mapping = {name.lower(): name for name in DB.db[user_id]['timers'].keys()}
        actual_name = mapping[timer_name.lower()]
        if actual_name in DB.db[user_id]['timers']:
            del DB.db[user_id]['timers'][actual_name]
        await DB.request_save()

    @staticmethod
    def get_alarms(user_id):
        DB.ensure_user_id(user_id)
        return DB.db[user_id]['alarms']

    @staticmethod
    def get_all_alarms():
        return {key: val['alarms'] for key, val in DB.db.items() if key != 'bot'}

    @staticmethod
    async def add_alarm(user_id, alarm_name, alarm_data):
        DB.ensure_user_id(user_id)
        DB.db[user_id]['alarms'][alarm_name] = alarm_data
        await DB.request_save()

    @staticmethod
    async def delete_alarm(user_id, alarm_name):
        DB.ensure_user_id(user_id)
        mapping = {name.lower(): name for name in DB.db[user_id]['alarms'].keys()}
        actual_name = mapping[alarm_name.lower()]
        if actual_name in DB.db[user_id]['alarms']:
            del DB.db[user_id]['alarms'][actual_name]
        await DB.request_save()

    @staticmethod
    async def acknowledge_alarm(user_id, alarm_name, alarm_datetime):
        DB.db['bot']['acknowledged_alarms'].append((user_id, alarm_name, alarm_datetime))
        if (user_id, alarm_name, alarm_datetime) in DB.db['bot']['ringing_alarms']:
            messages = DB.db['bot']['ringing_alarms'][(user_id, alarm_name, alarm_datetime)]['messages']
            del DB.db['bot']['ringing_alarms'][(user_id, alarm_name, alarm_datetime)]
            for message_id in messages:
                del DB.db['bot']['alarm_message_mappings'][message_id]
        await DB.request_save()

    @staticmethod
    def alarm_is_acknowledged(user_id, alarm_name, alarm_datetime):
        return (user_id, alarm_name, alarm_datetime) in DB.db['bot']['acknowledged_alarms']

    @staticmethod
    def remove_old_acknowledged_alarms(user_id, alarm_name, alarm_datetime):
        alarms_to_remove = []
        now = datetime.datetime.utcnow()
        for alarm_id in DB.db['bot']['acknowledged_alarms']:
            if now - alarm_id[2] > datetime.timedelta(hours=Data.config.max_alarm_snooze_hours, minutes=5):
                alarms_to_remove.append(alarm_id)
        for alarm_id in alarms_to_remove:
            DB.db['bot']['acknowledged_alarms'].remove(alarm_id)

    @staticmethod
    def alarm_is_ringing(user_id, alarm_name, alarm_datetime):
        return (user_id, alarm_name, alarm_datetime) in DB.db['bot']['ringing_alarms']

    @staticmethod
    async def reset_ringing_alarm_time(user_id, alarm_name, alarm_datetime):
        if (user_id, alarm_name, alarm_datetime) not in DB.db['bot']['ringing_alarms']:
            DB.db['bot']['ringing_alarms'][(user_id, alarm_name, alarm_datetime)] = {
                'last_ring': time.time(),
                'messages': []
            }
        DB.db['bot']['ringing_alarms'][(user_id, alarm_name, alarm_datetime)]['last_ring'] = time.time()
        await DB.request_save()

    @staticmethod
    async def add_ringing_alarm_message(user_id, alarm_name, alarm_datetime, message_id):
        if (user_id, alarm_name, alarm_datetime) not in DB.db['bot']['ringing_alarms']:
            DB.db['bot']['ringing_alarms'][(user_id, alarm_name, alarm_datetime)] = {
                'last_ring': time.time(),
                'messages': []
            }
        DB.db['bot']['ringing_alarms'][(user_id, alarm_name, alarm_datetime)]['messages'].append(message_id)
        DB.db['bot']['alarm_message_mappings'][message_id] = (user_id, alarm_name, alarm_datetime)
        await DB.request_save()

    @staticmethod
    def get_ringing_alarm_time(user_id, alarm_name, alarm_datetime):
        return DB.db['bot']['ringing_alarms'].get((user_id, alarm_name, alarm_datetime), {}).get('last_ring', 0)

    @staticmethod
    def get_ringing_alarm_messages(user_id, alarm_name, alarm_datetime):
        return DB.db['bot']['ringing_alarms'].get((user_id, alarm_name, alarm_datetime), {}).get('messages', [])

    @staticmethod
    def lookup_alarm_from_message(message_id):
        return DB.db['bot']['alarm_message_mappings'].get(message_id)


async def save_task():
    while True:
        _ = await DB.save_queue.get()
        while DB.save_queue.qsize() > 0:
            _ = await DB.save_queue.get()  # If multiple requested saves since the last one, "process" all saves at once
        await DB.save_to_disk()
        await asyncio.sleep(10)  # Add minimum time in between saves
