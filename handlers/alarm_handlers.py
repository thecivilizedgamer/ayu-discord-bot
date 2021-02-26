import datetime
import random

from bot_data import ConvoSubscription
from data import Data
from db import DB
from enums import Days
from interface import (get_menu_selections, get_next_response,
                       get_utc_offset_mins, get_yes_no, prompt)
from misc import (capitalize, get_alarm_description, get_formatted_datetime,
                  get_local_time_from_offset, str_to_time, uncapitalize)


async def alarm_command(message, command_arg):
    alarm_name = await prompt(message.author.id, message.channel, "What is the alarm for?")
    if alarm_name is None:
        await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
        return
    if alarm_name.lower() in [x.lower() for x in DB.get_alarms(message.author.id).keys()]:
        await message.channel.send(f"You already have an alarm with that name! Check your existing alarms with \"!{Data.config.command_word} list alarms\"")
        return

    times = await prompt(message.author.id, message.channel, "What times do you want the alarm to go off? (for example, \"10 AM and 5:30 PM\")")
    if times is None:
        await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
        return

    if times.strip().startswith('at '):
        times = times.strip()[3:]
    time_segments = times.replace('and', '').replace(',', '').split()

    if len(time_segments) % 2 != 0:
        raise RuntimeError('Time args not divisible by 2')

    normalized_times = []
    i = 0
    for _ in range(len(time_segments) // 2):
        hours, mins = str_to_time(time_segments[i], time_segments[i + 1])
        normalized_times.append((hours, mins))
        i += 2

    if DB.get_utc_time_offset_mins(message.author.id) is None:
        offset_mins = await get_utc_offset_mins(message.author.id, message.channel, message.created_at)
        await DB.set_utc_time_offset_mins(message.author.id, offset_mins)
    else:
        local_time = get_local_time_from_offset(DB.get_utc_time_offset_mins(message.author.id))
        confirmed = await get_yes_no(
            message.author.id,
            message.channel,
            f"Based on what I know, I think your local time is {get_formatted_datetime(local_time)}. Is that right?")
        if confirmed is None:
            await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
            return
        if not confirmed:
            offset_mins = await get_utc_offset_mins(message.author.id, message.channel, message.created_at)
            await DB.set_utc_time_offset_mins(message.author.id, offset_mins)

    days = await get_menu_selections(
        message.author.id,
        message.channel,
        "What days should the alarm go off? Select the numbers corresponding\n"
        "to the days you want, then select the checkmark when you're done!",
        Days.ordered_days())

    if days is None:
        await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
        return

    # Convert to ints
    days = [Days.str_to_int(x) for x in days]

    alarm_data = {'times': normalized_times, 'days': days, 'created_at': datetime.datetime.utcnow()}

    confirmed = await get_yes_no(
        message.author.id,
        message.channel,
        "I'm setting an alarm for you to " +
        get_alarm_description(uncapitalize(alarm_name), days, normalized_times) +
        "! Does that look right?")

    if confirmed is None:
        await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
    elif not confirmed:
        await message.channel.send("Ok, if you still want to set an alarm then ask me again!")
    else:
        await message.channel.send(" All right, you're all set!")
        await DB.add_alarm(message.author.id, alarm_name, alarm_data)


async def delete_alarm_command(message, command_arg):
    await list_alarms_command(message, None)
    with ConvoSubscription(message.author.id, message.channel.id) as queue:
        random_alarm_name = random.choice(list(DB.get_alarms(message.author.id).keys()))
        await message.channel.send(f"Which alarm would you like to delete? For example, \"{random_alarm_name}\"")
        alarm_name = await get_next_response(queue)
    if alarm_name.lower() not in [x.lower() for x in DB.get_alarms(message.author.id)]:
        await message.channel.send(f"You don't have an alarm for that! Check your current alarms with `!{Data.config.command_word} list alarms`")
    else:
        await DB.delete_alarm(message.author.id, alarm_name)
        await message.channel.send(f"Ok, I'll forget about that alarm :)")


async def list_alarms_command(message, command_arg):
    alarms = DB.get_alarms(message.author.id)
    if len(alarms) == 0:
        await message.channel.send(f"You don't have any alarms right now... But you could set some! Say `!{Data.config.command_word} help alarm` to find out how!")
    else:
        msg = "Here's the alarms I'm keeping for you!```"
        for alarm_name, alarm_data in alarms.items():
            msg += '\n' + get_alarm_description(capitalize(alarm_name), alarm_data['days'], alarm_data['times'])
        msg += '```'
        await message.channel.send(msg)


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
def remove_old_acknowledged_alarms(user_id, alarm_name, alarm_datetime):
    alarms_to_remove = []
    now = datetime.datetime.utcnow()
    for alarm_id in DB.db['bot']['acknowledged_alarms']:
        if now - alarm_id[2] > datetime.timedelta(hours=StaticData.get_value('config.max_alarm_snooze_hours'), minutes=5):
            alarms_to_remove.append(alarm_id)
    for alarm_id in alarms_to_remove:
        DB.db['bot']['acknowledged_alarms'].remove(alarm_id)


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
