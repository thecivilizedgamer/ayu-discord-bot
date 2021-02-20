import datetime
import random

from bot_data_store import ConvoSubscription
from data_store import Data
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
