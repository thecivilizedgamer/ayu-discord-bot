"""
Ideas:
    Snooze timers automatically, repeat until acknowledged - just add another timer for 5 min later, and add emoji to react and acknowledge
    Reminders have option of whether they need to be acknowledged
    Filter naughty words
"""

import logging
import random
import time
import traceback
from datetime import timedelta

from data_store import Data
from enums import Days
from interface import get_menu_selections, get_yes_no
from misc import (capitalize, remove_all_punctuation,
                  remove_trailing_punctuation, seconds_to_string, uncapitalize)
from user import User
from user_data_store import UserData, get_alarm_description

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

COMMAND_DESCRIPTIONS = {
    "ping":         "check that I\'m listening!",
    "help":         "display available commands",
    "dm":           "I'll send you a friendly DM!",
    "timer":        "Like a normal timer, but better! Tell me \"Go to \n"
                    "class in 1 hour 30 min\" or \"Eat pocky in 1 week\" or\n"
                    "even \"Smile in 5 seconds\"! Make as many as you want!",
    "timers":       "List all of the timers I'm keeping track of for you!",
    "timer-delete": "Changed your mind? Delete an existing timer\n"
                    "by name, for example \"delete-timer Go to class\"",
    "alarm":        "Set an alarm! Say what the alarm is for and what times\n"
                    "to go off, and I'll walk you through the rest! For example,\n"
                    "\"alarm eat taiyaki at 8:30 AM, 12 PM, and 5:30 PM\"",
    "alarms":        "List all of your alarms!"
}


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
    if command_arg is None:
        await help_command(message, 'timer')
    else:
        try:
            start = time.time()
            if ', in' in command_arg:
                timer_name, timer_args = command_arg.split(', in', maxsplit=1)
            else:
                timer_name, timer_args = command_arg.split(' in ', maxsplit=1)
            timer_name = timer_name.strip()
            if timer_name.lower() in [x.lower() for x in UserData.get_timers(message.author.id).keys()]:
                raise RuntimeError('Timer with that name already exists')
            if '-' in timer_args:
                raise RuntimeError('Negative times not supported')
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
            end = start + delta.total_seconds()

            UserData.add_timer(message.author.id, timer_name, end)
            remaining_time_str = seconds_to_string(round(end - time.time()))
            await message.channel.send(f"OK, I'll tell you to {uncapitalize(timer_name)} in {remaining_time_str}!")
        except Exception:
            logger.warning('Failed to parse timer command {}: {}'.format(command_arg, traceback.format_exc()))
            await message.channel.send("I'm sorry, I didn't understand how to set that timer! Try `!ayu help timer` for examples!")


async def timers_command(message, command_arg):
    timers = UserData.get_timers(message.author.id)
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


async def timer_delete_command(message, command_arg):
    if command_arg is None:
        await help_command(message, 'timer-delete')
    else:
        timer_name = command_arg.strip().lower()
        if timer_name not in UserData.get_timers(message.author.id):
            await message.channel.send(f"You don't have a timer for that! Check your current timers with `!ayu timers`")
        else:
            UserData.delete_timer(message.author.id, timer_name)
            await message.channel.send(f"Ok, I'll forget about that timer :)")


async def alarm_command(message, command_arg):
    if command_arg is None:
        await help_command(message, 'alarm')
    else:
        try:
            alarm_name, times = command_arg.split(' at ', maxsplit=1)
            time_segments = times.replace('and', '').replace(',', '').split()

            if len(time_segments) % 2 != 0:
                raise RuntimeError('Time args not divisible by 2')

            normalized_times = []
            i = 0
            for _ in range(len(time_segments) // 2):
                time_str = time_segments[i]
                am_pm = time_segments[i + 1].lower()
                i += 2

                if am_pm not in ['am', 'pm']:
                    raise RuntimeError('Invalid AM/PM specifier')

                if ':' in time_str:
                    hours, mins = time_str.split(':')
                    hours = int(hours)
                    mins = int(mins)
                else:
                    hours = int(time_str)
                    mins = 0
                if hours > 12 or hours < 1:
                    raise RuntimeError('Invalid hour specified')
                if mins > 59 or mins < 0:
                    raise RuntimeError('Invalid minutes specified')

                if am_pm == 'pm':
                    hours += 12
                normalized_times.append((hours, mins))

            days = await get_menu_selections(
                message.author.id,
                message.channel,
                "What days should the alarm go off? Select the numbers corresponding\n"
                "to the days you want, then select the checkmark when you're done!",
                [Days.SUNDAY, Days.MONDAY, Days.TUESDAY, Days.WEDNESDAY, Days.THURSDAY, Days.FRIDAY, Days.SATURDAY])

            if days is None:
                await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")

            alarm_data = {'times': normalized_times, 'days': days}

            confirmed = await get_yes_no(
                message.author.id,
                message.channel,
                "I'm setting an alarm for you to " +
                get_alarm_description(uncapitalize(alarm_name), days, normalized_times) +
                "! Does that look right? Select the check for yes, or the x for no!")

            if confirmed is None:
                await message.channel.send("I got tired of waiting, but if you want to set an alarm then ask me again!")
            elif not confirmed:
                await message.channel.send("Ok, if you still want to set an alarm then ask me again!")
            else:
                await message.channel.send(" All right, you're all set!")
                UserData.add_alarm(message.author.id, alarm_name, alarm_data)

        except Exception:
            logger.warning('Failed to parse timer command {}: {}'.format(command_arg, traceback.format_exc()))
            await message.channel.send("I'm sorry, something went wrong! Try again?")


async def alarms_command(message, command_arg):
    alarms = UserData.get_alarms(message.author.id)
    if len(alarms) == 0:
        await message.channel.send("You don't have any alarms right now... But you could set some! Say `!ayu help alarm` to find out how!")

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
    'timers': timers_command,
    'timer-delete': timer_delete_command,
    'alarm': alarm_command,
    'alarms': alarms_command,
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

        if first_word in admin_command_handlers and message.author.id == Data.config.admin_user_id:
            await admin_command_handlers[first_word](message, command_arg)
        elif first_word in command_handlers:
            await command_handlers[first_word](message, command_arg)
        else:
            await message.channel.send(
                "Sorry, I don't know how to help with that ^^' "
                "if you want to know what I can do, simply type `!ayu`")
