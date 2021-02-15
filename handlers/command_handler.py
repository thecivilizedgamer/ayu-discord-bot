"""
Ideas:
    Snooze timers automatically, repeat until acknowledged - just add another timer for 5 min later, and add emoji to react and acknowledge
    Reminders have option of whether they need to be acknowledged
    Filter naughty words
"""

import datetime
import logging
import random
import time
import traceback
from datetime import timedelta

from bot_data_store import ConvoSubscription
from client import Client
from data_store import Data
from db import DB
from enums import Days
from interface import (get_menu_selections, get_next_response,
                       get_utc_offset_mins, get_yes_no, prompt)
from misc import (capitalize, get_alarm_description, get_formatted_datetime,
                  get_local_time_from_offset, remove_all_punctuation,
                  remove_trailing_punctuation, seconds_to_string, str_to_time,
                  uncapitalize)
from user import User

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

COMMAND_DESCRIPTIONS = {
    "ping":         "check that I\'m listening!",
    "help":         "display available commands",
    #"dm":           "I'll send you a friendly DM!",
    "timer":        "Set a timer!",
    "list timers":  "List all of the timers I'm keeping track of for you!",
    "delete timer": "Delete an existing timer",
    "alarm":        "Set an alarm!",
    "list alarms":  "List all of your alarms!",
    "delete alarm": "Delete an existing alarm"

}


client = Client.get_client()


async def ping_command(message, command_arg):
    await message.channel.send('Pong!')


async def help_command(message, command_arg):
    if command_arg is None:
        max_command_width = max([len(x) for x in COMMAND_DESCRIPTIONS.keys()])

        help_str = ''
        for key in sorted(list(COMMAND_DESCRIPTIONS.keys())):
            description_lines = COMMAND_DESCRIPTIONS[key].split('\n')
            separator = '\n' + ''.join([' ' for _ in range(max_command_width + 2)])
            description_lines = separator.join(description_lines)
            help_str += f'{key:>{max_command_width}}: {description_lines}\n'
        help_str = help_str.rstrip()

        await message.channel.send(
            "Hi, I'm Ayu! I'm here to help!\n\n"
            "Here's what I can do (make sure you say `!ayu` first!):"
            f"```{help_str}```\n"
            "If you want to know how to use a single command, you can say `!ayu help <command>`\n\n"
            "I've also got a few hidden commands ^-^"
        )
    else:
        command_arg = remove_trailing_punctuation(command_arg).lower()
        if command_arg in command_handlers and command_arg not in COMMAND_DESCRIPTIONS:
            await message.channel.send(
                "Shhhhhh, that's a secret command!"
            )
        elif command_arg in COMMAND_DESCRIPTIONS:
            help_str = f"Here's what you need to know about the `{command_arg}` command!\n\n```" + \
                COMMAND_DESCRIPTIONS[command_arg] + "```"
            await message.channel.send(help_str)
        else:
            await message.channel.send("I'm sorry, I don't know that command! ^^'")


async def hi_command(message, command_arg):
    msg = Data.phrases.get_greeting_phrase()
    if random.random() < .35:
        msg += '\n\n' + Data.images.get_greeting_image()
    await message.channel.send(msg)


async def dm_command(message, command_arg):
    await User.send_dm(message.author.id, Data.phrases.get_dm_message())


async def timer_command(message, command_arg):
    timer_name = await prompt(message.author.id, message.channel, "What is the timer for?")
    if timer_name is None:
        await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
        return
    if timer_name.lower() in [x.lower() for x in DB.get_timers(message.author.id).keys()]:
        await message.channel.send("You already have a timer with that name! Check your existing timers with \"!ayu list timers\"")
        return

    timer_args = await prompt(message.author.id, message.channel, "How soon do you want the timer to go off? For example, \"in 5 hours and 30 min\"")
    if timer_args is None:
        await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
        return

    if timer_args.strip().startswith('in '):
        timer_args = timer_args.strip()[3:]
    timer_args = timer_args.replace('and', '').replace(',', '')
    timer_args = remove_all_punctuation(timer_args).split()
    if len(timer_args) % 2 != 0:
        raise RuntimeError('Timer args not divisible by 2')

    i = 0
    delta = timedelta()
    for _ in range(len(timer_args) // 2):
        val = int(timer_args[i])
        denom = timer_args[i + 1].lower()
        i += 2
        if denom in ['week', 'weeks', 'wks']:
            delta += timedelta(weeks=val)
        elif denom in ['day', 'days']:
            delta += timedelta(days=val)
        elif denom in ['hour', 'hours', 'hr', 'hrs']:
            delta += timedelta(hours=val)
        elif denom in ['minute', 'minutes', 'min', 'mins']:
            delta += timedelta(minutes=val)
        elif denom in ['second', 'seconds', 'sec', 'secs']:
            delta += timedelta(seconds=val)
    end = time.time() + delta.total_seconds()

    await DB.add_timer(message.author.id, timer_name, end)
    remaining_time_str = seconds_to_string(round(end - time.time()))
    await message.channel.send(f"OK, I'll tell you to {uncapitalize(timer_name)} in {remaining_time_str}!")


async def list_timers_command(message, command_arg):
    timers = DB.get_timers(message.author.id)
    if len(timers) == 0:
        await message.channel.send("You don't have any timers right now... But you could make some! Say `!ayu help timer` to find out how!")
    else:
        msg = ''
        for timer_name, timer_end in timers.items():
            remaining_time = timer_end - time.time()
            if remaining_time <= 0:
                msg += f'{timer_name} right now!\n'
            else:
                remaining_time_str = seconds_to_string(remaining_time)
                msg += f'{capitalize(timer_name)} in {remaining_time_str}\n'
        msg = msg.strip()
        await message.channel.send(f"Here's all of your timers!\n```{msg}```")


async def delete_timer_command(message, command_arg):
    await list_timers_command(message, None)
    random_timer_name = random.choice(list(DB.get_timers(message.author.id).keys()))
    prompt_str = f"Which timer would you like to delete? For example, \"{random_timer_name}\""
    timer_name = await prompt(message.author.id, message.channel, prompt_str)
    if timer_name is None:
        await message.channel.send("I got tired of waiting, but if you want to set a timer then ask me again!")
        return
    if timer_name.lower() not in [x.lower() for x in DB.get_timers(message.author.id)]:
        await message.channel.send(f"You don't have a timer for that! Check your current timers with `!ayu list timers`")
    else:
        await DB.delete_timer(message.author.id, timer_name)
        await message.channel.send(f"Ok, I'll forget about that timer :)")


async def alarm_command(message, command_arg):
    alarm_name = await prompt(message.author.id, message.channel, "What is the alarm for?")
    if alarm_name is None:
        await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
        return
    if alarm_name.lower() in [x.lower() for x in DB.get_alarms(message.author.id).keys()]:
        await message.channel.send("You already have an alarm with that name! Check your existing alarms with \"!ayu list alarms\"")
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
        await message.channel.send(f"You don't have an alarm for that! Check your current alarms with `!ayu list alarms`")
    else:
        await DB.delete_alarm(message.author.id, alarm_name)
        await message.channel.send(f"Ok, I'll forget about that alarm :)")


async def list_alarms_command(message, command_arg):
    alarms = DB.get_alarms(message.author.id)
    if len(alarms) == 0:
        await message.channel.send("You don't have any alarms right now... But you could set some! Say `!ayu help alarm` to find out how!")
    else:
        msg = "Here's the alarms I'm keeping for you!```"
        for alarm_name, alarm_data in alarms.items():
            msg += '\n' + get_alarm_description(capitalize(alarm_name), alarm_data['days'], alarm_data['times'])
        msg += '```'
        await message.channel.send(msg)


async def restart_command(message, command_arg):
    await message.channel.send('Reloading resources...')
    Data.reload_all()
    await message.channel.send('Finished reloading resources!')


async def admin_help(message, command_arg):
    normal_commands = ''
    for key in sorted(list(command_handlers.keys())):
        normal_commands += key + '\n'
    normal_commands = normal_commands.rstrip()

    admin_commands = ''
    for key in sorted(list(admin_command_handlers.keys())):
        admin_commands += key + '\n'
    admin_commands = admin_commands.rstrip()

    await message.channel.send(
        'Available normal commands:'
        f'```\n{normal_commands}``` \n'  # Leading newline needed to avoid losing the first line for some reason
        'Available admin commands:'
        f'```\n{admin_commands}```'
    )

command_handlers = {
    'ping': ping_command,
    'help': help_command,
    'dm': dm_command,
    'timer': timer_command,
    'delete': {
        'timer': delete_timer_command,
        'alarm': delete_alarm_command
    },
    'alarm': alarm_command,
    'list': {
        'timers': list_timers_command,
        'alarms': list_alarms_command
    },
    'hi': hi_command,
    'hello': hi_command,
    'hey': hi_command,
    'yo': hi_command,
}

admin_command_handlers = {
    'reload': restart_command,
    'admin': admin_help
}


async def handle_command(message):

    command = message.content.split('!ayu', maxsplit=1)[1].strip()
    command_arg = None
    if len(command) == 0:
        await help_command(message, command_arg)
    else:
        command_segments = command.split(maxsplit=1)
        first_word = remove_trailing_punctuation(command_segments[0]).lower()
        if len(command_segments) > 1:
            command_arg = command_segments[1]

        if first_word in admin_command_handlers and message.author.id == Data.config.owner_user_id:
            await admin_command_handlers[first_word](message, command_arg)
        elif first_word in command_handlers:
            try:
                # Handle nested commands
                val = command_handlers[first_word]
                while isinstance(val, dict):
                    if ' ' in command_arg:
                        next_index, command_arg = command_arg.split(' ', maxsplit=1)
                        next_index = next_index.strip()
                        command_arg = command_arg.strip()
                    else:
                        next_index = command_arg
                        command_arg = None
                    val = val[next_index]
            except:
                await message.channel.send(
                    "Sorry, I don't know how to help with that ^^' "
                    "if you want to know what I can do, simply type `!ayu`")
            else:
                try:
                    await val(message, command_arg)
                except Exception:
                    user = await User.get_user(message.author.id)
                    await client.get_channel(Data.config.debug_channel_id).send(
                        f'ERROR: Failed while processing command `{message.content}` from user {user}: ```{traceback.format_exc()}```')
                    await message.channel.send(
                        "I'm sorry, something went wrong! Double-check what you typed and try again?")
        else:
            await message.channel.send(
                "Sorry, I don't know how to help with that ^^' "
                "if you want to know what I can do, simply type `!ayu`")
